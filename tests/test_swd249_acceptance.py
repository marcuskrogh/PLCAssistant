"""SWD-249 acceptance: heal empty demo programs on load; mobile tap-to-place."""

from __future__ import annotations

import json
import threading
import urllib.request
from http.server import HTTPServer
from pathlib import Path

import pytest

from plcassistant.app.server import AppState, make_handler
from plcassistant.surface.builtin import wedge_softplc_project
from plcassistant.surface.schema import (
    project_to_dict,
    repair_empty_demo_programs,
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


def _empty_demo_project(program_id: str, *, name: str = "Tank") -> dict:
    return {
        "version": "2.0",
        "scan_period_s": 0.1,
        "programs": {
            program_id: {
                "version": "1.0",
                "name": name,
                "instances": {},
                "wires": [],
                "execution_order": [],
                "datablocks": ["DB_Tank"],
            }
        },
        "tasks": [{"id": "main", "priority": 1, "programs": [program_id]}],
    }


def _assert_cascade_positions(prog: dict) -> None:
    for iid in ("level_pi", "flow_pi"):
        inst = prog["instances"][iid]
        assert inst.get("x", 0) != 0 or inst.get("y", 0) != 0


def _assert_cascade_wire(prog: dict) -> None:
    wires = prog.get("wires") or []
    assert any(
        w.get("src_instance") == "level_pi"
        and w.get("src_pin") == "cv"
        and w.get("dst_instance") == "flow_pi"
        and w.get("dst_pin") == "sp"
        for w in wires
    ), f"expected level_pi.cv → flow_pi.sp wire, got {wires!r}"


def test_repair_empty_demo_programs_pure_function():
    from plcassistant.surface.model import Program, SoftPlcProject, Task

    project = SoftPlcProject(
        programs={
            "main": Program(
                name="Tank",
                instances={},
                wires=[],
                execution_order=[],
                datablocks=["DB_Tank"],
            ),
            "custom_empty": Program(
                name="Custom",
                instances={},
                wires=[],
                execution_order=[],
            ),
        },
        tasks=[Task(task_id="main", priority=1, programs=["main", "custom_empty"])],
    )
    assert repair_empty_demo_programs(project) is True
    main_prog = project_to_dict(project)["programs"]["main"]
    _assert_cascade_positions(main_prog)
    _assert_cascade_wire(main_prog)
    assert project.programs["custom_empty"].instances == {}


def test_repair_db_tank_name_only_not_auto_filled():
    """DB_Tank / name=Tank heuristics removed — only tank/main ids heal."""
    from plcassistant.surface.model import Program, SoftPlcProject, Task

    project = SoftPlcProject(
        programs={
            "sketch": Program(
                name="Tank",
                instances={},
                wires=[],
                execution_order=[],
                datablocks=["DB_Tank"],
            ),
        },
        tasks=[Task(task_id="main", priority=1, programs=["sketch"])],
    )
    assert repair_empty_demo_programs(project) is False
    assert project.programs["sketch"].instances == {}


def test_nonempty_demo_program_unchanged_by_repair():
    from plcassistant.surface.model import BlockInstance, Program, SoftPlcProject, Task

    custom_kp = 99.0
    project = SoftPlcProject(
        programs={
            "tank": Program(
                name="Tank",
                instances={
                    "level_pi": BlockInstance(
                        instance_id="level_pi",
                        template_id="PID",
                        library="builtin",
                        params={"kp": custom_kp},
                    ),
                },
                wires=[],
                execution_order=["level_pi"],
            ),
        },
        tasks=[Task(task_id="main", priority=1, programs=["tank"])],
    )
    assert repair_empty_demo_programs(project) is False
    assert project.programs["tank"].instances["level_pi"].params["kp"] == custom_kp


def test_asymmetric_envelope_copies_applied_to_saved(tmp_path):
    custom_kp = 77.0
    customized = {
        "version": "1.0",
        "name": "Tank",
        "instances": {
            "level_pi": {
                "template_id": "PID",
                "library": "builtin",
                "params": {"kp": custom_kp, "ki": 1.0},
                "x": 40.0,
                "y": 50.0,
            },
            "flow_pi": {
                "template_id": "PID",
                "library": "builtin",
                "params": {"kp": 12.0, "ki": 2.0},
                "x": 280.0,
                "y": 80.0,
            },
        },
        "wires": [
            {
                "src_instance": "level_pi",
                "src_pin": "cv",
                "dst_instance": "flow_pi",
                "dst_pin": "sp",
            }
        ],
        "execution_order": ["level_pi", "flow_pi"],
        "datablocks": ["DB_Tank"],
    }
    path = tmp_path / "program.json"
    envelope = {
        "version": "2.0",
        "project": _empty_demo_project("tank"),
        "applied_project": {
            "version": "2.0",
            "scan_period_s": 0.1,
            "programs": {"tank": customized},
            "tasks": [{"id": "main", "priority": 1, "programs": ["tank"]}],
        },
    }
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")

    state = AppState(program_path=str(path))
    saved = state.program_dict_for("tank")
    assert saved["instances"]["level_pi"]["params"]["kp"] == custom_kp
    _assert_cascade_wire(saved)

    healed = json.loads(path.read_text(encoding="utf-8"))
    saved_main = healed["project"]["programs"]["tank"]
    assert saved_main["instances"]["level_pi"]["params"]["kp"] == custom_kp


def test_repair_empty_demo_project_pair_asymmetric():
    from plcassistant.surface.model import BlockInstance, Program, SoftPlcProject, Task

    custom_kp = 55.0
    filled = Program(
        name="Tank",
        instances={
            "level_pi": BlockInstance(
                instance_id="level_pi",
                template_id="PID",
                library="builtin",
                params={"kp": custom_kp},
            ),
        },
        wires=[],
        execution_order=["level_pi"],
    )
    empty = Program(name="Tank", instances={}, wires=[], execution_order=[])
    saved = SoftPlcProject(
        programs={"tank": empty},
        tasks=[Task(task_id="main", priority=1, programs=["tank"])],
    )
    applied = SoftPlcProject(
        programs={"tank": filled},
        tasks=[Task(task_id="main", priority=1, programs=["tank"])],
    )
    assert repair_empty_demo_project_pair(saved, applied) is True
    assert saved.programs["tank"].instances["level_pi"].params["kp"] == custom_kp
    assert applied.programs["tank"].instances["level_pi"].params["kp"] == custom_kp


def test_app_state_heals_empty_main_program_on_disk(tmp_path):
    path = tmp_path / "program.json"
    envelope = {
        "version": "2.0",
        "project": _empty_demo_project("main"),
        "applied_project": _empty_demo_project("main"),
    }
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")

    state = AppState(program_path=str(path))
    prog = state.program_dict_for("main")
    _assert_cascade_positions(prog)
    _assert_cascade_wire(prog)

    healed = json.loads(path.read_text(encoding="utf-8"))
    healed_main = healed["project"]["programs"]["main"]
    _assert_cascade_positions(healed_main)
    _assert_cascade_wire(healed_main)


def test_app_state_heals_empty_tank_program_on_disk(tmp_path):
    path = tmp_path / "program.json"
    envelope = {
        "version": "2.0",
        "project": _empty_demo_project("tank"),
        "applied_project": _empty_demo_project("tank"),
    }
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")

    state = AppState(program_path=str(path))
    prog = state.program_dict_for("tank")
    _assert_cascade_positions(prog)
    _assert_cascade_wire(prog)


def test_custom_empty_program_not_auto_filled(tmp_path):
    path = tmp_path / "program.json"
    envelope = {
        "version": "2.0",
        "project": {
            "version": "2.0",
            "scan_period_s": 0.1,
            "programs": {
                "custom_empty": {
                    "version": "1.0",
                    "name": "User sketch",
                    "instances": {},
                    "wires": [],
                    "execution_order": [],
                }
            },
            "tasks": [{"id": "main", "priority": 1, "programs": ["custom_empty"]}],
        },
    }
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")

    state = AppState(program_path=str(path))
    prog = state.program_dict_for("custom_empty")
    assert prog["instances"] == {}


def test_get_api_program_returns_healed_instances(app_server, tmp_path):
    _, base_url, state = app_server
    path = tmp_path / "program.json"
    envelope = {
        "version": "2.0",
        "project": _empty_demo_project("main"),
        "applied_project": _empty_demo_project("main"),
    }
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")

    healed_state = AppState(program_path=str(path))
    state.saved_project = healed_state.saved_project

    status, prog = _json_get(base_url + "/api/program?id=main")
    assert status == 200
    _assert_cascade_positions(prog)
    _assert_cascade_wire(prog)


def test_canvas_html_swd249_tap_to_place_wiring(app_server):
    _, base_url, _ = app_server
    _, html = _get(base_url + "/")
    text = html.decode("utf-8")
    assert "SWD-249: tap-to-place" in text
    assert 'data-place-on-tap="1"' in text or "placeOnTap" in text
    assert "dragStarted" in text
    assert "tapPlaceCount" in text
    assert "placeClickTimer" in text
    assert "SWD-249: defer-tap" in text


def test_dual_tree_canvas_has_swd249_tap_to_place_markers():
    root_canvas = Path("plcassistant/app/_canvas.py").read_text(encoding="utf-8")
    mirror_canvas = Path("plc_assistant/plcassistant/app/_canvas.py").read_text(
        encoding="utf-8"
    )
    for label, text in (
        ("root", root_canvas),
        ("mirror", mirror_canvas),
    ):
        assert "SWD-249: tap-to-place" in text, f"{label} missing tap-to-place marker"
        assert "placeClickTimer" in text, f"{label} missing defer-tap timer"
        assert "SWD-249: defer-tap" in text, f"{label} missing defer-tap marker"


def test_place_still_works_via_api(app_server):
    _, base_url, _ = app_server
    status, resp = _json_request(
        base_url + "/api/place?id=tank",
        "POST",
        {
            "template_id": "PID",
            "library": "builtin",
            "instance_id": "swd249_pid",
            "x": 120.0,
            "y": 160.0,
            "program_id": "tank",
        },
    )
    assert status == 200
    assert "swd249_pid" in resp["instances"]


def test_app_version_0_1_53():
    root = Path("custom_components/plcassistant")
    dual = Path("plc_assistant/custom_components/plcassistant")
    assert '"0.1.61"' in (root / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.61"' in (dual / "manifest.json").read_text(encoding="utf-8")
    assert 'version: "0.1.61"' in Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.61" in Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")


def test_default_wedge_project_has_instances():
    """Sanity: fresh default project already has cascade blocks."""
    from plcassistant.surface.schema import project_from_dict

    project = project_from_dict(wedge_softplc_project())
    tank = project_to_dict(project)["programs"]["tank"]
    _assert_cascade_positions(tank)
    _assert_cascade_wire(tank)
