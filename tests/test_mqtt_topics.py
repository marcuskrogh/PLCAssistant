"""MQTT topic helpers + payload codec (SWD-125 / A1)."""

from __future__ import annotations

import pytest

from plcassistant.io.mqtt_topics import (
    DEFAULT_INSTANCE_ID,
    MQTT_QOS,
    MqttTagPayload,
    cmd_topic,
    parse_tag_topic,
    status_topic,
    tag_in_topic,
    tag_out_topic,
)
from plcassistant.io.quality import QualityStatus, ReasonCode


def test_tag_topics_locked_shape():
    assert tag_in_topic("default", "LT_TANK") == "plcassistant/default/tag/LT_TANK/in"
    assert tag_out_topic("default", "CMD_SPEED") == "plcassistant/default/tag/CMD_SPEED/out"
    assert cmd_topic("default", "start") == "plcassistant/default/cmd/start"
    assert status_topic("plant1") == "plcassistant/plant1/status"
    assert DEFAULT_INSTANCE_ID == "default"
    assert MQTT_QOS == 1


def test_parse_tag_topic():
    assert parse_tag_topic("plcassistant/default/tag/LT_TANK/in") == (
        "default",
        "LT_TANK",
        "in",
    )
    assert parse_tag_topic("plcassistant/default/tag/CMD/out") == ("default", "CMD", "out")
    assert parse_tag_topic("other/default/tag/X/in") is None
    assert parse_tag_topic("plcassistant/default/cmd/start") is None


def test_payload_roundtrip():
    payload = MqttTagPayload.now(0.15, QualityStatus.GOOD)
    decoded = MqttTagPayload.decode(payload.encode())
    assert decoded.value == 0.15
    assert decoded.status is QualityStatus.GOOD
    assert decoded.reason is None
    assert decoded.ts is not None


def test_payload_bad_requires_reason():
    payload = MqttTagPayload(
        value=None,
        status=QualityStatus.BAD,
        reason=ReasonCode.UNAVAILABLE,
    )
    data = payload.to_dict()
    assert data["status"] == "BAD"
    assert data["reason"] == "unavailable"
    again = MqttTagPayload.from_dict(data)
    assert again.status is QualityStatus.BAD
    assert again.reason is ReasonCode.UNAVAILABLE


def test_payload_rejects_good_with_reason():
    with pytest.raises(ValueError):
        MqttTagPayload(value=1, status=QualityStatus.GOOD, reason=ReasonCode.FAULT)
