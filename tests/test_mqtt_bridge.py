"""MqttIoBridge with InMemoryMqttBus (SWD-125 / A2)."""

from __future__ import annotations

from plcassistant.io.image import IoImage
from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
from plcassistant.io.mqtt_topics import MqttTagPayload, tag_in_topic, tag_out_topic
from plcassistant.io.quality import QualityStatus, ReasonCode


def _image() -> IoImage:
    image = IoImage()
    image.declare("LT_TANK", default=0.0)
    image.declare("CMD_SPEED", default=0.0)
    return image


def test_bridge_receives_in_and_applies():
    bus = InMemoryMqttBus()
    bridge = MqttIoBridge(bus, instance_id="default")
    bridge.start()
    image = _image()

    bus.publish(
        tag_in_topic("default", "LT_TANK"),
        MqttTagPayload.now(0.42).encode(),
    )
    applied = bridge.apply_inputs(image)
    assert "LT_TANK" in applied
    assert image.get_value("LT_TANK") == 0.42
    assert image.get_quality("LT_TANK").status is QualityStatus.GOOD


def test_bridge_publishes_out():
    bus = InMemoryMqttBus()
    bridge = MqttIoBridge(bus, instance_id="default")
    bridge.start()
    image = _image()
    image.set_output("CMD_SPEED", 55.0)

    published = bridge.publish_outputs(image)
    assert published == ("CMD_SPEED",)
    topics = [t for t, *_ in bus.published]
    assert tag_out_topic("default", "CMD_SPEED") in topics
    raw = next(p for t, p, *_ in bus.published if t.endswith("/CMD_SPEED/out"))
    sample = MqttTagPayload.decode(raw)
    assert sample.value == 55.0
    assert sample.status is QualityStatus.GOOD


def test_bridge_roundtrip_in_to_out_logic():
    """Integration publishes IN; App applies, logic writes OUT; bridge publishes."""
    bus = InMemoryMqttBus()
    bridge = MqttIoBridge(bus, instance_id="skid")
    bridge.start()
    image = _image()

    bus.publish(
        tag_in_topic("skid", "LT_TANK"),
        MqttTagPayload.now(0.2).encode(),
    )
    bridge.apply_inputs(image)
    level = image.get_value("LT_TANK")
    image.set_output("CMD_SPEED", level * 100.0)
    bridge.publish_outputs(image)

    out = next(p for t, p, *_ in bus.published if t.endswith("/CMD_SPEED/out"))
    assert MqttTagPayload.decode(out).value == 20.0


def test_bad_payload_becomes_fault_quality():
    bus = InMemoryMqttBus()
    bridge = MqttIoBridge(bus)
    bridge.start()
    image = _image()
    bus.publish(tag_in_topic("default", "LT_TANK"), b"not-json")
    bridge.apply_inputs(image)
    q = image.get_quality("LT_TANK")
    assert q.status is QualityStatus.BAD
    assert q.reason is ReasonCode.FAULT
