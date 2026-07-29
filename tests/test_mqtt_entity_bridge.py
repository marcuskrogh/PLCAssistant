"""Integration-side MQTT entity bridge + App↔HA round-trip (fix-forward)."""

from __future__ import annotations

from plcassistant.io import (
    BindingTable,
    InMemoryMqttBus,
    MqttEntityBridge,
    MqttIoBridge,
    MockEntityStore,
    QualityStatus,
    default_wedge_binding_config,
)
from plcassistant.app.runtime import MqttScanLoop, declare_default_image
from plcassistant.app.skid_scan import SkidImageLogic
from plcassistant.io.mqtt_topics import MqttTagPayload, cmd_topic, tag_in_topic
from plcassistant.io.quality import ReasonCode


def test_entity_bridge_roundtrip_with_skid_logic():
    bus = InMemoryMqttBus()
    table = BindingTable.from_config(default_wedge_binding_config())
    entities = MockEntityStore()
    entities.set("number.plcassistant_sp_level_req", 0.20)
    entities.set("number.plcassistant_lt_tank_in", 0.15)
    entities.set("number.plcassistant_lt_res_in", 0.20)
    entities.set("number.plcassistant_ft_inlet_in", 0.0)

    app_image = declare_default_image()
    app = MqttIoBridge(bus, instance_id="default")
    app.start()
    integ = MqttEntityBridge(bus, table, entities, instance_id="default")
    integ.start()

    integ.publish_inputs()
    app.apply_inputs(app_image)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(app_image)
    for _ in range(5):
        logic(app_image)
    app.publish_outputs(app_image)
    applied = integ.apply_outputs()

    assert "CMD_SPEED" in applied
    assert "LT_TANK" not in applied
    assert entities.get("sensor.plcassistant_cmd_speed").value > 0.0
    assert entities.get("sensor.plcassistant_cmd_speed").status is QualityStatus.GOOD


def test_ha_default_bindings_match_app_wedge_config():
    """HA thin-integration defaults must equal App packaging bindings (SWD-131)."""
    import ast
    import pathlib

    init_path = pathlib.Path("custom_components/plcassistant/__init__.py")
    tree = ast.parse(init_path.read_text(encoding="utf-8"))
    fn = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "_default_bindings"
    )
    ret = next(s for s in fn.body if isinstance(s, ast.Return))
    ha_bindings = ast.literal_eval(ret.value)

    app_bindings = default_wedge_binding_config()["bindings"]
    assert ha_bindings == app_bindings
    assert {b["tag"] for b in ha_bindings} >= {
        "LT_TANK",
        "LT_RES",
        "FT_INLET",
        "CMD_SPEED",
        "SP_LEVEL_REQ",
        "SP_LEVEL",
        "SP_FLOW",
        "MODE",
        "PERM_OK",
        "TRIP_ACTIVE",
    }
    by_tag = {b["tag"]: b for b in ha_bindings}
    assert by_tag["SP_LEVEL_REQ"]["direction"] == "IN"
    assert by_tag["LT_TANK"]["direction"] == "IN"
    assert by_tag["LT_RES"]["direction"] == "IN"
    assert by_tag["FT_INLET"]["direction"] == "IN"
    assert by_tag["SP_FLOW"]["direction"] == "OUT"
    assert by_tag["MODE"]["direction"] == "OUT"


def test_scan_loop_once_and_commands():
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.01)
    bridge.start()
    assert loop.scanning is False

    bus.publish(
        tag_in_topic("default", "SP_LEVEL_REQ"),
        MqttTagPayload.now(0.2).encode(),
    )
    bus.publish(cmd_topic("default", "start"), b"1")
    loop.scan_once()
    assert loop.scanning is True
    # First RUNNING scan may still show 0 CVs; plant moves on subsequent scans.
    loop.scan_once()
    assert image.get_value("CMD_SPEED") > 0.0
    assert image.get_value("SP_FLOW") > 0.0

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
