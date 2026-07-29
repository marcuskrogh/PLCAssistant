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
        "LT_TANK",
        "LT_RES",
        "FT_INLET",
        "CMD_SPEED",
        "SP_LEVEL",
        "SP_FLOW",
    ):
        assert name in tags
        assert "value" in tags[name]
    # After Start, active level SP mirrors request; flow/reservoir should be live.
    assert float(tags["SP_LEVEL"]["value"]) == pytest.approx(0.20, abs=0.05)
    assert float(tags["SP_FLOW"]["value"]) > 0.0
    assert float(tags["LT_RES"]["value"]) > 0.0


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


def test_hmi_tags_list_includes_active_setpoints_and_reservoir() -> None:
    """SWD-140: integration poll list matches App runtime write set (both trees)."""
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
        for tag in ("SP_LEVEL", "SP_FLOW", "LT_RES"):
            assert f'"{tag}"' in src
    for src_path in runtime_paths:
        src = src_path.read_text(encoding="utf-8")
        assert "_write_ha_config_runtime" in src
        assert "_apply_file_inputs" in src
        for tag in ("SP_LEVEL", "SP_FLOW", "LT_RES"):
            assert f'"{tag}"' in src
