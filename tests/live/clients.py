"""HTTP clients for live HA Core and Soft-PLC App APIs."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
HA_ROOT = REPO_ROOT / ".cursor" / "ha"
DEFAULT_TOKEN_PATH = HA_ROOT / "data" / "ha_token.json"
DEFAULT_HA_URL = "http://127.0.0.1:8123"
DEFAULT_SOFT_PLC_URL = "http://127.0.0.1:8099"


@dataclass(frozen=True)
class HaAuth:
    base_url: str
    access_token: str


def load_ha_auth(token_path: Path | None = None) -> HaAuth | None:
    path = token_path or Path(
        __import__("os").environ.get("HA_TOKEN_PATH", str(DEFAULT_TOKEN_PATH))
    )
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    token = data.get("access_token")
    base = data.get("base_url") or DEFAULT_HA_URL
    if not token:
        return None
    return HaAuth(base_url=str(base).rstrip("/"), access_token=str(token))


class HttpClient:
    """Minimal JSON HTTP client (stdlib only)."""

    def __init__(self, base_url: str, token: str | None = None, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        body: Any | None = None,
        *,
        form: bytes | None = None,
        content_type: str | None = None,
    ) -> tuple[int, Any]:
        data = form
        headers: dict[str, str] = {}
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if form is not None and content_type:
            headers["Content-Type"] = content_type
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode() or "null"
                try:
                    return resp.status, json.loads(raw)
                except json.JSONDecodeError:
                    return resp.status, raw
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode()
            try:
                parsed: Any = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                parsed = raw
            return exc.code, parsed
        except urllib.error.URLError as exc:
            raise ConnectionError(f"{method} {self.base_url}{path}: {exc}") from exc


class HaClient(HttpClient):
    def get_states(self) -> list[dict[str, Any]]:
        code, data = self.request("GET", "/api/states")
        if code != 200 or not isinstance(data, list):
            raise RuntimeError(f"HA states failed: {code} {data}")
        return data

    def get_state(self, entity_id: str) -> dict[str, Any] | None:
        code, data = self.request("GET", f"/api/states/{entity_id}")
        if code == 404:
            return None
        if code != 200 or not isinstance(data, dict):
            raise RuntimeError(f"HA state {entity_id} failed: {code} {data}")
        return data

    def call_service(
        self, domain: str, service: str, data: dict[str, Any] | None = None
    ) -> Any:
        code, body = self.request(
            "POST",
            f"/api/services/{domain}/{service}",
            data or {},
        )
        if code not in (200, 201):
            raise RuntimeError(f"HA service {domain}.{service} failed: {code} {body}")
        return body

    def set_number(self, entity_id: str, value: float) -> None:
        self.call_service(
            "number",
            "set_value",
            {"entity_id": entity_id, "value": value},
        )

    def press_button(self, entity_id: str) -> None:
        self.call_service("button", "press", {"entity_id": entity_id})

    def plcassistant_entities(self) -> list[str]:
        return sorted(
            s["entity_id"]
            for s in self.get_states()
            if str(s.get("entity_id", "")).startswith(
                (
                    "sensor.plcassistant",
                    "number.plcassistant",
                    "button.plcassistant",
                )
            )
        )


class SoftPlcClient(HttpClient):
    def runtime(self) -> dict[str, Any]:
        code, data = self.request("GET", "/api/runtime")
        if code != 200 or not isinstance(data, dict):
            raise RuntimeError(f"Soft-PLC runtime failed: {code} {data}")
        return data

    def project(self) -> dict[str, Any]:
        code, data = self.request("GET", "/api/project")
        if code != 200 or not isinstance(data, dict):
            raise RuntimeError(f"Soft-PLC project failed: {code} {data}")
        return data

    def cmd(self, name: str) -> dict[str, Any]:
        code, data = self.request("POST", "/api/cmd", {"name": name})
        if code != 200 or not isinstance(data, dict):
            raise RuntimeError(f"Soft-PLC cmd {name} failed: {code} {data}")
        return data

    def tag_value(self, tag: str) -> Any:
        tags = self.runtime().get("tags") or {}
        entry = tags.get(tag)
        if isinstance(entry, dict):
            return entry.get("value")
        return None


def wait_until(
    predicate,
    *,
    timeout: float = 60.0,
    interval: float = 0.5,
    desc: str = "condition",
) -> None:
    deadline = time.time() + timeout
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            if predicate():
                return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
        time.sleep(interval)
    detail = f" ({last_err})" if last_err else ""
    raise TimeoutError(f"Timed out waiting for {desc}{detail}")


def tcp_open(host: str, port: int, timeout: float = 1.0) -> bool:
    import socket

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


__all__ = [
    "DEFAULT_HA_URL",
    "DEFAULT_SOFT_PLC_URL",
    "DEFAULT_TOKEN_PATH",
    "HA_ROOT",
    "HaAuth",
    "HaClient",
    "HttpClient",
    "REPO_ROOT",
    "SoftPlcClient",
    "load_ha_auth",
    "tcp_open",
    "wait_until",
]
