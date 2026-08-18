"""SWD-229: Lovelace Operate SCADA-style declutter (not every entity)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path("custom_components/plcassistant")
DASH = ROOT / "lovelace" / "plcassistant.yaml"
DASH_PY = ROOT / "lovelace_dashboard.py"
RUN = Path("plc_assistant/run.sh")


def _operate_yaml() -> str:
    text = DASH.read_text(encoding="utf-8")
    # Truncate at Dynamics tab so Operate-only assertions stay scoped.
    marker = "\n  - title: Dynamics\n"
    assert marker in text
    return text.split(marker, 1)[0]


def test_unit_operate_is_scada_not_entity_dump() -> None:
    operate = _operate_yaml()
    assert "plcassistant_dashboard_version: 28" in operate
    assert "sensor.plcassistant_status" in operate
    assert "sensor.plcassistant_mode" in operate
    assert "sensor.plcassistant_trip_active" in operate
    assert "button.plcassistant_start" in operate
    assert "button.plcassistant_stop" in operate
    assert "button.plcassistant_reset" in operate
    assert "type: glance" in operate
    assert "sensor.plcassistant_lt_tank_in" in operate
    assert "sensor.plcassistant_lt_res_in" in operate
    assert "sensor.plcassistant_ft_inlet_in" in operate
    assert "sensor.plcassistant_cmd_speed" in operate
    assert "custom:plcassistant-pid-card" in operate
    assert "sensor.plcassistant_pid_level" in operate
    assert "sensor.plcassistant_pid_flow" in operate


def test_unit_operate_omits_clutter() -> None:
    operate = _operate_yaml()
    assert "type: markdown" not in operate
    assert "custom:plcassistant-block-list-card" not in operate
    assert "type: history-graph" not in operate
    assert "PID loops (fallback" not in operate
    assert "Active setpoints" not in operate
    assert "Level SP Man" not in operate
    assert "0.1.48+" not in operate
    # Dynamics preset belongs on Dynamics tab / options — not Operate SCADA.
    assert "sensor.plcassistant_dynamics_preset" not in operate
    assert "number.plcassistant_sp_level_req" not in operate
    assert "sensor.plcassistant_perm_ok" not in operate


def test_system_engineering_tabs_retained() -> None:
    text = DASH.read_text(encoding="utf-8")
    assert "path: dynamics" in text
    assert "/api/plcassistant/dynamics/ui" in text
    assert "path: datablocks" in text
    assert "/api/plcassistant/datablocks/ui" in text


def test_system_app_version_tracks_current() -> None:
    assert '"0.1.62"' in (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert 'version: "0.1.62"' in Path("plc_assistant/config.yaml").read_text(
        encoding="utf-8"
    )
    assert "BUILD_VERSION=0.1.62" in Path("plc_assistant/Dockerfile").read_text(
        encoding="utf-8"
    )
    dual = Path("plc_assistant/custom_components/plcassistant")
    assert '"0.1.62"' in (dual / "manifest.json").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 28" in (
        dual / "lovelace" / "plcassistant.yaml"
    ).read_text(encoding="utf-8")


def test_system_dashboard_upgrade_includes_27() -> None:
    dash_py = DASH_PY.read_text(encoding="utf-8")
    assert "2[0-7]" in dash_py
    run = RUN.read_text(encoding="utf-8")
    assert "2[0-7]" in run
    assert "1–27" in run or "1-27" in run or "1–27" in dash_py


def test_system_dual_trees_synced() -> None:
    a = DASH.read_text(encoding="utf-8")
    b = Path(
        "plc_assistant/custom_components/plcassistant/lovelace/plcassistant.yaml"
    ).read_text(encoding="utf-8")
    assert a == b
    ra = (ROOT / "lovelace" / "README.md").read_text(encoding="utf-8")
    rb = Path(
        "plc_assistant/custom_components/plcassistant/lovelace/README.md"
    ).read_text(encoding="utf-8")
    assert ra == rb
    assert "SCADA" in ra or "scada" in ra.lower()
    assert "0.1.62" in ra
    dash_a = DASH_PY.read_text(encoding="utf-8")
    dash_b = Path(
        "plc_assistant/custom_components/plcassistant/lovelace_dashboard.py"
    ).read_text(encoding="utf-8")
    assert dash_a == dash_b
