"""Skid-backed Soft-PLC scan body (SWD-133)."""

from __future__ import annotations

from plcassistant.app.default_image import declare_default_image
from plcassistant.app.skid_scan import SkidImageLogic
from plcassistant.io.quality import QualityStatus
from plcassistant.wedge.skid import Mode


def test_skid_image_logic_start_moves_flow_and_tank():
    image = declare_default_image()
    image.begin_inputs()
    image.apply_input("SP_LEVEL_REQ", 0.20, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    assert logic.skid.last is not None
    assert logic.skid.last.mode is Mode.RUNNING
    assert image.get_value("MODE") == "RUNNING"
    for _ in range(20):
        logic(image)
    assert float(image.get_value("SP_FLOW")) > 0.0
    assert float(image.get_value("CMD_SPEED")) > 0.0
    assert float(image.get_value("LT_TANK")) > 0.0


def test_scan_loop_start_publishes_status_with_mode():
    from plcassistant.app.runtime import MqttScanLoop
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.io.mqtt_topics import cmd_topic, status_topic

    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.01)
    bridge.start()
    bus.publish(cmd_topic("default", "start"), b"1")
    loop.scan_once()
    assert loop.scanning is True
    assert image.get_value("MODE") == "RUNNING"
    statuses = [
        __import__("json").loads(payload.decode("utf-8"))
        for topic, payload, _qos, _retain in bus.published
        if topic == status_topic("default")
    ]
    assert statuses
    assert statuses[-1]["state"] == "running"
    assert statuses[-1].get("mode") == "RUNNING"


def test_skid_image_logic_stop_zeros_cmd():
    image = declare_default_image()
    image.apply_input("SP_LEVEL_REQ", 0.20, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    for _ in range(10):
        logic(image)
    logic.enqueue_operator("stop")
    logic(image)
    assert logic.skid.last.mode is Mode.STOP
    assert float(image.get_value("CMD_SPEED")) == 0.0


def test_skid_reset_does_not_stop_healthy_run():
    """HMI_RESET clears latches; it must not stop a healthy RUNNING skid."""
    image = declare_default_image()
    image.apply_input("SP_LEVEL_REQ", 0.20, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    for _ in range(5):
        logic(image)
    assert logic.is_running is True
    logic.enqueue_operator("reset")
    logic(image)
    assert logic.skid.last.mode is Mode.RUNNING
    assert float(image.get_value("CMD_SPEED")) > 0.0


def test_scan_loop_reset_keeps_running_when_healthy():
    from plcassistant.app.runtime import MqttScanLoop
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.io.mqtt_topics import MqttTagPayload, cmd_topic, tag_in_topic

    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.01)
    bridge.start()
    bus.publish(tag_in_topic("default", "SP_LEVEL_REQ"), MqttTagPayload.now(0.2).encode())
    bus.publish(cmd_topic("default", "start"), b"1")
    loop.scan_once()
    loop.scan_once()
    assert loop.scanning is True
    bus.publish(cmd_topic("default", "reset"), b"1")
    loop.scan_once()
    assert loop.scanning is True
    assert float(image.get_value("CMD_SPEED")) > 0.0
