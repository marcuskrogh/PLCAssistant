"""SWD-182 integration: project scan_period_s drives skid dt and MQTT status."""

from __future__ import annotations

import json

import pytest

from plcassistant.app.runtime import MqttScanLoop
from plcassistant.app.skid_scan import SkidImageLogic
from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
from plcassistant.io.mqtt_topics import status_topic
from plcassistant.surface.builtin import wedge_softplc_project
from plcassistant.surface.schema import project_from_dict


def _status_payloads(bus: InMemoryMqttBus, instance_id: str = "default") -> list[dict]:
    topic = status_topic(instance_id)
    return [
        json.loads(payload.decode("utf-8"))
        for t, payload, _qos, _retain in bus.published
        if t == topic
    ]


def test_project_scan_period_propagates_to_skid_and_mqtt():
    """Load project scan_period_s=0.05; scan tick and MQTT status match."""
    proj = project_from_dict(wedge_softplc_project(scan_period_s=0.05))
    logic = SkidImageLogic()
    loader = logic.skid.program_loader
    assert loader is not None
    loader.load(proj)

    assert logic.skid.config.scan.scan_period_s == pytest.approx(0.05)
    assert logic._scan_dt() == pytest.approx(0.05)

    bus = InMemoryMqttBus()
    from plcassistant.app.default_image import declare_default_image

    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, logic=logic, period_s=logic.period_s)
    bridge.start()
    loop.scan_once()

    statuses = _status_payloads(bus)
    assert statuses
    assert statuses[-1].get("scan_period_s") == pytest.approx(0.05)


def test_skid_tick_uses_project_scan_period_as_dt():
    """Block-runtime tick receives dt from propagated project scan_period_s."""
    proj = project_from_dict(wedge_softplc_project(scan_period_s=0.05))
    logic = SkidImageLogic()
    loader = logic.skid.program_loader
    assert loader is not None
    loader.load(proj)

    from plcassistant.app.default_image import declare_default_image
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    image.apply_input("SP_LEVEL_REQ", 0.20, QualityStatus.GOOD)
    image.apply_input("LT_TANK", 0.15, QualityStatus.GOOD)
    image.apply_input("LT_RES", 0.20, QualityStatus.GOOD)
    image.apply_input("FT_INLET", 0.0, QualityStatus.GOOD)

    logic.enqueue_operator("start")
    logic(image)

    diag = logic.skid.last and logic.skid.last.scan_diagnostics
    assert diag is not None
    assert diag.last_dt_s == pytest.approx(0.05)
