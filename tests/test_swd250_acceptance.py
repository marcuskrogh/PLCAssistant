"""SWD-250 acceptance (package 2): diagram SVG viewBox sizing and pointer mapping."""

from __future__ import annotations

import json
import threading
import urllib.request
from http.server import HTTPServer
from pathlib import Path

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


def test_wedge_cascade_program_extends_beyond_default_svg_viewport():
    """PID cascade layout exceeds the SVG default 300×150 user-unit box."""
    prog = wedge_cascade_program()
    level = prog["instances"]["level_pi"]
    flow = prog["instances"]["flow_pi"]
    block_w = 140
    # Three IN + one OUT pins → blockHeight ≈ 88
    block_h = 30 + 3 * 16 + 10
    assert flow["x"] + block_w > 300
    assert level["y"] + block_h > 150
    assert flow["x"] + block_w > 300


def test_canvas_html_swd250_viewbox_and_pointer_mapping(app_server):
    _, base_url, _ = app_server
    _, html = _get(base_url + "/")
    text = html.decode("utf-8")
    assert "SWD-250: map screen pointer coords to SVG user units" in text
    assert "SWD-250: resize viewBox so all blocks + padding fit" in text
    assert "function clientToSvg" in text
    assert "function updateCanvasViewBox" in text
    assert "function scheduleCanvasViewBox" in text
    assert "setAttribute('viewBox'" in text
    assert "getScreenCTM" in text
    assert "CANVAS_PAD" in text
    assert "updateCanvasViewBox(positions)" in text
    assert "clientToSvg(e.clientX, e.clientY)" in text
    assert "addEventListener('resize', scheduleCanvasViewBox)" in text


def test_canvas_source_has_swd250_diagram_markers():
    canvas = Path("plcassistant/app/_canvas.py").read_text(encoding="utf-8")
    assert "SWD-250: map screen pointer coords to SVG user units" in canvas
    assert "SWD-250: resize viewBox so all blocks + padding fit" in canvas
    assert "function updateCanvasViewBox" in canvas
    assert "function clientToSvg" in canvas


def test_default_tank_program_still_has_cascade_positions(app_server):
    _, base_url, _ = app_server
    status, prog = _json_get(base_url + "/api/program?id=tank")
    assert status == 200
    for iid in ("level_pi", "flow_pi"):
        inst = prog["instances"][iid]
        assert inst.get("x", 0) != 0 or inst.get("y", 0) != 0
