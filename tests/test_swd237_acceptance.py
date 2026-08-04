"""SWD-237 acceptance: overview cards, diagram layout, place drag payload, built-in copy, editors."""

from __future__ import annotations

import json
import threading
import urllib.request
from http.server import HTTPServer

import pytest

from plcassistant.app.server import AppState, make_handler
from plcassistant.surface.builtin import wedge_cascade_program


@pytest.fixture()
def app_server(monkeypatch):
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    state = AppState()
    handler = make_handler(state)
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    base_url = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, base_url, state
    server.shutdown()


def _get(url: str) -> tuple[int, bytes]:
    with urllib.request.urlopen(url) as r:
        return r.status, r.read()


def _json_get(url: str) -> tuple[int, object]:
    status, body = _get(url)
    return status, json.loads(body)


def _json_request(url: str, method: str, data: object | None = None) -> tuple[int, object]:
    body_bytes = json.dumps(data).encode() if data is not None else b""
    req = urllib.request.Request(
        url,
        data=body_bytes,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return r.status, json.loads(r.read())


def test_wedge_cascade_program_has_distinct_canvas_positions():
    prog = wedge_cascade_program()
    level = prog["instances"]["level_pi"]
    flow = prog["instances"]["flow_pi"]
    assert level.get("x", 0) != 0 or level.get("y", 0) != 0
    assert flow.get("x", 0) != 0 or flow.get("y", 0) != 0
    assert (level.get("x"), level.get("y")) != (flow.get("x"), flow.get("y"))


def test_default_tank_program_api_returns_block_positions(app_server):
    _, base_url, _ = app_server
    status, prog = _json_get(base_url + "/api/program?id=tank")
    assert status == 200
    for iid in ("level_pi", "flow_pi"):
        inst = prog["instances"][iid]
        assert inst.get("x", 0) != 0 or inst.get("y", 0) != 0


def test_canvas_html_swd237_ui_wiring(app_server):
    _, base_url, _ = app_server
    _, html = _get(base_url + "/")
    text = html.decode("utf-8")
    assert "nav-card" in text
    assert "program-card nav-card" in text
    assert "task-card nav-card" in text
    assert "<h2>Built-in</h2>" in text
    assert "<h2>Shipped</h2>" not in text
    assert "Shipped PID" not in text
    assert "libraryFormTitle" in text
    assert "needsLayout" in text
    assert "#lib-body" in text
    assert "font-family: var(--mono)" in text
    assert "white-space: pre" in text
    assert "setData('text/plain'" in text
    assert "setData('application/json'" in text
    assert "blockPositions" in text
    # Built-in cards: title carries name (description); helper only for custom.
    assert "isCustom" in text
    assert "Built-in: name (description) in the title only" in text or "do not repeat description" in text


def test_program_without_canvas_positions_still_returned(app_server):
    """API still returns instances when x/y omitted (client auto-layouts)."""
    _, base_url, state = app_server
    from plcassistant.surface.schema import program_from_dict

    bare = {
        "version": "1.0",
        "name": "Bare",
        "instances": {
            "a": {"template_id": "PID", "library": "builtin", "params": {}},
            "b": {"template_id": "PID", "library": "builtin", "params": {}},
        },
        "wires": [],
        "execution_order": ["a", "b"],
    }
    state._set_program("tank", program_from_dict(bare))
    status, prog = _json_get(base_url + "/api/program?id=tank")
    assert status == 200
    assert set(prog["instances"]) == {"a", "b"}
    # Positions omitted from serialization when zero — client must layout.
    assert "x" not in prog["instances"]["a"]
    assert "y" not in prog["instances"]["a"]


def test_place_still_works_via_api(app_server):
    _, base_url, _ = app_server
    status, resp = _json_request(
        base_url + "/api/place?id=tank",
        "POST",
        {
            "template_id": "PID",
            "library": "builtin",
            "instance_id": "swd237_pid",
            "x": 120.0,
            "y": 160.0,
            "program_id": "tank",
        },
    )
    assert status == 200
    assert "swd237_pid" in resp["instances"]


def test_app_version_0_1_53():
    from pathlib import Path

    root = Path("custom_components/plcassistant")
    dual = Path("plc_assistant/custom_components/plcassistant")
    assert '"0.1.54"' in (root / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.54"' in (dual / "manifest.json").read_text(encoding="utf-8")
    assert 'version: "0.1.54"' in Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.54" in Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
