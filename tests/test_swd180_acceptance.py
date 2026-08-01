"""SWD-180 acceptance: inspectable library + generic PID copies."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer
from typing import Any

import pytest

from plcassistant.app.server import AppState, make_handler
from plcassistant.surface.builtin import PID_EQUATION, PID_TEMPLATE_ID, wedge_softplc_project
from plcassistant.surface.schema import place_block, program_from_dict, project_from_dict


def _old_cascade_program() -> dict[str, Any]:
    return {
        "version": "1.0",
        "name": "Tank",
        "instances": {
            "level_pi": {
                "template_id": "level_pi",
                "library": "builtin",
                "params": {"kp": 40.0, "ki": 5.0, "cv_min": 0.0, "cv_max": 6.0},
            },
            "flow_pi": {
                "template_id": "flow_pi",
                "library": "builtin",
                "params": {"kp": 12.0, "ki": 2.0, "cv_min": 0.0, "cv_max": 100.0},
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
    }


class _Server:
    def __init__(self, state: AppState) -> None:
        self.server = HTTPServer(("127.0.0.1", 0), make_handler(state))
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> "_Server":
        self.thread.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.server.shutdown()


def _json_get(url: str) -> tuple[int, Any]:
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _json_request(url: str, method: str, data: Any = None) -> tuple[int, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(data if data is not None else {}).encode("utf-8"),
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_pid_is_only_shipped_controller() -> None:
    state = AppState(initial_project=wedge_softplc_project())
    ids = {item["template_id"] for item in state.library_payload()}
    assert PID_TEMPLATE_ID in ids
    assert "level_pi" not in ids
    assert "flow_pi" not in ids
    pid = state.library_template("builtin", PID_TEMPLATE_ID)
    assert pid["description"].startswith("PID controller")
    assert {"kp", "ki", "kd", "td", "cv_min", "cv_max"} <= set(pid["params"])
    assert pid["body"] == PID_EQUATION


def test_migrates_legacy_level_and_flow_to_pid_copies() -> None:
    prog = program_from_dict(_old_cascade_program())
    assert set(prog.instances) == {"level_pi", "flow_pi"}
    assert prog.instances["level_pi"].template_id == PID_TEMPLATE_ID
    assert prog.instances["flow_pi"].template_id == PID_TEMPLATE_ID
    assert prog.instances["level_pi"].params["kp"] == pytest.approx(40.0)
    assert prog.instances["flow_pi"].params["kp"] == pytest.approx(12.0)
    assert prog.instances["level_pi"].params["hold_when_stopped"] is True
    assert prog.instances["flow_pi"].params["hold_when_stopped"] is False
    assert prog.instances["level_pi"].equation == PID_EQUATION
    assert prog.wires[0].src_instance == "level_pi"
    assert prog.wires[0].dst_instance == "flow_pi"


def test_place_copies_current_library_definition_and_isolates_existing_instances() -> None:
    state = AppState(initial_project=wedge_softplc_project())
    tmpl = state.library.get("builtin", PID_TEMPLATE_ID)
    assert tmpl is not None
    first = place_block(tmpl, "pid_a")
    changed = dict(state.library_template("builtin", PID_TEMPLATE_ID))
    changed["params"] = {**changed["params"], "kp": 7.0}
    changed["body"] = "cv = clamp((sp - pv) * kp, cv_min, cv_max)"
    state.save_shipped_template(PID_TEMPLATE_ID, changed)
    tmpl2 = state.library.get("builtin", PID_TEMPLATE_ID)
    assert tmpl2 is not None
    second = place_block(tmpl2, "pid_b")
    assert first.params["kp"] == pytest.approx(1.0)
    assert first.equation == PID_EQUATION
    assert second.params["kp"] == pytest.approx(7.0)
    assert second.equation == changed["body"]


def test_http_library_override_persists_and_reset_restores_factory(tmp_path) -> None:
    path = tmp_path / "program.json"
    state = AppState(initial_project=wedge_softplc_project(), program_path=str(path))
    with _Server(state) as srv:
        status, pid = _json_get(srv.base + "/api/library/shipped/PID")
        assert status == 200
        pid["params"]["kp"] = 5.0
        pid["body"] = "cv = clamp((sp - pv) * kp, cv_min, cv_max)"
        status, saved = _json_request(srv.base + "/api/library/shipped/PID", "PUT", pid)
        assert status == 200
        assert saved["params"]["kp"] == pytest.approx(5.0)

    restarted = AppState(program_path=str(path))
    assert restarted.library_template("builtin", PID_TEMPLATE_ID)["params"]["kp"] == pytest.approx(5.0)

    with _Server(restarted) as srv:
        status, reset = _json_request(srv.base + "/api/library/shipped/PID/reset", "POST")
        assert status == 200
        assert reset["params"]["kp"] == pytest.approx(1.0)

    reloaded = AppState(program_path=str(path))
    assert reloaded.library_template("builtin", PID_TEMPLATE_ID)["params"]["kp"] == pytest.approx(1.0)


def test_http_place_and_edit_instance_equation() -> None:
    state = AppState(initial_project=wedge_softplc_project())
    with _Server(state) as srv:
        status, prog = _json_request(
            srv.base + "/api/place",
            "POST",
            {"template_id": "PID", "library": "builtin", "instance_id": "pid_x"},
        )
        assert status == 200
        assert prog["instances"]["pid_x"]["equation"] == PID_EQUATION
        lib_before = state.library_template("builtin", PID_TEMPLATE_ID)["body"]
        sibling_eq = prog["instances"]["level_pi"]["equation"]
        prog["instances"]["pid_x"]["equation"] = "cv = 42.0"
        status, saved = _json_request(srv.base + "/api/program", "PUT", prog)
        assert status == 200
        assert saved["instances"]["pid_x"]["equation"] == "cv = 42.0"
        assert saved["instances"]["level_pi"]["equation"] == sibling_eq
        assert state.library_template("builtin", PID_TEMPLATE_ID)["body"] == lib_before
        status, _ = _json_request(
            srv.base + "/api/place",
            "POST",
            {"template_id": "PID", "library": "builtin", "instance_id": "pid_x"},
        )
        assert status == 409


def test_custom_library_survives_apply_and_restart(tmp_path) -> None:
    path = tmp_path / "program.json"
    state = AppState(initial_project=wedge_softplc_project(), program_path=str(path))
    custom = {
        "template_id": "gain",
        "description": "P gain",
        "pins": [
            {"name": "pv", "direction": "IN", "data_type": "float", "default": 0.0},
            {"name": "cv", "direction": "OUT", "data_type": "float", "default": 0.0},
        ],
        "params": {"kp": 2.0},
        "body": "cv = pv * kp",
    }
    with _Server(state) as srv:
        status, saved = _json_request(srv.base + "/api/library/custom", "POST", custom)
        assert status == 200
        assert saved["template_id"] == "gain"
        status, _ = _json_request(srv.base + "/api/apply", "POST", {"mode": "restart"})
        assert status == 200
        ids = {item["template_id"] for item in state.library_payload() if item.get("kind") == "custom"}
        assert "gain" in ids
        assert state.library.get("custom", "gain") is not None

    restarted = AppState(program_path=str(path))
    assert restarted.library.get("custom", "gain") is not None
    assert any(
        item["template_id"] == "gain" and item.get("kind") == "custom"
        for item in restarted.library_payload()
    )


def test_equation_errors_are_equation_error_not_raw() -> None:
    from plcassistant.surface.builtin import pid_template
    from plcassistant.surface.equations import EquationError, evaluate_equation

    tmpl = pid_template()
    pins = {"pv": 1.0, "sp": 0.0, "running": True}
    with pytest.raises(EquationError):
        evaluate_equation("cv = 1 / 0", tmpl, pins, tmpl.params, {}, 0.1)
    with pytest.raises(EquationError):
        evaluate_equation("# only comments", tmpl, pins, tmpl.params, {}, 0.1)


def test_system_migrated_tank_runs_two_pid_instances_under_mqtt() -> None:
    from plcassistant.app.runtime import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.binding import BindingTable
    from plcassistant.io.integration import MockEntityStore
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.io.mqtt_entity_bridge import MqttEntityBridge, default_wedge_binding_config
    from plcassistant.wedge.safety import Mode

    project = {
        "version": "2.0",
        "scan_period_s": 0.1,
        "programs": {"tank": _old_cascade_program()},
        "tasks": [{"id": "main", "priority": 1, "programs": ["tank"]}],
    }
    migrated = project_from_dict(project)
    assert migrated.programs["tank"].instances["level_pi"].template_id == PID_TEMPLATE_ID
    assert migrated.programs["tank"].instances["flow_pi"].template_id == PID_TEMPLATE_ID

    bus = InMemoryMqttBus()
    table = BindingTable.from_config(default_wedge_binding_config())
    entities = MockEntityStore()
    entities.set("number.plcassistant_sp_level_req", 0.20)
    entities.set("number.plcassistant_lt_tank_in", 0.15)
    entities.set("number.plcassistant_lt_res_in", 0.20)
    entities.set("number.plcassistant_ft_inlet_in", 0.0)

    image = declare_default_image()
    app = MqttIoBridge(bus, instance_id="default")
    app.start()
    integ = MqttEntityBridge(bus, table, entities, instance_id="default")
    integ.start()

    integ.publish_inputs()
    app.apply_inputs(image)
    logic = SkidImageLogic(period_s=0.1)
    logic.skid.program_loader.restart_apply(migrated)
    logic.enqueue_operator("start")
    for _ in range(6):
        logic(image)
    app.publish_outputs(image)
    integ.apply_outputs()

    assert logic.skid.last is not None
    assert logic.skid.last.mode is Mode.RUNNING
    assert entities.get("sensor.plcassistant_cmd_speed").value > 0.0
