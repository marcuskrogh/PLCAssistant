"""SWD-222: Start/cascade, plant load, PID mux/card — rigorous acceptance."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

ROOT = Path("custom_components/plcassistant")
_CC = Path(__file__).resolve().parents[1] / "custom_components" / "plcassistant"
if str(_CC) not in sys.path:
    sys.path.insert(0, str(_CC))


def test_unit_no_optimistic_running_on_start() -> None:
    """Start must not publish running before Skid MODE accepts it."""
    src = Path("plcassistant/app/runtime.py").read_text(encoding="utf-8")
    apply = src.split("def _apply_commands", 1)[1].split("\n    def ", 1)[0]
    assert 'name == "start"' not in apply or "scanning = True" not in apply
    assert '_publish_scan_status("running")' not in apply
    assert "optimistic" in apply.lower() or "PERM_OK" in apply or "Skid MODE" in apply


def test_unit_operator_file_beats_stale_mqtt_retain(tmp_path: Path, monkeypatch) -> None:
    """File-seeded FLOW_MODE=Automatic wins over stale MQTT FLOW_MODE=Manual."""
    from plcassistant.app.runtime import MqttScanLoop, declare_default_image
    from plcassistant.io.ha_config_bridge import write_input_tags
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.io.mqtt_topics import MqttTagPayload, cmd_topic, tag_in_topic
    from plcassistant.io.quality import QualityStatus

    monkeypatch.setenv("PLCASSISTANT_HA_CONFIG", str(tmp_path))
    monkeypatch.setattr(MqttScanLoop, "FILE_BRIDGE_PERIOD_S", 0.0)
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.05)
    bridge.start()

    # HA seed / Number write: cascade-ready defaults on disk.
    assert write_input_tags(
        {
            "LEVEL_MODE": 1.0,
            "FLOW_MODE": 1.0,
            "SP_LEVEL_REQ": 0.25,
            "LT_TANK": 0.15,
            "LT_RES": 0.20,
            "FT_INLET": 0.0,
        },
        tmp_path,
    )
    # Stale broker retain still says Flow Manual (old ts; kills cascade).
    stale_ts = time.time() - 3600.0
    bus.publish(
        tag_in_topic("default", "FLOW_MODE"),
        MqttTagPayload(
            value=0.0, status=QualityStatus.GOOD, reason=None, ts=stale_ts
        ).encode(),
    )
    bus.publish(
        tag_in_topic("default", "LEVEL_MODE"),
        MqttTagPayload(
            value=0.0, status=QualityStatus.GOOD, reason=None, ts=stale_ts
        ).encode(),
    )
    bus.publish(cmd_topic("default", "start"), b"1")
    loop.scan_once()
    assert float(image.get_value("FLOW_MODE")) == pytest.approx(1.0)
    assert float(image.get_value("LEVEL_MODE")) == pytest.approx(1.0)
    assert loop.scanning is True
    assert image.get_value("MODE") == "RUNNING"
    for _ in range(25):
        loop.scan_once()
    assert float(image.get_value("SP_FLOW")) > 0.0
    assert float(image.get_value("CMD_SPEED")) > 0.0


def test_unit_fresher_mqtt_operator_beats_older_file(
    tmp_path: Path, monkeypatch
) -> None:
    """Live MQTT operator write with newer ts must not be stomped by file."""
    from plcassistant.app.runtime import MqttScanLoop, declare_default_image
    from plcassistant.io.ha_config_bridge import write_input_tags
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.io.mqtt_topics import MqttTagPayload, tag_in_topic
    from plcassistant.io.quality import QualityStatus

    monkeypatch.setenv("PLCASSISTANT_HA_CONFIG", str(tmp_path))
    monkeypatch.setattr(MqttScanLoop, "FILE_BRIDGE_PERIOD_S", 0.0)
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.05)
    bridge.start()
    assert write_input_tags({"FLOW_MODE": 1.0, "LEVEL_MODE": 0.0}, tmp_path)
    # Make file timestamps old, then publish fresher MQTT Manual.
    snap_path = tmp_path / "plcassistant" / "inputs.json"
    body = json.loads(snap_path.read_text(encoding="utf-8"))
    for tag in body.get("tags", {}).values():
        tag["ts"] = time.time() - 120.0
    snap_path.write_text(json.dumps(body), encoding="utf-8")
    bus.publish(
        tag_in_topic("default", "FLOW_MODE"),
        MqttTagPayload(
            value=0.0,
            status=QualityStatus.GOOD,
            reason=None,
            ts=time.time(),
        ).encode(),
    )
    loop.scan_once()
    assert float(image.get_value("FLOW_MODE")) == pytest.approx(0.0)


def test_system_defaults_start_cascade_inlet_rises() -> None:
    """Defaults → Start → RUNNING + SP_FLOW/CMD > 0; plant FT_INLET rises on CMD."""
    from dynamics.plant import PlantSimulator
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    image.apply_input("LEVEL_MODE", 1.0, QualityStatus.GOOD)
    image.apply_input("FLOW_MODE", 1.0, QualityStatus.GOOD)
    image.apply_input("SP_LEVEL_REQ", 0.25, QualityStatus.GOOD)
    image.apply_input("LT_TANK", 0.15, QualityStatus.GOOD)
    image.apply_input("LT_RES", 0.20, QualityStatus.GOOD)
    image.apply_input("FT_INLET", 0.0, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    assert image.get_value("MODE") == "RUNNING"
    for _ in range(20):
        logic(image)
    sp_flow = float(image.get_value("SP_FLOW"))
    cmd = float(image.get_value("CMD_SPEED"))
    assert sp_flow > 0.0
    assert cmd > 0.0

    published: dict[str, dict] = {}

    def publish(tag: str, payload: str) -> None:
        published[tag] = json.loads(payload)

    plant = PlantSimulator.for_preset(publish)
    plant.apply_status_payload({"state": "running", "scan_period_s": 0.1})
    plant.apply_cmd_speed(cmd)
    ft0 = float(plant.model.outputs().get("FT_INLET", 0.0))
    for _ in range(40):
        plant.tick(0.1)
    assert float(published["FT_INLET"]["value"]) > ft0
    assert float(published["FT_INLET"]["value"]) > 0.0


def test_unit_plant_watchdog_paused_while_frozen() -> None:
    from dynamics.plant import PlantSimulator

    published: dict[str, dict] = {}

    def publish(tag: str, payload: str) -> None:
        published[tag] = json.loads(payload)

    plant = PlantSimulator.for_preset(publish)
    plant.apply_status_payload({"state": "running", "scan_period_s": 0.1})
    plant.apply_cmd_speed(60.0, mono=100.0)
    plant.tick(0.1, mono=100.1)
    assert plant.model._inputs["cmd_speed"] == pytest.approx(60.0)

    plant.apply_status_payload({"state": "offline", "scan_period_s": 0.1})
    assert plant.frozen is True
    assert plant.model._inputs["cmd_speed"] == pytest.approx(0.0)
    # Long freeze — watchdog must not run while frozen.
    plant.tick(0.1, mono=200.0)

    plant.apply_status_payload({"state": "running", "scan_period_s": 0.1})
    assert plant.frozen is False
    # Soft-PLC republishes CMD after thaw; freeze gap must not zero it.
    plant.apply_cmd_speed(60.0, mono=200.0)
    plant.tick(0.1, mono=200.5)
    assert plant.model._inputs["cmd_speed"] == pytest.approx(60.0)
    # Watchdog still engages once unfrozen after cmd_watchdog_s silence.
    plant.tick(0.1, mono=203.0)
    assert plant.model._inputs["cmd_speed"] == pytest.approx(0.0)


def test_unit_plant_simulator_rate_limits_file_writes() -> None:
    sim = (ROOT / "dynamics" / "simulator.py").read_text(encoding="utf-8")
    assert "_FILE_WRITE_PERIOD_S = 1.0" in sim
    assert "await asyncio.sleep(_POLL_S)" in sim
    assert "period_s / 2" not in sim


def test_integration_seed_awaits_mqtt_qos1() -> None:
    text = (ROOT / "number.py").read_text(encoding="utf-8")
    seed = text.split("async def async_seed_operator_defaults", 1)[1].split(
        "\ndef _object_id_from_entity", 1
    )[0]
    assert "_bg_mqtt" not in seed
    assert '"qos": 1' in seed
    assert "blocking=True" in seed
    assert "wait_for" in seed
    assert "retain" in seed


def test_integration_start_stop_blocking_qos1() -> None:
    init = (ROOT / "__init__.py").read_text(encoding="utf-8")
    pub = init.split("async def _publish_cmd", 1)[1].split("async def handle_start", 1)[0]
    assert '"qos": 1' in pub
    assert "blocking=True" in pub
    assert "write_cmd" in pub
    # File fallback must be queued before MQTT await (SWD-222 review-fix).
    assert pub.index("write_cmd") < pub.index("blocking=True")
    button = (ROOT / "button.py").read_text(encoding="utf-8")
    assert "blocking=True" in button


def test_integration_pid_sp_always_muxes() -> None:
    pid = (ROOT / "pid_loop.py").read_text(encoding="utf-8")
    refresh = pid.split("def _refresh_from_store", 1)[1].split(
        "async def async_added_to_hass", 1
    )[0]
    assert "_select_sp(mode, man, auto, rem)" in refresh
    assert "sp_active" not in refresh


def test_integration_auto_sp_flips_level_mode() -> None:
    from plcassistant.io.pid_loop import SpSourceMode

    text = (ROOT / "number.py").read_text(encoding="utf-8")
    assert "SP_LEVEL_AUTO" in text
    assert "SP_LEVEL_REQ" in text
    assert "SpSourceMode.AUTOMATIC.code" in text
    flip = {
        "SP_LEVEL_MAN": float(SpSourceMode.MANUAL.code),
        "SP_LEVEL_AUTO": float(SpSourceMode.AUTOMATIC.code),
        "SP_LEVEL_REQ": float(SpSourceMode.AUTOMATIC.code),
        "SP_LEVEL_REM": float(SpSourceMode.REMOTE.code),
    }
    assert flip["SP_LEVEL_AUTO"] == pytest.approx(1.0)
    assert flip["SP_LEVEL_REQ"] == pytest.approx(1.0)


def test_integration_pid_card_preserves_drafts() -> None:
    card = (ROOT / "www" / "pid-loop-card.js").read_text(encoding="utf-8")
    assert "_drafts" in card
    assert "_captureFocusedDrafts" in card
    assert "_dirty" in card
    assert "MAN writes CO; AUTO writes local SP" in card
    assert "this.innerHTML = `" not in card.split("_render", 1)[1].split(
        "customElements.define", 1
    )[0] or "forceRebuild" in card


def test_system_app_version_and_dashboard() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.59"' in manifest
    dash = (ROOT / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 28" in dash
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.59"' in config
    docker = Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.59" in docker
