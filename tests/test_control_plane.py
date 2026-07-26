"""Control-plane client tests with a stdlib fake addon HTTP server."""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
import types
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from plcassistant_contract import (
    Binding,
    BindingDirection,
    InputPolicy,
    OutputFaultPolicy,
    ScanOptions,
    ValueType,
)

_INTEGRATION_ROOT = (
    Path(__file__).resolve().parents[1] / "custom_components" / "plcassistant"
)


def _load_control_plane():
    """Load control_plane without executing HA-dependent plcassistant/__init__.py."""
    pkg_name = "plcassistant"
    if pkg_name not in sys.modules or not hasattr(sys.modules[pkg_name], "__path__"):
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(_INTEGRATION_ROOT)]  # type: ignore[attr-defined]
        pkg.__file__ = str(_INTEGRATION_ROOT / "__init__.py")
        sys.modules[pkg_name] = pkg

    def _load(mod_name: str, file_name: str):
        full = f"{pkg_name}.{mod_name}"
        if full in sys.modules:
            return sys.modules[full]
        path = _INTEGRATION_ROOT / file_name
        spec = importlib.util.spec_from_file_location(full, path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full] = mod
        spec.loader.exec_module(mod)
        setattr(sys.modules[pkg_name], mod_name, mod)
        return mod

    _load("bootstrap", "bootstrap.py")
    return _load("control_plane", "control_plane.py")


_cp = _load_control_plane()
ControlPlaneClient = _cp.ControlPlaneClient
AddonUnavailableError = _cp.AddonUnavailableError


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
    reloaded = False
    bad_json = False


def _make_handler(state: _State):
    class Handler(BaseHTTPRequestHandler):
        def _read_json(self):
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            return json.loads(raw.decode("utf-8") or "{}")

        def _write(self, code: int, body: dict | bytes):
            if isinstance(body, bytes):
                data = body
            else:
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
                if state.bad_json:
                    self._write(200, b"not-json{")
                else:
                    self._write(200, state.status)
            else:
                self._write(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802
            self._read_json()
            if self.path == "/api/start":
                state.started = True
                self._write(200, {"ok": True})
            elif self.path == "/api/reload":
                state.reloaded = True
                self._write(200, {"ok": True})
            elif self.path == "/api/stop":
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

    client.put_scan_options(
        ScanOptions(
            scan_period_ms=50,
            default_unavailable_policy=InputPolicy.FORCE_ZERO,
            default_on_bridge_fault=OutputFaultPolicy.SAFE_OFF,
        )
    )
    assert state.options["scan_period_ms"] == 50
    assert state.options["default_unavailable_policy"] == "force_zero"
    assert state.options["default_on_bridge_fault"] == "safe_off"

    status = client.get_status()
    assert status.bridge_connected is True
    assert status.runtime_state == "running"
    assert status.overrun_count == 1

    client.start()
    assert state.started is True
    client.reload()
    assert state.reloaded is True


def test_unavailable_host():
    client = ControlPlaneClient(base_url="http://127.0.0.1:1", timeout_s=0.2)
    with pytest.raises(AddonUnavailableError):
        client.get_status()


def test_invalid_json_wrapped(addon_server):
    base, state = addon_server
    state.bad_json = True
    client = ControlPlaneClient(base_url=base, timeout_s=1.0)
    with pytest.raises(AddonUnavailableError, match="Invalid JSON"):
        client.get_status()


def test_sync_payload_matches_contract_schema(addon_server):
    """AC3: PutBindings payload matches contract schema fields."""
    base, state = addon_server
    client = ControlPlaneClient(base_url=base)
    binding = Binding(
        tag="QX0",
        direction=BindingDirection.OUTPUT,
        entity_id="switch.pump",
        value_type=ValueType.BOOL,
        write_mode="entity",
        critical=True,
        on_bridge_fault=OutputFaultPolicy.HOLD_LAST_COMMAND,
    )
    client.put_bindings([binding])
    client.put_scan_options(ScanOptions(scan_period_ms=100))
    client.reload()

    assert state.bindings[0]["tag"] == "QX0"
    assert state.bindings[0]["direction"] == "output"
    assert state.bindings[0]["critical"] is True
    assert state.options["scan_period_ms"] == 100
    assert state.reloaded is True
