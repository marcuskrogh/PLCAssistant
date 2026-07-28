"""SWD-84 acceptance aggregation (SWD-124)."""

from __future__ import annotations

import pathlib

import pytest

from plcassistant.io.image import IoImage
from plcassistant.io.integration import ThinIntegrationStub
from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
from plcassistant.io.mqtt_entity_bridge import (
    MqttEntityBridge,
    default_wedge_binding_config,
)
from plcassistant.io.mqtt_topics import MqttTagPayload, tag_in_topic
from plcassistant.io.binding import BindingTable
from plcassistant.io.integration import MockEntityStore
from plcassistant.app.runtime import default_scan_logic, declare_default_image

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_packaging_docs_present():
    pkg = ROOT / "docs" / "packaging"
    for name in ("README.md", "01-shape.md", "02-mqtt-topics.md", "03-acceptance.md"):
        assert (pkg / name).is_file()


def test_app_ha_mqtt_roundtrip_without_broker():
    """App bridge + integration-side bridge over in-memory bus (PLAN MQTT AC)."""
    bus = InMemoryMqttBus()
    table = BindingTable.from_config(default_wedge_binding_config())
    entities = MockEntityStore()
    entities.set("number.plcassistant_lt_tank_in", 0.3)

    image = declare_default_image()
    app = MqttIoBridge(bus, instance_id="default")
    app.start()
    integ = MqttEntityBridge(bus, table, entities, instance_id="default")
    integ.start()

    integ.publish_inputs()
    app.apply_inputs(image)
    default_scan_logic(image)
    app.publish_outputs(image)
    integ.apply_outputs()
    assert entities.get("number.plcassistant_cmd_speed_out").value == pytest.approx(30.0)


def test_scaffold_and_github_app_trees():
    assert (ROOT / "plc_assistant" / "config.yaml").is_file()
    assert (ROOT / "repository.yaml").is_file()
    assert (ROOT / "custom_components" / "plcassistant" / "manifest.json").is_file()
    assert (ROOT / "custom_components" / "plcassistant" / "number.py").is_file()
    assert (ROOT / "custom_components" / "plcassistant" / "button.py").is_file()
    assert not (ROOT / "custom_components" / "plcassistant" / "sensor.py").exists()


def test_default_wedge_bindings_include_flow():
    cfg = default_wedge_binding_config()
    tags = set(cfg["tags"])
    assert {"LT_TANK", "LT_RES", "FT_INLET", "CMD_SPEED", "SP_LEVEL_REQ", "SP_LEVEL", "SP_FLOW"} <= tags
    bound = {b["tag"] for b in cfg["bindings"]}
    assert "FT_INLET" in bound
    assert any(b["tag"] == "FT_INLET" and b["direction"] == "IN" for b in cfg["bindings"])

def test_non_ha_stub_still_works():
    """In-process ThinIntegrationStub remains the non-HA CI path."""
    stub = ThinIntegrationStub(
        {
            "tags": {
                "LT_TANK": {"default": 0.0},
                "CMD_SPEED": {"default": 0.0},
            },
            "bindings": [
                {
                    "tag": "LT_TANK",
                    "entity": "sensor.lt",
                    "direction": "IN",
                    "scale": 1.0,
                },
                {
                    "tag": "CMD_SPEED",
                    "entity": "number.cmd",
                    "direction": "OUT",
                    "scale": 1.0,
                },
            ],
        }
    )
    image = stub.attach()
    stub.entities.set("sensor.lt", 0.25)

    def logic(img: IoImage) -> None:
        img.set_output("CMD_SPEED", img.get_value("LT_TANK") * 100.0)

    flush = stub.run_scan(image, logic)
    assert flush["number.cmd"] == pytest.approx(25.0)


def test_program_path_persistence_and_place(tmp_path):
    """Program-of-record survives reload; place persists (H6)."""
    from plcassistant.app.server import AppState, make_handler
    from http.server import HTTPServer
    from io import BytesIO
    import json

    path = tmp_path / "program.json"
    state = AppState(
        {
            "version": "1.0",
            "instances": {},
            "wires": [],
            "execution_order": [],
        },
        program_path=str(path),
    )
    state.persist_program()
    assert path.is_file()

    # Corrupt load recovers
    path.write_text("{not-json", encoding="utf-8")
    recovered = AppState(program_path=str(path))
    assert recovered.program_dict["version"] == "1.0"

    # Place persists
    state2 = AppState(program_path=str(path))
    # Ensure a builtin exists for place — use library after loader init
    from plcassistant.surface.builtin import register_builtins

    # place via mutating API: call persist after manual place through handler is heavy;
    # unit-level: mutate and persist_program already tested; exercise place path:
    handler_cls = make_handler(state2)
    # Simulate place by writing program then place_block through state
    from plcassistant.surface.schema import place_block

    tmpl = state2.library.get("builtin", "TON")
    if tmpl is None:
        # any builtin
        templates = state2.library.all_templates()
        assert templates
        tmpl = templates[0]
    prog = state2.loader.program
    assert prog is not None
    inst = place_block(tmpl, "i1", x=1.0, y=2.0)
    prog.instances["i1"] = inst
    prog.execution_order.append("i1")
    state2.persist_program()
    reloaded = AppState(program_path=str(path))
    assert "i1" in reloaded.program_dict["instances"]


def test_atomic_persist_does_not_leave_tmp(tmp_path):
    from plcassistant.app.server import AppState

    path = tmp_path / "program.json"
    state = AppState(program_path=str(path))
    state.persist_program()
    assert path.is_file()
    assert not (tmp_path / "program.json.tmp").exists()
