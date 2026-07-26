#!/usr/bin/env python3
"""arXiv Atom API research helper — stdlib only.

See .agents/skills/research/reference.md for query syntax and output schema.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from typing import Any

API_URLS = (
    "https://arxiv.org/api/query",
    "https://export.arxiv.org/api/query",
)
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}
USER_AGENT = "PLCAssistant-arxiv-research/1.0 (mailto:research@localhost)"
MIN_INTERVAL_S = 5.0
MAX_RETRIES = 6

_last_request_at = 0.0


def _rate_limit() -> None:
    global _last_request_at
    now = time.monotonic()
    wait = MIN_INTERVAL_S - (now - _last_request_at)
    if wait > 0:
        time.sleep(wait)
    _last_request_at = time.monotonic()


def _http_get(url: str) -> bytes:
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES):
        _rate_limit()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 503) and attempt < MAX_RETRIES - 1:
                # Exponential backoff; arXiv rate limits can persist after bursts.
                sleep_s = min(180.0, 20.0 * (2**attempt))
                print(
                    f"arXiv HTTP {e.code}; backing off {sleep_s:.0f}s "
                    f"(attempt {attempt + 1}/{MAX_RETRIES})",
                    file=sys.stderr,
                )
                time.sleep(sleep_s)
                continue
            raise SystemExit(f"HTTP {e.code} from arXiv API: {e.reason}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                reason = getattr(e, "reason", e)
                sleep_s = min(120.0, 10.0 * (2**attempt))
                print(
                    f"arXiv network/timeout; backing off {sleep_s:.0f}s "
                    f"(attempt {attempt + 1}/{MAX_RETRIES}): {reason}",
                    file=sys.stderr,
                )
                time.sleep(sleep_s)
                continue
            raise SystemExit(f"Network error reaching arXiv API: {e}") from e
    raise SystemExit(f"Failed to fetch from arXiv API: {last_err}")


def _text(el: ET.Element | None) -> str | None:
    if el is None or el.text is None:
        return None
    return " ".join(el.text.split())


def _canonical_arxiv_id(raw: str) -> tuple[str, int | None]:
    """Return (id without version, version or None)."""
    raw = raw.strip()
    if raw.startswith("http"):
        raw = raw.rstrip("/").split("/")[-1]
    m = re.match(r"^(.+?)v(\d+)$", raw)
    if m:
        return m.group(1), int(m.group(2))
    return raw, None


def _parse_entry(entry: ET.Element) -> dict[str, Any]:
    id_url = _text(entry.find("atom:id", ATOM_NS)) or ""
    arxiv_id, version = _canonical_arxiv_id(id_url)

    authors = [
        _text(a.find("atom:name", ATOM_NS)) or ""
        for a in entry.findall("atom:author", ATOM_NS)
    ]
    authors = [a for a in authors if a]

    categories = [
        c.attrib.get("term", "")
        for c in entry.findall("atom:category", ATOM_NS)
        if c.attrib.get("term")
    ]
    primary_el = entry.find("arxiv:primary_category", ATOM_NS)
    primary = (
        primary_el.attrib.get("term")
        if primary_el is not None
        else (categories[0] if categories else "")
    )

    published = _text(entry.find("atom:published", ATOM_NS))
    updated = _text(entry.find("atom:updated", ATOM_NS))

    links = {lnk.attrib.get("title") or lnk.attrib.get("rel"): lnk.attrib.get("href")
             for lnk in entry.findall("atom:link", ATOM_NS)}
    abs_url = links.get("alternate") or f"https://arxiv.org/abs/{arxiv_id}"
    pdf_url = links.get("pdf") or f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    comment = _text(entry.find("arxiv:comment", ATOM_NS))
    journal_ref = _text(entry.find("arxiv:journal_ref", ATOM_NS))
    doi = _text(entry.find("arxiv:doi", ATOM_NS))

    return {
        "arxiv_id": arxiv_id,
        "version": version,
        "canonical_id_with_version": f"{arxiv_id}v{version}" if version else arxiv_id,
        "title": _text(entry.find("atom:title", ATOM_NS)) or "",
        "authors": authors,
        "abstract": _text(entry.find("atom:summary", ATOM_NS)) or "",
        "submitted_date": published,
        "updated_date": updated,
        "primary_category": primary,
        "categories": categories,
        "comment": comment,
        "journal_ref": journal_ref,
        "doi": doi,
        "abs_url": abs_url,
        "pdf_url": pdf_url,
        "source_queries": [],
    }


def _parse_feed(xml_bytes: bytes) -> tuple[int, list[dict[str, Any]]]:
    root = ET.fromstring(xml_bytes)
    total_el = root.find("opensearch:totalResults", ATOM_NS)
    total = int(total_el.text) if total_el is not None and total_el.text else 0
    papers = [_parse_entry(e) for e in root.findall("atom:entry", ATOM_NS)]
    return total, papers


def api_search(
    search_query: str,
    *,
    start: int = 0,
    max_results: int = 25,
    sort_by: str = "relevance",
    sort_order: str = "descending",
) -> tuple[int, list[dict[str, Any]]]:
    params = {
        "search_query": search_query,
        "start": start,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    query = urllib.parse.urlencode(params)
    last_err: Exception | None = None
    for base in API_URLS:
        try:
            return _parse_feed(_http_get(f"{base}?{query}"))
        except SystemExit as e:
            last_err = e
            print(f"endpoint failed ({base}): {e}", file=sys.stderr)
            continue
    raise SystemExit(f"All arXiv endpoints failed: {last_err}")


def api_lookup(ids: list[str], *, max_results: int = 25) -> tuple[int, list[dict[str, Any]]]:
    params = {
        "id_list": ",".join(ids),
        "max_results": max(max_results, len(ids)),
    }
    query = urllib.parse.urlencode(params)
    last_err: Exception | None = None
    for base in API_URLS:
        try:
            return _parse_feed(_http_get(f"{base}?{query}"))
        except SystemExit as e:
            last_err = e
            print(f"endpoint failed ({base}): {e}", file=sys.stderr)
            continue
    raise SystemExit(f"All arXiv endpoints failed: {last_err}")


def _merge_papers(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for p in papers:
        existing = by_id.get(p["arxiv_id"])
        if existing is None:
            by_id[p["arxiv_id"]] = p
            continue
        # Merge source_queries; keep newer version metadata if present
        sq = list(dict.fromkeys(existing["source_queries"] + p["source_queries"]))
        if (p.get("version") or 0) >= (existing.get("version") or 0):
            merged = dict(p)
            merged["source_queries"] = sq
            by_id[p["arxiv_id"]] = merged
        else:
            existing["source_queries"] = sq
    return list(by_id.values())


def cmd_search(args: argparse.Namespace) -> dict[str, Any]:
    query_meta = []
    all_papers: list[dict[str, Any]] = []
    for q in args.query:
        fetched_for_q: list[dict[str, Any]] = []
        start = args.start
        total = 0
        while True:
            total, page = api_search(
                q,
                start=start,
                max_results=args.max_results,
                sort_by=args.sort,
                sort_order=args.order,
            )
            for p in page:
                p["source_queries"] = [q]
            fetched_for_q.extend(page)
            if not args.paginate or not page:
                break
            start += len(page)
            if start >= total:
                break
        query_meta.append(
            {
                "search_query": q,
                "total_results": total,
                "fetched": len(fetched_for_q),
            }
        )
        all_papers.extend(fetched_for_q)

    merged = _merge_papers(all_papers)
    return {
        "mode": "search",
        "queries": query_meta,
        "unique_papers": len(merged),
        "papers": merged,
    }


def cmd_lookup(args: argparse.Namespace) -> dict[str, Any]:
    ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    total, papers = api_lookup(ids, max_results=args.max_results)
    for p in papers:
        p["source_queries"] = [f"id_list:{args.ids}"]
    return {
        "mode": "lookup",
        "id_list": args.ids,
        "total_results": total,
        "papers": papers,
    }


def _years_ago_window(years_back: int) -> str:
    now = datetime.now(timezone.utc)
    start_year = now.year - years_back
    return f"submittedDate:[{start_year:04d}01010000 TO {now.year:04d}12312359]"


def cmd_snowball(args: argparse.Namespace) -> dict[str, Any]:
    ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    _, seeds = api_lookup(ids, max_results=max(args.max_results, len(ids)))
    for p in seeds:
        p["source_queries"] = [f"seed:{p['arxiv_id']}"]

    author_counts: Counter[str] = Counter()
    cat_counts: Counter[str] = Counter()
    for p in seeds:
        for a in p["authors"][: args.max_authors]:
            # Use last token as surname for au: queries
            surname = a.split()[-1] if a.split() else a
            author_counts[surname.lower()] += 1
        for c in p["categories"][: args.max_categories]:
            cat_counts[c] += 1
        if p["primary_category"]:
            cat_counts[p["primary_category"]] += 1

    top_authors = [a for a, _ in author_counts.most_common(args.max_authors)]
    top_categories = [c for c, _ in cat_counts.most_common(args.max_categories)]
    date_window = _years_ago_window(args.years_back)

    follow_ups: list[str] = []
    for au in top_authors:
        for cat in top_categories:
            follow_ups.append(f"au:{au}+AND+cat:{cat}+AND+{date_window}")

    all_papers = list(seeds)
    for q in follow_ups:
        total, page = api_search(q, max_results=args.max_results)
        for p in page:
            p["source_queries"] = [q]
        all_papers.extend(page)

    merged = _merge_papers(all_papers)
    return {
        "mode": "snowball",
        "seed_ids": ids,
        "seed_papers": seeds,
        "follow_up_queries": follow_ups,
        "top_authors": top_authors,
        "top_categories": top_categories,
        "unique_papers": len(merged),
        "papers": merged,
    }


def _print_json(payload: dict[str, Any], compact: bool) -> None:
    if compact:
        json.dump(payload, sys.stdout, separators=(",", ":"), ensure_ascii=False)
    else:
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="arXiv research helper (Atom API)")
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--max-results", type=int, default=25)
    common.add_argument("--compact", action="store_true")

    sp = sub.add_parser("search", parents=[common])
    sp.add_argument("-q", "--query", action="append", required=True)
    sp.add_argument(
        "--sort",
        choices=["relevance", "submittedDate", "lastUpdatedDate"],
        default="relevance",
    )
    sp.add_argument("--order", choices=["ascending", "descending"], default="descending")
    sp.add_argument("--start", type=int, default=0)
    sp.add_argument("--paginate", action="store_true")

    lp = sub.add_parser("lookup", parents=[common])
    lp.add_argument("--ids", required=True)

    sb = sub.add_parser("snowball", parents=[common])
    sb.add_argument("--ids", required=True)
    sb.add_argument("--years-back", type=int, default=3)
    sb.add_argument("--max-authors", type=int, default=3)
    sb.add_argument("--max-categories", type=int, default=2)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "search":
        payload = cmd_search(args)
    elif args.command == "lookup":
        payload = cmd_lookup(args)
    elif args.command == "snowball":
        payload = cmd_snowball(args)
    else:
        parser.error(f"unknown command {args.command}")
        return 2
    _print_json(payload, args.compact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
