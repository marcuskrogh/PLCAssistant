"""SWD-181 acceptance: Program cards + Diagram/Log/Settings surface."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer
from typing import Any

import pytest

from plcassistant.app.runtime import MqttLifecycle, MqttScanLoop
from plcassistant.app.server import AppState, make_handler
from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
from plcassistant.surface.builtin import wedge_softplc_project
from plcassistant.surface.model import Program, SoftPlcProject, Task
from plcassistant.surface.program_status import (
    health_from_log,
    program_run_status,
    program_schedule_status,
)
from plcassistant.surface.schema import project_to_dict


def _get(url: str) -> tuple[int, bytes, str]:
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), ""


def _json_get(url: str) -> tuple[int, Any]:
    status, body, _ = _get(url)
    return status, json.loads(body)


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


class _Server:
    def __init__(self, state: AppState) -> None:
        self.state = state
        self.server = HTTPServer(("127.0.0.1", 0), make_handler(state))
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> "_Server":
        self.thread.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.server.shutdown()


def test_status_and_health_helpers() -> None:
    project = SoftPlcProject(
        programs={"tank": Program(name="Tank"), "spare": Program(name="Spare")},
        tasks=[Task("main", 1, ["tank"])],
    )
    assert program_schedule_status(project, "tank") == "scheduled"
    assert program_schedule_status(project, "spare") == "unscheduled"
    assert program_run_status(project, "tank", False) == "not running"
    assert program_run_status(project, "tank", True) == "running"
    assert program_run_status(project, "spare", True) == "unscheduled"
    assert health_from_log([]) == "ok"
    assert health_from_log([{"level": "warning"}]) == "warning"
    assert health_from_log([{"level": "info"}, {"level": "error"}]) == "error"


def test_create_meta_and_delete_program_state() -> None:
    state = AppState(initial_project=wedge_softplc_project())
    card = state.create_program("Batch Mix", "Empty draft")
    assert card["id"] == "batch-mix"
    assert card["status"] == "unscheduled"
    created = state.program_for_id("batch-mix")
    assert created is not None
    assert created.instances == {}
    assert created.execution_order == []

    before = set(state.program_for_id("tank").instances)
    renamed = state.update_program_meta("tank", "Tank v2", "same graph")
    assert renamed["name"] == "Tank v2"
    assert set(state.program_for_id("tank").instances) == before

    state.delete_program("tank")
    project = state.loader.project
    assert project is not None
    assert "tank" not in project.programs
    assert all("tank" not in task.programs for task in project.tasks)


def test_http_create_get_meta_diagram_put_log_delete_and_html(tmp_path) -> None:
    state = AppState(initial_project=wedge_softplc_project(), program_path=str(tmp_path / "program.json"))
    with _Server(state) as srv:
        status, body, content_type = _get(srv.base + "/")
        assert status == 200
        html = body.decode("utf-8")
        assert "program-card" in html
        assert "#/programs/new" in html
        assert "#/programs/<id>/diagram" not in html
        assert "Diagram" in html and "Log" in html and "Settings" in html
        assert "text/html" in content_type

        status, created = _json_request(
            srv.base + "/api/programs",
            "POST",
            {"name": "Aux Pump", "description": "Standby logic"},
        )
        assert status == 201
        assert created["id"] == "aux-pump"
        assert created["status"] == "unscheduled"
        assert created["health"] == "ok"

        status, prog = _json_get(srv.base + "/api/programs/aux-pump")
        assert status == 200
        assert prog["name"] == "Aux Pump"
        assert prog["description"] == "Standby logic"
        assert prog["instances"] == {}

        status, meta = _json_request(
            srv.base + "/api/programs/aux-pump/meta",
            "PUT",
            {"name": "Aux Pump 2", "description": "Renamed only"},
        )
        assert status == 200
        assert meta["name"] == "Aux Pump 2"
        status, blank = _json_request(
            srv.base + "/api/programs/aux-pump/meta",
            "PUT",
            {"name": "   ", "description": "blank rejected"},
        )
        assert status == 400
        status, renamed = _json_get(srv.base + "/api/program?id=aux-pump")
        assert status == 200
        assert renamed["instances"] == {}

        replacement = {
            "version": "1.0",
            "name": "Aux Pump 2",
            "description": "Renamed only",
            "instances": {
                "flow_pi": {
                    "template_id": "flow_pi",
                    "library": "builtin",
                    "params": {"kp": 12.0, "ki": 2.0, "cv_min": 0.0, "cv_max": 100.0},
                }
            },
            "wires": [],
            "execution_order": ["flow_pi"],
        }
        status, saved = _json_request(srv.base + "/api/program?id=aux-pump", "PUT", replacement)
        assert status == 200
        assert "flow_pi" in saved["instances"]
        status, opened = _json_get(srv.base + "/api/program?id=aux-pump")
        assert status == 200
        assert "flow_pi" in opened["instances"]

        status, log = _json_get(srv.base + "/api/programs/aux-pump/log")
        assert status == 200
        assert any(entry["level"] == "info" for entry in log)

        status, deleted = _json_request(srv.base + "/api/programs/aux-pump", "DELETE")
        assert status == 200
        assert deleted["deleted"] == "aux-pump"
        status, missing = _json_get(srv.base + "/api/programs/aux-pump")
        assert status == 404
        assert "not found" in missing["error"].lower()


def test_encoded_program_id_and_scoped_user_templates(tmp_path) -> None:
    from plcassistant.surface.user_library import make_user_template

    project = wedge_softplc_project()
    project["programs"]["aux pump"] = {
        "version": "1.0",
        "name": "Aux Pump",
        "description": "",
        "instances": {},
        "wires": [],
        "execution_order": [],
        "user_templates": {},
    }
    state = AppState(initial_project=project, program_path=str(tmp_path / "program.json"))
    a = state.create_program("Alpha")
    b = state.create_program("Beta")
    prog_a = state.program_for_id(a["id"])
    prog_b = state.program_for_id(b["id"])
    assert prog_a is not None and prog_b is not None
    tmpl_a = make_user_template(
        "calc",
        body="out = 1",
        pins=[
            {"name": "out", "direction": "OUT", "data_type": "float"},
        ],
        description="A",
    )
    tmpl_b = make_user_template(
        "calc",
        body="out = 2",
        pins=[
            {"name": "out", "direction": "OUT", "data_type": "float"},
        ],
        description="B",
    )
    prog_a.user_templates["calc"] = tmpl_a
    prog_b.user_templates["calc"] = tmpl_b
    state.library.register(tmpl_b)  # last-wins global registration
    state.library.register(tmpl_a)
    state.persist_program()

    with _Server(state) as srv:
        status, got = _json_get(srv.base + "/api/programs/aux%20pump")
        assert status == 200
        assert got["name"] == "Aux Pump"

        status, place_a = _json_request(
            srv.base + "/api/place",
            "POST",
            {
                "program_id": a["id"],
                "template_id": "calc",
                "library": "user",
                "instance_id": "calc_a",
            },
        )
        assert status == 200
        assert place_a["instances"]["calc_a"]["template_id"] == "calc"
        resolved_a = state.resolve_template(a["id"], "user", "calc")
        resolved_b = state.resolve_template(b["id"], "user", "calc")
        assert resolved_a is not None and resolved_b is not None
        assert resolved_a.description == "A"
        assert resolved_b.description == "B"

        status, lib_a = _json_get(srv.base + f"/api/library?id={a['id']}")
        assert status == 200
        user_a = [t for t in lib_a if t["library"] == "user" and t["template_id"] == "calc"]
        assert len(user_a) == 1
        assert user_a[0]["description"] == "A"


def test_system_app_mqtt_program_cards_and_opening_program_api() -> None:
    from plcassistant.app.runtime import declare_default_image

    state = AppState(initial_project=wedge_softplc_project())
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id=state.instance_id)
    loop = MqttScanLoop(bridge, image, period_s=0.1)
    life = MqttLifecycle()
    life.attach(loop)
    state.attach_runtime(life)
    bridge.start()
    loop.start()

    with _Server(state) as srv:
        try:
            status, cards = _json_get(srv.base + "/api/programs")
            assert status == 200
            tank = next(card for card in cards if card["id"] == "tank")
            assert tank["name"] == "Tank"
            assert tank["task_id"] == "main"
            assert tank["status"] in {"not running", "running"}
            assert tank["health"] == "ok"

            status, tank_program = _json_get(srv.base + "/api/programs/tank")
            assert status == 200
            assert tank_program["name"] == "Tank"
            assert "level_pi" in tank_program["instances"]

            state.superuser_hot_apply = True
            project = state.loader.project
            assert project is not None
            raw = project_to_dict(project)
            raw["programs"]["tank"]["instances"]["level_pi"]["params"]["kp"] = 41.0
            status, saved = _json_request(srv.base + "/api/project", "PUT", raw)
            assert status == 200
            assert saved["programs"]["tank"]["instances"]["level_pi"]["params"]["kp"] == pytest.approx(41.0)
        finally:
            life.stop()
