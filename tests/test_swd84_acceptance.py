"""SWD-84 acceptance aggregation (SWD-124 / A1–A6)."""

from __future__ import annotations

import pathlib

import pytest

from plcassistant.io.image import IoImage
from plcassistant.io.integration import ThinIntegrationStub
from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
from plcassistant.io.mqtt_topics import MqttTagPayload, tag_in_topic

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_a1_packaging_docs_present():
    pkg = ROOT / "docs" / "packaging"
    for name in ("README.md", "01-shape.md", "02-mqtt-topics.md", "03-acceptance.md"):
        assert (pkg / name).is_file()


def test_a2_mqtt_mock_roundtrip_without_broker():
    bus = InMemoryMqttBus()
    bridge = MqttIoBridge(bus, instance_id="default")
    bridge.start()
    image = IoImage()
    image.declare("LT_TANK", default=0.0)
    image.declare("CMD_SPEED", default=0.0)
    bus.publish(tag_in_topic("default", "LT_TANK"), MqttTagPayload.now(0.3).encode())
    bridge.apply_inputs(image)
    image.set_output("CMD_SPEED", 30.0)
    assert bridge.publish_outputs(image) == ("CMD_SPEED",)


def test_a3_a5_scaffold_trees():
    assert (ROOT / "ha_app" / "plcassistant" / "config.yaml").is_file()
    assert (ROOT / "ha_app" / "repository.yaml").is_file()
    assert (ROOT / "custom_components" / "plcassistant" / "manifest.json").is_file()


def test_a6_non_ha_stub_still_works():
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


def test_program_path_persistence(tmp_path):
    """App program-of-record survives reload via program_path (H6 automated slice)."""
    from plcassistant.app.server import AppState

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
    reloaded = AppState(program_path=str(path))
    assert reloaded.program_dict["version"] == "1.0"
