#!/usr/bin/env python3
"""Minimal arXiv Atom API client for /research (stdlib only)."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"
OPENSEARCH = "{http://a9.com/-/spec/opensearch/1.1/}"
API = "https://export.arxiv.org/api/query"
_LAST_CALL = 0.0


def _throttle() -> None:
    global _LAST_CALL
    elapsed = time.time() - _LAST_CALL
    if elapsed < 3.0:
        time.sleep(3.0 - elapsed)
    _LAST_CALL = time.time()


def _get(params: dict[str, Any]) -> str:
    _throttle()
    qs = urllib.parse.urlencode(params, safe=":+[]")
    url = f"{API}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "PLCAssistant-research/0.1"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return " ".join(el.text.split())


def _canonical_id(raw: str) -> tuple[str, int | None]:
    # http://arxiv.org/abs/1234.5678v2 or id tag
    m = re.search(r"arxiv\.org/abs/([^/\s]+)$", raw)
    if m:
        raw = m.group(1)
    raw = raw.strip()
    vm = re.match(r"^(.+?)v(\d+)$", raw)
    if vm:
        return vm.group(1), int(vm.group(2))
    return raw, None


def _parse_feed(xml: str) -> tuple[int, list[dict[str, Any]]]:
    root = ET.fromstring(xml)
    total_el = root.find(f"{OPENSEARCH}totalResults")
    total = int(_text(total_el) or "0")
    papers: list[dict[str, Any]] = []
    for entry in root.findall(f"{ATOM}entry"):
        id_raw = _text(entry.find(f"{ATOM}id"))
        arxiv_id, version = _canonical_id(id_raw)
        authors = [_text(a.find(f"{ATOM}name")) for a in entry.findall(f"{ATOM}author")]
        cats = [c.get("term", "") for c in entry.findall(f"{ARXIV}primary_category")]
        cats += [c.get("term", "") for c in entry.findall(f"{ATOM}category")]
        cats = list(dict.fromkeys([c for c in cats if c]))
        primary = cats[0] if cats else ""
        links = {l.get("title") or l.get("rel"): l.get("href") for l in entry.findall(f"{ATOM}link")}
        pdf = links.get("pdf") or f"https://arxiv.org/pdf/{arxiv_id}"
        abs_url = f"https://arxiv.org/abs/{arxiv_id}"
        papers.append(
            {
                "arxiv_id": arxiv_id,
                "version": version,
                "canonical_id_with_version": f"{arxiv_id}v{version}" if version else arxiv_id,
                "title": _text(entry.find(f"{ATOM}title")),
                "authors": authors,
                "abstract": _text(entry.find(f"{ATOM}summary")),
                "submitted_date": _text(entry.find(f"{ARXIV}published")) or _text(entry.find(f"{ATOM}published")),
                "updated_date": _text(entry.find(f"{ATOM}updated")),
                "primary_category": primary,
                "categories": cats,
                "comment": _text(entry.find(f"{ARXIV}comment")) or None,
                "journal_ref": _text(entry.find(f"{ARXIV}journal_ref")) or None,
                "doi": _text(entry.find(f"{ARXIV}doi")) or None,
                "abs_url": abs_url,
                "pdf_url": pdf,
                "source_queries": [],
            }
        )
    return total, papers


def search(queries: list[str], max_results: int, sort: str, order: str, start: int, paginate: bool) -> dict[str, Any]:
    query_meta = []
    by_id: dict[str, dict[str, Any]] = {}
    for q in queries:
        offset = start
        fetched_for_q = 0
        total = 0
        while True:
            xml = _get(
                {
                    "search_query": q,
                    "start": offset,
                    "max_results": max_results,
                    "sortBy": sort,
                    "sortOrder": order,
                }
            )
            total, papers = _parse_feed(xml)
            for p in papers:
                p["source_queries"] = list(dict.fromkeys(p.get("source_queries", []) + [q]))
                prev = by_id.get(p["arxiv_id"])
                if prev:
                    prev["source_queries"] = list(dict.fromkeys(prev["source_queries"] + [q]))
                else:
                    by_id[p["arxiv_id"]] = p
            fetched_for_q += len(papers)
            if not paginate or not papers or offset + max_results >= total:
                break
            offset += max_results
        query_meta.append({"search_query": q, "total_results": total, "fetched": fetched_for_q})
    return {"mode": "search", "queries": query_meta, "unique_papers": len(by_id), "papers": list(by_id.values())}


def lookup(ids: list[str], max_results: int) -> dict[str, Any]:
    id_list = ",".join(ids)
    xml = _get({"id_list": id_list, "max_results": max(max_results, len(ids))})
    total, papers = _parse_feed(xml)
    return {"mode": "lookup", "id_list": id_list, "total_results": total, "papers": papers}


def snowball(ids: list[str], max_results: int, years_back: int, max_authors: int, max_categories: int) -> dict[str, Any]:
    seed = lookup(ids, max_results)
    seed_papers = seed["papers"]
    authors: list[str] = []
    categories: list[str] = []
    for p in seed_papers:
        authors.extend(p.get("authors", [])[:2])
        categories.extend(p.get("categories", [])[:2])
    # unique preserve order
    top_authors = list(dict.fromkeys(authors))[:max_authors]
    top_categories = list(dict.fromkeys(categories))[:max_categories]
    # rough date window
    from datetime import datetime, timezone
    end = datetime.now(timezone.utc)
    start_y = end.year - years_back
    date_win = f"submittedDate:[{start_y}01010000 TO {end.year}12312359]"
    follow = []
    for a in top_authors:
        last = a.split()[-1]
        follow.append(f"au:{last}+AND+{date_win}")
    for c in top_categories:
        follow.append(f"cat:{c}+AND+{date_win}")
    follow = follow[:6]
    merged = search(follow, max_results, "relevance", "descending", 0, False) if follow else {"papers": []}
    by_id = {p["arxiv_id"]: p for p in seed_papers}
    for p in merged.get("papers", []):
        by_id.setdefault(p["arxiv_id"], p)
    return {
        "mode": "snowball",
        "seed_ids": ids,
        "seed_papers": seed_papers,
        "follow_up_queries": follow,
        "top_authors": top_authors,
        "top_categories": top_categories,
        "unique_papers": len(by_id),
        "papers": list(by_id.values()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search")
    s.add_argument("-q", "--query", action="append", required=True)
    s.add_argument("--max-results", type=int, default=25)
    s.add_argument("--sort", default="relevance", choices=["relevance", "submittedDate", "lastUpdatedDate"])
    s.add_argument("--order", default="descending", choices=["ascending", "descending"])
    s.add_argument("--start", type=int, default=0)
    s.add_argument("--paginate", action="store_true")
    s.add_argument("--compact", action="store_true")

    l = sub.add_parser("lookup")
    l.add_argument("--ids", required=True)
    l.add_argument("--max-results", type=int, default=25)
    l.add_argument("--compact", action="store_true")

    b = sub.add_parser("snowball")
    b.add_argument("--ids", required=True)
    b.add_argument("--max-results", type=int, default=20)
    b.add_argument("--years-back", type=int, default=3)
    b.add_argument("--max-authors", type=int, default=3)
    b.add_argument("--max-categories", type=int, default=2)
    b.add_argument("--compact", action="store_true")

    args = ap.parse_args()
    if args.cmd == "search":
        out = search(args.query, args.max_results, args.sort, args.order, args.start, args.paginate)
    elif args.cmd == "lookup":
        out = lookup([x.strip() for x in args.ids.split(",") if x.strip()], args.max_results)
    else:
        out = snowball(
            [x.strip() for x in args.ids.split(",") if x.strip()],
            args.max_results,
            args.years_back,
            args.max_authors,
            args.max_categories,
        )
    print(json.dumps(out, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
