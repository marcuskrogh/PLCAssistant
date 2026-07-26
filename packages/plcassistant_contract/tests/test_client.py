"""Control-plane client tests with a stdlib fake addon HTTP server."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from plcassistant_contract import (
    Binding,
    BindingDirection,
    ScanOptions,
    ValueType,
)
from plcassistant_contract.client import AddonUnavailableError, ControlPlaneClient


class _State:
    bindings: list | None = None
    options: dict | None = None
    status = {
        "scan_period_ms": 100,
        "last_cycle_ms": 12,
        "overrun_count": 1,
        "bridge_connected": True,
        "bridge_lag_ms": 3,
        "stale_binding_count": 0,
        "fail_safe_active": False,
        "binding_error_count": 0,
        "runtime_state": "running",
    }
    started = False


def _make_handler(state: _State):
    class Handler(BaseHTTPRequestHandler):
        def _read_json(self):
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            return json.loads(raw.decode("utf-8") or "{}")

        def _write(self, code: int, body: dict):
            data = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_PUT(self):  # noqa: N802
            body = self._read_json()
            if self.path == "/api/bindings":
                state.bindings = body.get("bindings")
                self._write(200, {"ok": True})
            elif self.path == "/api/scan_options":
                state.options = body
                self._write(200, {"ok": True})
            else:
                self._write(404, {"error": "not found"})

        def do_GET(self):  # noqa: N802
            if self.path == "/api/status":
                self._write(200, state.status)
            else:
                self._write(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802
            self._read_json()
            if self.path == "/api/start":
                state.started = True
                self._write(200, {"ok": True})
            elif self.path in {"/api/stop", "/api/reload"}:
                self._write(200, {"ok": True})
            else:
                self._write(404, {"error": "not found"})

        def log_message(self, format, *args):  # noqa: A003
            return

    return Handler


@pytest.fixture()
def addon_server():
    state = _State()
    server = HTTPServer(("127.0.0.1", 0), _make_handler(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    yield f"http://{host}:{port}", state
    server.shutdown()


def test_put_bindings_and_status(addon_server):
    base, state = addon_server
    client = ControlPlaneClient(base_url=base, token="test")
    binding = Binding(
        tag="I0",
        direction=BindingDirection.INPUT,
        entity_id="binary_sensor.door",
        value_type=ValueType.BOOL,
    )
    client.put_bindings([binding])
    assert state.bindings is not None
    assert state.bindings[0]["tag"] == "I0"
    assert state.bindings[0]["entity_id"] == "binary_sensor.door"

    client.put_scan_options(ScanOptions(scan_period_ms=50))
    assert state.options["scan_period_ms"] == 50

    status = client.get_status()
    assert status.bridge_connected is True
    assert status.runtime_state == "running"
    assert status.overrun_count == 1

    client.start()
    assert state.started is True


def test_unavailable_host():
    client = ControlPlaneClient(base_url="http://127.0.0.1:1", timeout_s=0.2)
    with pytest.raises(AddonUnavailableError):
        client.get_status()
