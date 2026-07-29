"""Shared HA-config Soft-PLC bridge (SWD-139 / SWD-140)."""

from __future__ import annotations

from pathlib import Path

import pytest

from plcassistant.io.ha_config_bridge import (
    drain_cmd,
    read_runtime_snapshot,
    write_cmd,
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
        for tag in ("SP_LEVEL", "SP_FLOW", "LT_RES"):
            assert f'"{tag}"' in src
