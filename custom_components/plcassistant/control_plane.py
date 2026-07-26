"""stdlib HTTP control-plane client for PutBindings / GetStatus / Start/Stop/Reload."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .bootstrap import ensure_contract

ensure_contract()

from plcassistant_contract import Binding, RuntimeStatus, ScanOptions  # noqa: E402


class AddonUnavailableError(RuntimeError):
    """Addon HTTP endpoint unreachable or returned an error."""


@dataclass
class ControlPlaneClient:
    """Synchronous HTTP adapter (mockable base_url). No Home Assistant imports."""

    base_url: str
    token: str | None = None
    timeout_s: float = 5.0

    def _url(self, path: str) -> str:
        return self.base_url.rstrip("/") + path

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self._url(path),
            data=data,
            headers=self._headers(),
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8") or "{}"
                if not raw.strip():
                    return {}
                try:
                    return json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise AddonUnavailableError(f"Invalid JSON from addon: {exc}") from exc
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise AddonUnavailableError(f"HTTP {exc.code}: {detail}") from exc
        except OSError as exc:
            raise AddonUnavailableError(str(exc)) from exc

    def put_bindings(self, bindings: list[Binding]) -> dict[str, Any]:
        payload = {"bindings": [b.to_dict() for b in bindings]}
        return self._request("PUT", "/api/bindings", payload)

    def put_scan_options(self, options: ScanOptions) -> dict[str, Any]:
        return self._request("PUT", "/api/scan_options", options.to_dict())

    def get_status(self) -> RuntimeStatus:
        data = self._request("GET", "/api/status")
        return RuntimeStatus.from_dict(data)

    def start(self) -> dict[str, Any]:
        return self._request("POST", "/api/start", {})

    def stop(self) -> dict[str, Any]:
        return self._request("POST", "/api/stop", {})

    def reload(self) -> dict[str, Any]:
        return self._request("POST", "/api/reload", {})
