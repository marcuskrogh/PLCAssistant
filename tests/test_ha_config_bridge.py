"""Shared HA-config Soft-PLC bridge (SWD-139 / SWD-140 / SWD-141)."""

from __future__ import annotations

from pathlib import Path

import pytest

from plcassistant.io.ha_config_bridge import (
    drain_cmd,
    read_inputs,
    read_runtime_snapshot,
    write_cmd,
    write_input_tag,
    write_runtime_snapshot,
)


def test_runtime_roundtrip(tmp_path: Path) -> None:
    assert write_runtime_snapshot(
        {"status": "stopped", "scanning": False, "tags": {"MODE": {"value": "STOP"}}},
        root=tmp_path,
    )
    snap = read_runtime_snapshot(root=tmp_path)
    assert snap is not None
    assert snap["status"] == "stopped"
    assert snap["tags"]["MODE"]["value"] == "STOP"
    assert "ts" in snap


def test_cmd_drain_roundtrip(tmp_path: Path) -> None:
    assert write_cmd("start", root=tmp_path)
    assert drain_cmd(root=tmp_path) == "start"
    assert drain_cmd(root=tmp_path) is None


def test_cmd_rejects_unknown(tmp_path: Path) -> None:
    assert write_cmd("noop", root=tmp_path) is False
    assert not (tmp_path / "plcassistant" / "cmd.json").exists()


def test_input_tag_roundtrip(tmp_path: Path) -> None:
    assert write_input_tag("SP_LEVEL_REQ", 0.30, root=tmp_path)
    snap = read_inputs(root=tmp_path)
    assert snap is not None
    assert snap["tags"]["SP_LEVEL_REQ"]["value"] == pytest.approx(0.30)
    assert write_input_tag("SP_LEVEL_REQ", 0.25, root=tmp_path)
    snap2 = read_inputs(root=tmp_path)
    assert snap2["tags"]["SP_LEVEL_REQ"]["value"] == pytest.approx(0.25)


def test_write_input_tag_accepts_ha_executor_positional_args(tmp_path: Path) -> None:
    """SWD-141: HA async_add_executor_job passes status/reason/root positionally."""
    assert write_input_tag("SP_LEVEL_REQ", 0.30, "GOOD", None, tmp_path)
    # Dual-tree CC module must match (no keyword-only star after value).
    import importlib.util

    cc = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "plcassistant"
        / "ha_config_bridge.py"
    )
    spec = importlib.util.spec_from_file_location("cc_ha_config_bridge_pos", cc)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.write_input_tag("SP_LEVEL_REQ", 0.31, "GOOD", None, tmp_path)
    snap = mod.read_inputs(root=tmp_path)
    assert float(snap["tags"]["SP_LEVEL_REQ"]["value"]) == pytest.approx(0.31)


def test_scan_loop_drains_file_cmd_and_writes_runtime(tmp_path: Path, monkeypatch) -> None:
    from plcassistant.app.runtime import MqttScanLoop, declare_default_image
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge

    monkeypatch.setenv("PLCASSISTANT_HA_CONFIG", str(tmp_path))
    monkeypatch.setattr(MqttScanLoop, "FILE_BRIDGE_PERIOD_S", 0.0)
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.05)
    bridge.start()
    assert write_cmd("start", root=tmp_path)
    loop.scan_once()
    assert loop.scanning is True
    # Allow cascade a few scans; period=0 keeps runtime.json fresh each scan.
    for _ in range(5):
        loop.scan_once()
    snap = read_runtime_snapshot(root=tmp_path)
    assert snap is not None
    assert snap["status"] == "running"
    tags = snap["tags"]
    for name in (
        "MODE",
        "PERM_OK",
        "TRIP_ACTIVE",
        "CMD_SPEED",
        "SP_LEVEL",
        "SP_FLOW",
    ):
        assert name in tags
        assert "value" in tags[name]
    for plant in ("LT_TANK", "LT_RES", "FT_INLET"):
        assert plant not in tags
    # After Start, active level SP mirrors request; CVs live without plant motion.
    assert float(tags["SP_LEVEL"]["value"]) == pytest.approx(0.20, abs=0.05)
    assert float(tags["SP_FLOW"]["value"]) > 0.0
    assert snap.get("scan_period_s") == pytest.approx(0.05)


def test_file_sp_level_req_updates_active_level_sp(tmp_path: Path, monkeypatch) -> None:
    """SWD-141: MQTT-silent Level setpoint via inputs.json drives Active SP."""
    from plcassistant.app.runtime import MqttScanLoop, declare_default_image
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge

    monkeypatch.setenv("PLCASSISTANT_HA_CONFIG", str(tmp_path))
    monkeypatch.setattr(MqttScanLoop, "FILE_BRIDGE_PERIOD_S", 0.0)
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.05)
    bridge.start()
    assert write_input_tag("SP_LEVEL_REQ", 0.30, root=tmp_path)
    assert write_cmd("start", root=tmp_path)
    loop.scan_once()
    assert loop.scanning is True
    for _ in range(5):
        loop.scan_once()
    assert float(image.get_value("SP_LEVEL_REQ")) == pytest.approx(0.30)
    assert float(image.get_value("SP_LEVEL")) == pytest.approx(0.30)
    snap = read_runtime_snapshot(root=tmp_path)
    assert snap is not None
    assert float(snap["tags"]["SP_LEVEL"]["value"]) == pytest.approx(0.30)


def test_hmi_tags_list_excludes_plant_includes_active_setpoints() -> None:
    """SWD-145: Soft-PLC OUT HMI set excludes plant PVs; keeps active setpoints."""
    root = Path(__file__).resolve().parents[1]
    init_paths = [
        root / "custom_components" / "plcassistant" / "__init__.py",
        root / "plc_assistant" / "custom_components" / "plcassistant" / "__init__.py",
    ]
    runtime_paths = [
        root / "plcassistant" / "app" / "runtime.py",
        root / "plc_assistant" / "plcassistant" / "app" / "runtime.py",
    ]
    for src_path in init_paths:
        src = src_path.read_text(encoding="utf-8")
        assert "_HMI_TAGS" in src
        for tag in ("SP_LEVEL", "SP_FLOW"):
            assert f'"{tag}"' in src
        for plant in ("LT_TANK", "LT_RES", "FT_INLET"):
            # Present in bindings as IN, but not in _HMI_TAGS OUT poll list.
            assert f'"{plant}"' in src
        # Extract _HMI_TAGS tuple contents roughly
        start = src.index("_HMI_TAGS")
        chunk = src[start : start + 250]
        assert "SP_LEVEL" in chunk
        assert "LT_TANK" not in chunk
    for src_path in runtime_paths:
        src = src_path.read_text(encoding="utf-8")
        assert "_write_ha_config_runtime" in src
        assert "_apply_file_inputs" in src
        assert "_FILE_INPUT_TAGS" in src
        for tag in ("SP_LEVEL", "SP_FLOW"):
            assert f'"{tag}"' in src
        # Soft-PLC OUT snapshot must not republish plant PVs as OUT.
        write_start = src.index("def _write_ha_config_runtime")
        write_end = src.index("\n    def ", write_start + 1)
        write_fn = src[write_start:write_end]
        for plant in ("LT_TANK", "LT_RES", "FT_INLET"):
            assert f'"{plant}"' not in write_fn
        # SWD-171: plant IN is allowed on the file-input fallback path.
        file_inputs = src[src.index("_FILE_INPUT_TAGS") : src.index("def _apply_file_inputs")]
        for plant in ("LT_TANK", "LT_RES", "FT_INLET"):
            assert f'"{plant}"' in file_inputs
        assert '"SP_LEVEL_REQ"' in file_inputs


def test_file_plant_inputs_drive_soft_plc_when_mqtt_silent(
    tmp_path: Path, monkeypatch
) -> None:
    """SWD-171: inputs.json plant tags feed Soft-PLC when MQTT plant IN is silent."""
    from plcassistant.app.runtime import MqttScanLoop, declare_default_image
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.io.quality import QualityStatus

    monkeypatch.setenv("PLCASSISTANT_HA_CONFIG", str(tmp_path))
    monkeypatch.setattr(MqttScanLoop, "FILE_BRIDGE_PERIOD_S", 0.0)
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.05)
    bridge.start()
    assert write_input_tag("LT_TANK", 0.33, root=tmp_path)
    assert write_input_tag("LT_RES", 0.18, root=tmp_path)
    assert write_input_tag("FT_INLET", 2.5, root=tmp_path)
    assert write_input_tag("SP_LEVEL_REQ", 0.30, root=tmp_path)
    loop._apply_file_inputs()
    assert float(image.get_value("SP_LEVEL_REQ")) == pytest.approx(0.30)
    assert float(image.get_value("LT_TANK")) == pytest.approx(0.33)
    assert float(image.get_value("LT_RES")) == pytest.approx(0.18)
    assert float(image.get_value("FT_INLET")) == pytest.approx(2.5)
    assert image.get_quality("LT_TANK").status is QualityStatus.GOOD


def test_mqtt_plant_in_wins_over_file_on_same_scan(
    tmp_path: Path, monkeypatch
) -> None:
    """SWD-171: live MQTT plant IN overrides file hydrate on the same scan."""
    from plcassistant.app.runtime import MqttScanLoop, declare_default_image
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
    assert write_input_tag("LT_TANK", 0.10, root=tmp_path)
    bus.publish(
        tag_in_topic("default", "LT_TANK"),
        MqttTagPayload.now(0.28).encode(),
    )
    loop.scan_once()
    assert float(image.get_value("LT_TANK")) == pytest.approx(0.28)
    assert image.get_quality("LT_TANK").status is QualityStatus.GOOD


def test_write_input_tags_batch_merges(tmp_path: Path) -> None:
    from plcassistant.io.ha_config_bridge import write_input_tags

    assert write_input_tag("SP_LEVEL_REQ", 0.20, root=tmp_path)
    assert write_input_tags(
        {
            "LT_TANK": {"value": 0.25, "status": "GOOD", "reason": None},
            "LT_RES": 0.15,
            "FT_INLET": {"value": 1.2, "status": "GOOD"},
        },
        root=tmp_path,
    )
    snap = read_inputs(root=tmp_path)
    assert snap is not None
    assert float(snap["tags"]["SP_LEVEL_REQ"]["value"]) == pytest.approx(0.20)
    assert float(snap["tags"]["LT_TANK"]["value"]) == pytest.approx(0.25)
    assert float(snap["tags"]["LT_RES"]["value"]) == pytest.approx(0.15)
    assert float(snap["tags"]["FT_INLET"]["value"]) == pytest.approx(1.2)
    assert "ts" in snap["tags"]["LT_TANK"]


def test_file_plant_malformed_value_demotes_bad(
    tmp_path: Path, monkeypatch
) -> None:
    """SWD-171 review: non-numeric GOOD plant values must not crash the scan."""
    from plcassistant.app.runtime import MqttScanLoop, declare_default_image
    from plcassistant.io.ha_config_bridge import write_input_tags
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.io.quality import QualityStatus, ReasonCode

    monkeypatch.setenv("PLCASSISTANT_HA_CONFIG", str(tmp_path))
    monkeypatch.setattr(MqttScanLoop, "FILE_BRIDGE_PERIOD_S", 0.0)
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.05)
    bridge.start()
    assert write_input_tags(
        {"LT_TANK": {"value": "not-a-number", "status": "GOOD"}},
        root=tmp_path,
    )
    loop.scan_once()  # must not raise
    assert image.get_quality("LT_TANK").status is QualityStatus.BAD
    assert image.get_quality("LT_TANK").reason is ReasonCode.FAULT


def test_file_plant_stale_holds_last_good_no_los(
    tmp_path: Path, monkeypatch
) -> None:
    """SWD-173: stale plant file skips apply (hold last good) — no LOS latch."""
    import time

    from plcassistant.app.runtime import MqttScanLoop, declare_default_image
    from plcassistant.io.ha_config_bridge import PLANT_FILE_STALE_S, write_cmd, write_input_tags
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.io.quality import QualityStatus
    from plcassistant.wedge.safety import Mode

    monkeypatch.setenv("PLCASSISTANT_HA_CONFIG", str(tmp_path))
    monkeypatch.setattr(MqttScanLoop, "FILE_BRIDGE_PERIOD_S", 0.0)
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.05)
    bridge.start()
    assert write_input_tags(
        {
            "LT_TANK": 0.22,
            "LT_RES": 0.18,
            "FT_INLET": 1.0,
            "SP_LEVEL_REQ": 0.25,
        },
        root=tmp_path,
    )
    assert write_cmd("start", root=tmp_path)
    for _ in range(5):
        loop.scan_once()
    assert loop.logic.skid.last.mode is Mode.RUNNING
    assert loop.logic.skid.last.trip_active is False

    stale_ts = time.time() - (PLANT_FILE_STALE_S + 2.0)
    assert write_input_tags(
        {
            "LT_TANK": {"value": 0.99, "status": "GOOD", "ts": stale_ts},
            "LT_RES": {"value": 0.01, "status": "GOOD", "ts": stale_ts},
            "FT_INLET": {"value": 9.0, "status": "GOOD", "ts": stale_ts},
            "SP_LEVEL_REQ": {"value": 0.30, "status": "GOOD", "ts": stale_ts},
        },
        root=tmp_path,
    )
    for _ in range(5):
        loop.scan_once()
    snap = loop.logic.skid.last
    assert snap.trip_active is False
    assert snap.mode is Mode.RUNNING
    # Stale plant values were skipped — last good retained.
    assert float(image.get_value("LT_TANK")) == pytest.approx(0.22)
    assert image.get_quality("LT_TANK").status is QualityStatus.GOOD
    # Operator SP still applies (not subject to plant stale skip).
    assert float(image.get_value("SP_LEVEL_REQ")) == pytest.approx(0.30)


def test_settled_plant_file_age_does_not_block_reset(
    tmp_path: Path, monkeypatch
) -> None:
    """SWD-173 regression: after settle + aged file, Reset/Start still work."""
    import time

    from plcassistant.app.runtime import MqttScanLoop, declare_default_image
    from plcassistant.io.ha_config_bridge import PLANT_FILE_STALE_S, write_cmd, write_input_tags
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.wedge.safety import Mode

    monkeypatch.setenv("PLCASSISTANT_HA_CONFIG", str(tmp_path))
    monkeypatch.setattr(MqttScanLoop, "FILE_BRIDGE_PERIOD_S", 0.0)
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.05)
    bridge.start()
    assert write_input_tags(
        {
            "LT_TANK": 0.15,
            "LT_RES": 0.20,
            "FT_INLET": 0.0,
            "SP_LEVEL_REQ": 0.25,
        },
        root=tmp_path,
    )
    assert write_cmd("start", root=tmp_path)
    for _ in range(5):
        loop.scan_once()
    assert loop.logic.skid.last.mode is Mode.RUNNING

    stale_ts = time.time() - (PLANT_FILE_STALE_S + 2.0)
    assert write_input_tags(
        {
            "LT_TANK": {"value": 0.15, "status": "GOOD", "ts": stale_ts},
            "LT_RES": {"value": 0.20, "status": "GOOD", "ts": stale_ts},
            "FT_INLET": {"value": 0.0, "status": "GOOD", "ts": stale_ts},
        },
        root=tmp_path,
    )
    for _ in range(3):
        loop.scan_once()
    assert loop.logic.skid.last.trip_active is False

    assert write_cmd("stop", root=tmp_path)
    loop.scan_once()
    assert write_cmd("reset", root=tmp_path)
    loop.scan_once()
    assert loop.logic.skid.last.mode is Mode.STOP
    assert loop.logic.skid.last.trip_active is False
    assert write_cmd("start", root=tmp_path)
    loop.scan_once()
    assert loop.logic.skid.last.mode is Mode.RUNNING



def test_concurrent_input_tag_merges_preserve_both(tmp_path: Path) -> None:
    """SWD-171 review: locked merge keeps plant + SP_LEVEL_REQ writes."""
    import threading

    from plcassistant.io.ha_config_bridge import write_input_tag, write_input_tags

    errors: list[BaseException] = []

    def plant_writer() -> None:
        try:
            for i in range(40):
                write_input_tags(
                    {
                        "LT_TANK": 0.10 + i * 0.001,
                        "LT_RES": 0.20,
                        "FT_INLET": 1.0,
                    },
                    root=tmp_path,
                )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    def sp_writer() -> None:
        try:
            for i in range(40):
                write_input_tag("SP_LEVEL_REQ", 0.20 + i * 0.001, root=tmp_path)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    t1 = threading.Thread(target=plant_writer)
    t2 = threading.Thread(target=sp_writer)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert not errors
    snap = read_inputs(root=tmp_path)
    assert snap is not None
    tags = snap["tags"]
    assert "SP_LEVEL_REQ" in tags
    assert "LT_TANK" in tags
    assert "LT_RES" in tags
    assert "FT_INLET" in tags

