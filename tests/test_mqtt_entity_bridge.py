"""Integration-side MQTT entity bridge + App↔HA round-trip (fix-forward)."""

from __future__ import annotations

from plcassistant.io import (
    BindingTable,
    InMemoryMqttBus,
    IoImage,
    MqttEntityBridge,
    MqttIoBridge,
    MockEntityStore,
    QualityStatus,
    default_wedge_binding_config,
)
from plcassistant.app.runtime import MqttScanLoop, declare_default_image, default_scan_logic


def test_entity_bridge_roundtrip_with_app_bridge():
    bus = InMemoryMqttBus()
    table = BindingTable.from_config(default_wedge_binding_config())
    entities = MockEntityStore()
    entities.set("number.plcassistant_lt_tank_in", 0.25)

    app_image = declare_default_image()
    app = MqttIoBridge(bus, instance_id="default")
    app.start()
    integ = MqttEntityBridge(bus, table, entities, instance_id="default")
    integ.start()

    integ.publish_inputs()
    app.apply_inputs(app_image)
    default_scan_logic(app_image)
    app.publish_outputs(app_image)
    applied = integ.apply_outputs()

    assert "CMD_SPEED" in applied
    assert entities.get("number.plcassistant_cmd_speed_out").value == 25.0
    assert entities.get("number.plcassistant_cmd_speed_out").status is QualityStatus.GOOD
    assert "FT_INLET" in table.tags
    assert any(b.tag == "FT_INLET" for b in table.bindings)


def test_scan_loop_once_and_commands():
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.01)
    bridge.start()
    from plcassistant.io.mqtt_topics import MqttTagPayload, cmd_topic, tag_in_topic

    bus.publish(tag_in_topic("default", "LT_TANK"), MqttTagPayload.now(0.1).encode())
    loop.scan_once()
    assert image.get_value("LT_TANK") == 0.1
    assert image.get_value("CMD_SPEED") == 10.0

    bus.publish(cmd_topic("default", "stop"), b"1")
    loop.scan_once()
    assert loop.scanning is False
    bus.publish(cmd_topic("default", "start"), b"1")
    loop.scan_once()
    assert loop.scanning is True


def test_topic_parity_with_custom_component():
    """HA copy of topic helpers must match Soft-PLC map (Architecture note)."""
    import pathlib
    import re

    from plcassistant.io import mqtt_topics as core

    text = pathlib.Path("custom_components/plcassistant/mqtt_topics.py").read_text(
        encoding="utf-8"
    )
    assert 'f"{TOPIC_ROOT}/{instance_id}/tag/{tag}/in"' in text
    assert 'f"{TOPIC_ROOT}/{instance_id}/tag/{tag}/out"' in text
    assert 'f"{TOPIC_ROOT}/{instance_id}/cmd/{name}"' in text
    assert 'f"{TOPIC_ROOT}/{instance_id}/status"' in text
    const = pathlib.Path("custom_components/plcassistant/const.py").read_text(
        encoding="utf-8"
    )
    assert re.search(r'TOPIC_ROOT\s*=\s*"plcassistant"', const)
    assert core.TOPIC_ROOT == "plcassistant"
    assert core.tag_in_topic("default", "LT_TANK") == "plcassistant/default/tag/LT_TANK/in"
