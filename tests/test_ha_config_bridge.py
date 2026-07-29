"""Shared HA-config Soft-PLC bridge (SWD-139)."""

from __future__ import annotations

from pathlib import Path

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
    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.05)
    bridge.start()
    assert write_cmd("start", root=tmp_path)
    loop.scan_once()
    assert loop.scanning is True
    snap = read_runtime_snapshot(root=tmp_path)
    assert snap is not None
    assert snap["status"] == "running"
