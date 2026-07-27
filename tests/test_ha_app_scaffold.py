"""HA App scaffold layout (SWD-123 / A3)."""

from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "plc_assistant"


def test_app_required_files_exist():
    for name in ("config.yaml", "Dockerfile", "run.sh", "README.md"):
        path = APP / name
        assert path.is_file(), f"missing {path}"


def test_config_ingress_and_port():
    data = yaml.safe_load((APP / "config.yaml").read_text(encoding="utf-8"))
    assert data["ingress"] is True
    assert data["ingress_port"] == 8099
    assert "8099/tcp" in data["ports"]
    assert data["slug"] == "plcassistant"
    maps = data.get("map") or []
    assert any(
        (isinstance(m, dict) and m.get("type") == "data")
        or m == "data:rw"
        or (isinstance(m, str) and m.startswith("data"))
        for m in maps
    )
    opts = data["options"]
    assert opts["mqtt_broker"] == "core-mosquitto"
    assert opts["instance_id"] == "default"


def test_run_sh_wires_ha_runtime():
    text = (APP / "run.sh").read_text(encoding="utf-8")
    assert "program.json" in text
    assert "plcassistant.app" in text
    assert "0.0.0.0" in text
    assert "--ha-runtime" in text or "PLCASSISTANT_HA_RUNTIME" in text
    assert "options.json" in text
