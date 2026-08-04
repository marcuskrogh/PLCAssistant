"""SWD-250 acceptance: cascade PID cv_max repair + diagram SVG viewBox.

Dynamics structured fields (catalog payload, editor HTML, dual-tree sync) are
covered in tests/test_dynamics_editor.py — not duplicated here.
"""

from __future__ import annotations

import json
import threading
import urllib.request
from http.server import HTTPServer
from pathlib import Path

import pytest

from plcassistant.app.server import AppState, make_handler
from plcassistant.surface.builtin import (
    CASCADE_CMD_SPEED_MAX,
    CASCADE_SP_FLOW_MAX,
    wedge_cascade_program,
    wedge_softplc_project,
)
from plcassistant.surface.model import BlockInstance, Program
from plcassistant.surface.schema import (
    project_from_dict,
    project_to_dict,
    repair_cascade_pid_limits,
    repair_empty_demo_project_pair,
)


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


def _broken_cascade_program_dict() -> dict:
    """Cascade program with both PID copies wrongly capped at 6."""
    prog = wedge_cascade_program()
    prog["instances"]["level_pi"]["params"]["cv_max"] = 6.0
    prog["instances"]["flow_pi"]["params"]["cv_max"] = 6.0
    return prog


def test_wedge_cascade_program_has_distinct_cv_limits():
    prog = wedge_cascade_program()
    level = prog["instances"]["level_pi"]["params"]
    flow = prog["instances"]["flow_pi"]["params"]
    assert level["cv_min"] == pytest.approx(0.0)
    assert level["cv_max"] == pytest.approx(CASCADE_SP_FLOW_MAX)
    assert flow["cv_min"] == pytest.approx(0.0)
    assert flow["cv_max"] == pytest.approx(CASCADE_CMD_SPEED_MAX)


def _broken_cascade_program() -> Program:
    """Cascade program with both PID copies wrongly capped at 6 (in-memory)."""
    prog_dict = _broken_cascade_program_dict()
    instances = {}
    for iid, raw in prog_dict["instances"].items():
        instances[iid] = BlockInstance(
            instance_id=iid,
            template_id=raw["template_id"],
            library=raw["library"],
            params=dict(raw["params"]),
            equation=raw.get("equation", ""),
            x=float(raw.get("x", 0.0)),
            y=float(raw.get("y", 0.0)),
        )
    return Program(
        name=prog_dict["name"],
        description=prog_dict["description"],
        instances=instances,
        execution_order=list(prog_dict["execution_order"]),
        datablocks=list(prog_dict.get("datablocks", [])),
        version=prog_dict.get("version", "1.0"),
    )


def test_repair_cascade_pid_limits_fixes_both_at_six():
    prog = _broken_cascade_program()
    assert prog.instances["flow_pi"].params["cv_max"] == pytest.approx(6.0)

    assert repair_cascade_pid_limits(prog) is True
    assert prog.instances["level_pi"].params["cv_max"] == pytest.approx(CASCADE_SP_FLOW_MAX)
    assert prog.instances["flow_pi"].params["cv_max"] == pytest.approx(CASCADE_CMD_SPEED_MAX)
    assert prog.instances["level_pi"].params["cv_min"] == pytest.approx(0.0)
    assert prog.instances["flow_pi"].params["cv_min"] == pytest.approx(0.0)

    # Idempotent.
    assert repair_cascade_pid_limits(prog) is False


def test_repair_cascade_pid_limits_fixes_missing_flow_cv_max():
    prog_dict = wedge_cascade_program()
    del prog_dict["instances"]["flow_pi"]["params"]["cv_max"]
    raw = prog_dict["instances"]["flow_pi"]
    prog = Program(
        name=prog_dict["name"],
        instances={
            "level_pi": BlockInstance(
                instance_id="level_pi",
                template_id=prog_dict["instances"]["level_pi"]["template_id"],
                library="builtin",
                params=dict(prog_dict["instances"]["level_pi"]["params"]),
                equation=prog_dict["instances"]["level_pi"]["equation"],
            ),
            "flow_pi": BlockInstance(
                instance_id="flow_pi",
                template_id=raw["template_id"],
                library="builtin",
                params=dict(raw["params"]),
                equation=raw["equation"],
            ),
        },
        execution_order=["level_pi", "flow_pi"],
    )

    assert "cv_max" not in prog.instances["flow_pi"].params
    assert repair_cascade_pid_limits(prog) is True
    assert prog.instances["flow_pi"].params["cv_max"] == pytest.approx(CASCADE_CMD_SPEED_MAX)


def test_repair_cascade_pid_limits_project_pair():
    raw = wedge_softplc_project()
    raw["programs"]["tank"] = _broken_cascade_program_dict()
    project = project_from_dict(raw)
    saved = project_from_dict(project_to_dict(project))
    applied = project_from_dict(project_to_dict(project))
    # Simulate broken on-disk state: migration leaves PID+equation copies unchanged.
    for proj in (saved, applied):
        tank = proj.programs["tank"]
        tank.instances["flow_pi"].params["cv_max"] = 6.0

    assert repair_empty_demo_project_pair(saved, applied) is True
    for proj in (saved, applied):
        tank = proj.programs["tank"]
        assert tank.instances["level_pi"].params["cv_max"] == pytest.approx(CASCADE_SP_FLOW_MAX)
        assert tank.instances["flow_pi"].params["cv_max"] == pytest.approx(CASCADE_CMD_SPEED_MAX)


def test_repair_cascade_pid_limits_preserves_other_params():
    custom_kp = 55.0
    prog = _broken_cascade_program()
    prog.instances["level_pi"].params["kp"] = custom_kp

    repair_cascade_pid_limits(prog)
    assert prog.instances["level_pi"].params["kp"] == pytest.approx(custom_kp)
    assert prog.instances["flow_pi"].params["cv_max"] == pytest.approx(CASCADE_CMD_SPEED_MAX)


def test_repair_cascade_pid_limits_ignores_non_cascade_instances():
    prog = Program(
        name="Custom",
        instances={
            "other_pi": BlockInstance(
                instance_id="other_pi",
                template_id="PID",
                library="builtin",
                params={"kp": 1.0, "cv_min": 0.0, "cv_max": 6.0},
            ),
        },
        execution_order=["other_pi"],
    )
    assert repair_cascade_pid_limits(prog) is False
    assert prog.instances["other_pi"].params["cv_max"] == pytest.approx(6.0)


def test_app_state_load_repairs_broken_cascade_cv_limits(tmp_path: Path, monkeypatch):
    """Persisted project with both cv_max=6 is healed on AppState init."""
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    program_path = tmp_path / "program.json"
    payload = wedge_softplc_project()
    payload["programs"]["tank"] = _broken_cascade_program_dict()
    program_path.write_text(json.dumps(payload), encoding="utf-8")

    state = AppState(program_path=str(program_path))
    tank = state.saved_project.programs["tank"]
    assert tank.instances["level_pi"].params["cv_max"] == pytest.approx(CASCADE_SP_FLOW_MAX)
    assert tank.instances["flow_pi"].params["cv_max"] == pytest.approx(CASCADE_CMD_SPEED_MAX)

    # Repair should have been persisted back to disk.
    reloaded = json.loads(program_path.read_text(encoding="utf-8"))
    tank_saved = reloaded["project"]["programs"]["tank"]
    assert tank_saved["instances"]["flow_pi"]["params"]["cv_max"] == pytest.approx(
        CASCADE_CMD_SPEED_MAX
    )


# --- Diagram SVG viewBox / pointer mapping (package 2) ---


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


def test_dual_tree_canvas_has_swd250_viewbox_markers():
    root_canvas = Path("plcassistant/app/_canvas.py").read_text(encoding="utf-8")
    mirror_canvas = Path("plc_assistant/plcassistant/app/_canvas.py").read_text(
        encoding="utf-8"
    )
    for label, text in (
        ("root", root_canvas),
        ("mirror", mirror_canvas),
    ):
        assert "SWD-250: map screen pointer coords to SVG user units" in text, (
            f"{label} missing viewBox pointer mapping marker"
        )
        assert "SWD-250: resize viewBox so all blocks + padding fit" in text, (
            f"{label} missing viewBox resize marker"
        )
        assert "function updateCanvasViewBox" in text, f"{label} missing updateCanvasViewBox"
        assert "function clientToSvg" in text, f"{label} missing clientToSvg"


def test_default_tank_program_still_has_cascade_positions(app_server):
    _, base_url, _ = app_server
    status, prog = _json_get(base_url + "/api/program?id=tank")
    assert status == 200
    for iid in ("level_pi", "flow_pi"):
        inst = prog["instances"][iid]
        assert inst.get("x", 0) != 0 or inst.get("y", 0) != 0


def test_default_tank_program_has_distinct_cv_limits(app_server):
    _, base_url, _ = app_server
    status, prog = _json_get(base_url + "/api/program?id=tank")
    assert status == 200
    assert prog["instances"]["level_pi"]["params"]["cv_max"] == pytest.approx(
        CASCADE_SP_FLOW_MAX
    )
    assert prog["instances"]["flow_pi"]["params"]["cv_max"] == pytest.approx(
        CASCADE_CMD_SPEED_MAX
    )


def test_app_version_0_1_53():
    root = Path("custom_components/plcassistant")
    dual = Path("plc_assistant/custom_components/plcassistant")
    assert '"0.1.53"' in (root / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.53"' in (dual / "manifest.json").read_text(encoding="utf-8")
    assert 'version: "0.1.53"' in Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.53" in Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
