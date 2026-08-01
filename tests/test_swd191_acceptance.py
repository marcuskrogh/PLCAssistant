"""SWD-191 acceptance: saved Task schedule editor + restart apply."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer
from typing import Any

from plcassistant.app.runtime import MqttLifecycle, MqttScanLoop, declare_default_image
from plcassistant.app.server import AppState, make_handler
from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
from plcassistant.surface.builtin import wedge_softplc_project
from plcassistant.surface.model import Program, SoftPlcProject, Task
from plcassistant.surface.schema import project_from_dict, project_to_dict


def _project_with_aux() -> dict[str, Any]:
    project = wedge_softplc_project()
    project["programs"]["aux"] = {
        "version": "1.0",
        "name": "Aux",
        "description": "Auxiliary draft",
        "instances": {},
        "wires": [],
        "execution_order": [],
    }
    return project


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


def test_task_description_round_trip() -> None:
    project = SoftPlcProject(
        programs={"tank": Program(name="Tank")},
        tasks=[Task("main", 1, ["tank"], "Primary scan")],
    )
    raw = project_to_dict(project)
    assert raw["tasks"][0]["description"] == "Primary scan"

    loaded = project_from_dict(raw)
    assert loaded.tasks[0].description == "Primary scan"


def test_picker_eligibility_and_delete_unschedules_zero_tasks() -> None:
    state = AppState(initial_project=_project_with_aux())
    assert [item["id"] for item in state.unscheduled_programs()] == ["aux"]

    state.create_task("aux-task", 2, "Auxiliary")
    state.set_task_programs("aux-task", ["aux"])
    assert state.unscheduled_programs() == []

    state.delete_task("aux-task")
    assert [item["id"] for item in state.unscheduled_programs()] == ["aux"]

    state.delete_task("main")
    assert state.tasks_payload() == []
    assert {item["id"] for item in state.unscheduled_programs()} == {"tank", "aux"}


def test_save_without_apply_leaves_live_unchanged_then_apply_updates() -> None:
    state = AppState(initial_project=wedge_softplc_project())
    assert state.program_card("tank")["task_id"] == "main"

    state.create_task("process", 1, "Process scan")
    state.set_task_programs("main", [])
    state.set_task_programs("process", ["tank"])
    state.delete_task("main")
    saved = state.save_schedule()

    assert saved["saved_applied"] is False
    assert state.program_card("tank")["task_id"] == "main"
    assert state.program_card("tank")["saved_task_id"] == "process"
    assert state.program_card("tank")["pending_schedule"] is True

    applied = state.apply_saved_schedule()
    assert applied["saved_applied"] is True
    assert state.program_card("tank")["task_id"] == "process"
    assert state.program_card("tank")["pending_schedule"] is False


def test_http_task_crud_save_apply_and_reload_from_disk(tmp_path) -> None:
    path = tmp_path / "program.json"
    state = AppState(initial_project=_project_with_aux(), program_path=str(path))
    with _Server(state) as srv:
        status, tasks = _json_get(srv.base + "/api/tasks")
        assert status == 200
        assert tasks[0]["id"] == "main"

        status, unscheduled = _json_get(srv.base + "/api/programs/unscheduled")
        assert status == 200
        assert [item["id"] for item in unscheduled] == ["aux"]

        status, created = _json_request(
            srv.base + "/api/tasks",
            "POST",
            {"id": "aux-task", "priority": 2, "description": "Auxiliary scan"},
        )
        assert status == 201
        assert created["description"] == "Auxiliary scan"

        status, updated = _json_request(
            srv.base + "/api/tasks/aux-task/programs",
            "PUT",
            {"programs": ["aux"]},
        )
        assert status == 200
        assert updated["programs"] == ["aux"]

        status, renamed = _json_request(
            srv.base + "/api/tasks/aux-task",
            "PUT",
            {"id": "support", "priority": 3, "description": "Renamed"},
        )
        assert status == 200
        assert renamed["id"] == "support"
        assert renamed["priority"] == 3

        status, deleted = _json_request(srv.base + "/api/tasks/main", "DELETE")
        assert status == 200
        assert deleted["deleted"] == "main"

        status, saved = _json_request(srv.base + "/api/schedule/save", "POST")
        assert status == 200
        assert saved["saved_applied"] is False
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        assert on_disk["version"] == "2.0"
        assert on_disk["project"]["tasks"][0]["id"] == "support"
        assert on_disk["applied_project"]["tasks"][0]["id"] == "main"

    restarted = AppState(program_path=str(path))
    assert restarted.tasks_payload()[0]["id"] == "support"
    assert restarted.program_card("aux")["task_id"] is None
    assert restarted.program_card("aux")["saved_task_id"] == "support"

    applied = restarted.apply_saved_schedule()
    assert applied["saved_applied"] is True
    assert restarted.program_card("aux")["task_id"] == "support"


def test_system_reload_saved_schedule_then_apply_with_mqtt_runtime(tmp_path) -> None:
    path = tmp_path / "program.json"
    state = AppState(initial_project=wedge_softplc_project(), program_path=str(path))
    state.create_task("process", 1, "Process scan")
    state.set_task_programs("main", [])
    state.set_task_programs("process", ["tank"])
    state.delete_task("main")
    state.save_schedule()

    restarted = AppState(program_path=str(path))
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id=restarted.instance_id)
    loop = MqttScanLoop(bridge, image, period_s=0.1)
    life = MqttLifecycle()
    life.attach(loop)
    restarted.attach_runtime(life)
    bridge.start()
    loop.start()
    try:
        assert restarted.program_card("tank")["task_id"] == "main"
        assert restarted.program_card("tank")["saved_task_id"] == "process"

        restarted.apply_saved_schedule()
        assert restarted.program_card("tank")["task_id"] == "process"
        assert restarted.program_card("tank")["pending_schedule"] is False
        live_loader = restarted._live_skid_loader()
        assert live_loader is not None
        live_project = live_loader.project
        assert live_project is not None
        assert [t.task_id for t in live_project.tasks] == ["process"]
        assert live_project.tasks[0].programs == ["tank"]
        loop.scan_once()
    finally:
        life.stop()
