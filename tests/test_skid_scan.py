"""Skid-backed Soft-PLC scan body (SWD-133)."""

from __future__ import annotations

from plcassistant.app.default_image import declare_default_image
from plcassistant.app.skid_scan import SkidImageLogic
from plcassistant.io.quality import QualityStatus
from plcassistant.wedge.process import HeldProcess, MockProcess
from plcassistant.wedge.skid import Mode


def test_skid_image_logic_start_drives_cv_without_plant_out():
    """SWD-145: control OUT moves; plant PVs are IN and stay static (no Soft-PLC physics)."""
    image = declare_default_image()
    image.begin_inputs()
    image.apply_input("SP_LEVEL_REQ", 0.20, QualityStatus.GOOD)
    image.apply_input("LT_TANK", 0.15, QualityStatus.GOOD)
    image.apply_input("LT_RES", 0.20, QualityStatus.GOOD)
    image.apply_input("FT_INLET", 0.0, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    assert isinstance(logic.skid.process, HeldProcess)
    assert not isinstance(logic.skid.process, MockProcess)
    logic.enqueue_operator("start")
    logic(image)
    assert logic.skid.last is not None
    assert logic.skid.last.mode is Mode.RUNNING
    assert image.get_value("MODE") == "RUNNING"
    tank0 = float(image.get_value("LT_TANK"))
    for _ in range(20):
        logic(image)
    assert float(image.get_value("SP_FLOW")) > 0.0
    assert float(image.get_value("CMD_SPEED")) > 0.0
    assert float(image.get_value("LT_TANK")) == tank0
    outs = image.snapshot_outputs()
    assert "LT_TANK" not in outs
    assert "LT_RES" not in outs
    assert "FT_INLET" not in outs
    assert "CMD_SPEED" in outs


def test_skid_plant_los_after_sample_trips():
    """SWD-145 review-fix: real BAD/unavailable after a GOOD sample must trip LOS."""
    from plcassistant.io.quality import ReasonCode
    from plcassistant.wedge.safety import TripCode

    image = declare_default_image()
    image.begin_inputs()
    image.apply_input("SP_LEVEL_REQ", 0.20, QualityStatus.GOOD)
    image.apply_input("LT_TANK", 0.15, QualityStatus.GOOD)
    image.apply_input("LT_RES", 0.20, QualityStatus.GOOD)
    image.apply_input("FT_INLET", 0.0, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    for _ in range(3):
        logic(image)
    assert logic.is_running is True
    # Simulate MQTT plant LOS after a valid sample.
    image.apply_input("LT_TANK", None, QualityStatus.BAD, ReasonCode.UNAVAILABLE)
    logic(image)
    assert logic.skid.last is not None
    assert logic.skid.last.mode is Mode.TRIPPED
    assert TripCode.LOS_LT_TANK in logic.skid.last.trip_codes
    assert image.get_value("TRIP_ACTIVE") is True


def test_skid_unsampled_plant_does_not_trip_on_boot():
    """Declared BAD/unavailable with no last_good must not block Start (HeldProcess hold)."""
    image = declare_default_image()
    image.begin_inputs()
    image.apply_input("SP_LEVEL_REQ", 0.20, QualityStatus.GOOD)
    # Plant tags remain declared-default BAD/unavailable (never sampled).
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    assert logic.skid.last is not None
    assert logic.skid.last.mode is Mode.RUNNING
    assert image.get_value("TRIP_ACTIVE") is False


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
    assert statuses[-1].get("scan_period_s") == 0.01


def test_scan_loop_status_heartbeat_republishes_when_idle():
    """SWD-136: retained status must republish so late HA listeners recover."""
    import json
    import time

    from plcassistant.app.runtime import MqttScanLoop
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.io.mqtt_topics import status_topic

    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.01)
    loop.STATUS_HEARTBEAT_S = 0.05
    # Single-threaded: no background scan thread (avoids racing assertions).
    bridge.start()
    loop._publish_scan_status("stopped")
    loop._last_status_heartbeat = time.monotonic() - 1.0
    before = len(bus.published)
    loop.scan_once()
    statuses = [
        json.loads(payload.decode("utf-8"))
        for topic, payload, _qos, retain in bus.published[before:]
        if topic == status_topic("default")
    ]
    assert statuses
    assert statuses[-1]["state"] == "stopped"
    assert statuses[-1].get("scan_period_s") == 0.01
    assert all(
        retain
        for topic, _payload, _qos, retain in bus.published[before:]
        if topic == status_topic("default")
    )


def test_parse_app_status_payload_vocabulary():
    """SWD-136: status chip vocabulary + legacy reset → stopped."""
    from plcassistant.io.mqtt_topics import parse_app_status_payload

    assert parse_app_status_payload('{"state":"stopped"}') == "stopped"
    assert parse_app_status_payload(b'{"state":"running"}') == "running"
    assert parse_app_status_payload('{"state":"reset"}') == "stopped"
    assert parse_app_status_payload('{"state":"offline"}') == "offline"
    assert parse_app_status_payload('{"state":"weird"}') == "fault"
    assert parse_app_status_payload("{}") is None
    assert parse_app_status_payload(None) is None


def test_paho_bus_sets_retained_offline_lwt_before_connect(monkeypatch):
    """SWD-136: will_set(status, offline, retain) must run before connect."""
    from plcassistant.io import mqtt_paho as paho_mod
    from plcassistant.io.mqtt_topics import MQTT_QOS, status_topic

    calls: list[tuple] = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def username_pw_set(self, *args, **kwargs):
            calls.append(("username_pw_set", args, kwargs))

        def will_set(self, topic, payload, qos=0, retain=False):
            calls.append(("will_set", topic, payload, qos, retain))

        def connect(self, host, port, keepalive=60):
            calls.append(("connect", host, port, keepalive))

        def loop_start(self):
            calls.append(("loop_start",))

    assert paho_mod.mqtt is not None
    monkeypatch.setattr(paho_mod.mqtt, "Client", FakeClient)
    will_topic = status_topic("default")
    will_payload = b'{"state":"offline"}'
    paho_mod.PahoMqttBus(
        "core-mosquitto",
        1883,
        will_topic=will_topic,
        will_payload=will_payload,
    )
    names = [c[0] for c in calls]
    assert names.index("will_set") < names.index("connect")
    will = next(c for c in calls if c[0] == "will_set")
    assert will[1] == will_topic
    assert will[2] == will_payload
    assert will[3] == MQTT_QOS
    assert will[4] is True


def test_paho_bus_uses_unique_client_id_by_default(monkeypatch):
    """SWD-138: default client_id must not be a fixed plcassistant-app."""
    from plcassistant.io import mqtt_paho as paho_mod

    seen: list[str] = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            cid = kwargs.get("client_id")
            if cid is None and args:
                cid = args[0]
            seen.append(str(cid))

        def username_pw_set(self, *args, **kwargs):
            return None

        def will_set(self, *args, **kwargs):
            return None

        def connect(self, *args, **kwargs):
            return None

        def loop_start(self):
            return None

    assert paho_mod.mqtt is not None
    monkeypatch.setattr(paho_mod.mqtt, "Client", FakeClient)
    paho_mod.PahoMqttBus("core-mosquitto", 1883)
    paho_mod.PahoMqttBus("core-mosquitto", 1883)
    assert len(seen) == 2
    assert seen[0] != seen[1]
    assert seen[0].startswith("plcassistant-app-")
    assert seen[0] != "plcassistant-app"


def test_build_bus_documents_offline_lwt():
    """SWD-136/145: live paho bus must register retained offline LWT with scan_period_s."""
    import inspect

    from plcassistant.app import runtime as runtime_mod
    from plcassistant.io import mqtt_paho as paho_mod

    src = inspect.getsource(runtime_mod.build_bus_from_options)
    assert "will_topic" in src
    assert '"offline"' in src or "'offline'" in src
    assert "scan_period_s" in src
    sig = inspect.signature(paho_mod.PahoMqttBus.__init__)
    assert "will_topic" in sig.parameters
    assert "will_payload" in sig.parameters
    assert "will_set" in inspect.getsource(paho_mod.PahoMqttBus.__init__)
    bus_sig = inspect.signature(runtime_mod.build_bus_from_options)
    assert "period_s" in bus_sig.parameters


def test_build_bus_lwt_includes_scan_period(monkeypatch):
    """SWD-145 review-fix: offline LWT retains scan_period_s for observe."""
    import json

    from plcassistant.app.runtime import build_bus_from_options
    from plcassistant.io import mqtt_paho as paho_mod

    wills: list[bytes] = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def username_pw_set(self, *args, **kwargs):
            return None

        def will_set(self, topic, payload, qos=0, retain=False):
            wills.append(payload)

        def connect(self, *args, **kwargs):
            return None

        def loop_start(self):
            return None

    assert paho_mod.mqtt is not None
    monkeypatch.setattr(paho_mod.mqtt, "Client", FakeClient)
    bus = build_bus_from_options(
        {"mqtt_broker": "core-mosquitto"}, ha_runtime=True, period_s=0.05
    )
    assert bus is not None
    assert wills
    body = json.loads(wills[-1].decode("utf-8"))
    assert body["state"] == "offline"
    assert body["scan_period_s"] == 0.05


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
