"""SWD-182 system acceptance: HA + App + MQTT project organization."""

from __future__ import annotations

import json
import pathlib
import threading
import urllib.request
from http.server import HTTPServer

import pytest

from plcassistant.app.runtime import declare_default_image
from plcassistant.app.server import AppState, make_handler
from plcassistant.app.skid_scan import SkidImageLogic
from plcassistant.io.integration import MockEntityStore
from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
from plcassistant.io.mqtt_entity_bridge import MqttEntityBridge, default_wedge_binding_config
from plcassistant.io.binding import BindingTable
from plcassistant.surface.builtin import wedge_softplc_project
from plcassistant.surface.schema import is_legacy_program_dict, project_from_dict
from plcassistant.wedge.safety import Mode

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_legacy_program_migrates_to_project_on_load():
    flat = wedge_softplc_project()["programs"]["tank"]
    assert is_legacy_program_dict(flat)
    proj = project_from_dict(flat)
    assert proj.tasks[0].task_id == "main"
    assert "main" in proj.programs or "tank" in proj.programs


def test_skid_loads_softplc_project():
    logic = SkidImageLogic(period_s=0.1)
    loader = logic.skid.program_loader
    assert loader is not None
    assert loader.project is not None
    assert loader.project.tasks
    assert loader.program is not None
    assert "level_pi" in loader.program.instances


def test_app_project_api_roundtrip(tmp_path):
    path = tmp_path / "program.json"
    state = AppState(program_path=str(path))
    handler = make_handler(state)
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    base = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(base + "/api/project") as resp:
            project = json.loads(resp.read())
        assert project["version"] == "2.0"
        assert "tasks" in project
        assert "programs" in project
        assert "tank" in project["programs"]

        with urllib.request.urlopen(base + "/api/program") as resp:
            program = json.loads(resp.read())
        assert "level_pi" in program["instances"]

        # PUT project with logic-only tweak → hot when superuser enabled
        state.superuser_hot_apply = True
        tweaked = json.loads(json.dumps(project))
        tweaked["programs"]["tank"]["instances"]["level_pi"]["params"]["kp"] = 42.0
        req = urllib.request.Request(
            base + "/api/project",
            data=json.dumps(tweaked).encode(),
            method="PUT",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
        with urllib.request.urlopen(base + "/api/program") as resp:
            updated = json.loads(resp.read())
        assert updated["instances"]["level_pi"]["params"]["kp"] == 42.0
        assert path.is_file()
        on_disk = json.loads(path.read_text())
        assert on_disk["version"] == "2.0"
    finally:
        server.shutdown()


def test_ha_app_mqtt_roundtrip_with_project():
    """Full stack: migrated tank project runs Main Task under MQTT scan."""
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
    assert logic.skid.program_loader is not None
    assert logic.skid.program_loader.project is not None
    logic.enqueue_operator("start")
    logic(image)
    for _ in range(5):
        logic(image)
    app.publish_outputs(image)
    applied = integ.apply_outputs()
    assert "CMD_SPEED" in applied
    assert logic.skid.last is not None
    assert logic.skid.last.mode is Mode.RUNNING
    assert entities.get("sensor.plcassistant_cmd_speed").value > 0.0
