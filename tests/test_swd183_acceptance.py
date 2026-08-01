"""SWD-183 acceptance: PID SP-source modes, faceplates, App online, Lovelace cards."""

from __future__ import annotations

import pytest

from pathlib import Path

from plcassistant.app.default_image import declare_default_image
from plcassistant.app.skid_scan import SkidImageLogic
from plcassistant.io.datablock import default_tank_datablock_catalog
from plcassistant.io.pid_loop import (
    DEMO_PID_LOOPS,
    FLOW_LOOP,
    LEVEL_LOOP,
    SpSourceMode,
    apply_sp_write,
    faceplate_from_image_tags,
    select_active_sp,
)
from plcassistant.app.operator_runtime import OperatorRuntime
from plcassistant.wedge.control import CascadeConfig


# --- unit -----------------------------------------------------------------


def test_unit_select_active_sp_modes() -> None:
    assert select_active_sp("manual", sp_man=0.1, sp_auto=0.2, sp_rem=0.3) == pytest.approx(0.1)
    assert select_active_sp(1, sp_man=0.1, sp_auto=0.2, sp_rem=0.3) == pytest.approx(0.2)
    assert select_active_sp(SpSourceMode.REMOTE, sp_man=0.1, sp_auto=0.2, sp_rem=0.3) == pytest.approx(
        0.3
    )


def test_unit_ha_parse_mode_aliases_match_sp_source_mode() -> None:
    """HA _parse_mode valid aliases must match Soft-PLC SpSourceMode.parse."""
    text = Path("custom_components/plcassistant/pid_loop.py").read_text(encoding="utf-8")
    assert "_parse_mode" in text
    assert "SpSourceMode.parse" in text or "fall back to manual" in text
    for alias, expected in (
        ("manual", SpSourceMode.MANUAL),
        ("man", SpSourceMode.MANUAL),
        ("0", SpSourceMode.MANUAL),
        (0, SpSourceMode.MANUAL),
        ("automatic", SpSourceMode.AUTOMATIC),
        ("auto", SpSourceMode.AUTOMATIC),
        ("1", SpSourceMode.AUTOMATIC),
        (1, SpSourceMode.AUTOMATIC),
        ("remote", SpSourceMode.REMOTE),
        ("rem", SpSourceMode.REMOTE),
        ("2", SpSourceMode.REMOTE),
        (2, SpSourceMode.REMOTE),
    ):
        assert SpSourceMode.parse(alias) is expected
        assert f'"{alias}"' in text or f"'{alias}'" in text or str(alias) in text


def test_unit_sp_mode_flip_map_publishes_level_mode() -> None:
    """Manual/Remote SP writes flip LEVEL_MODE / FLOW_MODE via SpSourceMode codes."""
    text = Path("custom_components/plcassistant/number.py").read_text(encoding="utf-8")
    assert "_sp_mode_flip_map" in text
    assert "SpSourceMode.MANUAL.code" in text
    flip = {
        "SP_LEVEL_MAN": ("LEVEL_MODE", float(SpSourceMode.MANUAL.code)),
        "SP_LEVEL_REM": ("LEVEL_MODE", float(SpSourceMode.REMOTE.code)),
        "SP_FLOW_MAN": ("FLOW_MODE", float(SpSourceMode.MANUAL.code)),
        "SP_FLOW_REM": ("FLOW_MODE", float(SpSourceMode.REMOTE.code)),
    }
    assert flip["SP_LEVEL_MAN"] == ("LEVEL_MODE", 0.0)
    assert flip["SP_LEVEL_REM"] == ("LEVEL_MODE", 2.0)
    for tag in flip:
        assert tag in text


def test_unit_apply_sp_write_flip_rules() -> None:
    man = apply_sp_write(
        source="manual",
        value=0.25,
        current_mode="automatic",
        sp_man=0.2,
        sp_auto=0.2,
        sp_rem=0.2,
    )
    assert man["mode"] == "manual"
    assert man["sp"] == pytest.approx(0.25)
    assert man["sp_man"] == pytest.approx(0.25)

    rem = apply_sp_write(
        source="remote",
        value=0.35,
        current_mode="automatic",
        sp_man=0.2,
        sp_auto=0.2,
        sp_rem=0.2,
    )
    assert rem["mode"] == "remote"
    assert rem["sp"] == pytest.approx(0.35)

    auto = apply_sp_write(
        source="automatic",
        value=0.22,
        current_mode="manual",
        sp_man=0.25,
        sp_auto=0.2,
        sp_rem=0.2,
    )
    assert auto["mode"] == "manual"  # AUTO write does not flip
    assert auto["sp_auto"] == pytest.approx(0.22)
    assert auto["sp"] == pytest.approx(0.25)


# --- integration ----------------------------------------------------------


def test_integration_datablock_has_mode_tags() -> None:
    block = default_tank_datablock_catalog().get("DB_Tank")
    assert block is not None
    for tag in (
        "SP_LEVEL_MAN",
        "SP_LEVEL_AUTO",
        "SP_LEVEL_REM",
        "LEVEL_MODE",
        "SP_FLOW_MAN",
        "SP_FLOW_AUTO",
        "SP_FLOW_REM",
        "FLOW_MODE",
        "LEVEL_KP",
        "LEVEL_KI",
        "LEVEL_KD",
        "FLOW_KP",
        "FLOW_KI",
        "FLOW_KD",
    ):
        assert tag in block.tags
    tags = {b.tag for b in block.bindings}
    assert "LEVEL_MODE" in tags
    assert "FLOW_MODE" in tags
    assert "SP_FLOW_AUTO" in tags
    assert "LEVEL_KD" in tags
    assert "FLOW_KD" in tags
    assert len(block.bindings) == 24


def test_integration_softplc_ha_pid_loop_tag_parity() -> None:
    """Soft-PLC DEMO_PID_LOOPS tag names must match HA compound sensor map."""
    text = Path("custom_components/plcassistant/pid_loop.py").read_text(encoding="utf-8")
    for loop in DEMO_PID_LOOPS:
        assert f'"loop_id": "{loop.loop_id}"' in text
        for field in ("pv", "sp", "sp_man", "sp_auto", "sp_rem", "mode", "cv", "kp", "ki", "kd"):
            assert f'"{field}": "{getattr(loop, field)}"' in text


def test_integration_compound_entity_attribute_schema_keys() -> None:
    """Compound PID sensor attrs include faceplate keys from DEMO_PID_LOOPS."""
    text = Path("custom_components/plcassistant/pid_loop.py").read_text(encoding="utf-8")
    fp = faceplate_from_image_tags(LEVEL_LOOP, {})
    for key in ("loop_id", "mode", "pv", "sp", "sp_man", "sp_auto", "sp_rem", "cv", "kp", "ki", "kd"):
        assert f'"{key}"' in text
    for entity_key in (
        "pv_entity",
        "sp_entity",
        "sp_man_entity",
        "sp_auto_entity",
        "sp_rem_entity",
        "mode_entity",
        "cv_entity",
        "kp_entity",
        "ki_entity",
    ):
        assert entity_key in text


def test_integration_file_input_tags_include_operator_pid_in() -> None:
    from plcassistant.app.runtime import MqttScanLoop

    tags = MqttScanLoop._FILE_INPUT_TAGS
    for tag in (
        "SP_LEVEL_REQ",
        "LEVEL_MODE",
        "FLOW_MODE",
        "SP_LEVEL_MAN",
        "LEVEL_KP",
        "LEVEL_KD",
        "FLOW_KD",
        "LT_TANK",
    ):
        assert tag in tags


def test_integration_faceplate_from_image_tags() -> None:
    values = {
        "LT_TANK": 0.18,
        "SP_LEVEL_MAN": 0.10,
        "SP_LEVEL_AUTO": 0.20,
        "SP_LEVEL_REM": 0.30,
        "LEVEL_MODE": 0,
        "SP_FLOW": 1.5,
        "LEVEL_KP": 8.0,
        "LEVEL_KI": 0.4,
        "LEVEL_KD": 0.0,
    }
    fp = faceplate_from_image_tags(LEVEL_LOOP, values)
    assert fp["mode"] == "manual"
    assert fp["sp"] == pytest.approx(0.10)
    assert fp["pv"] == pytest.approx(0.18)
    assert fp["loop_id"] == "level"


# --- system ---------------------------------------------------------------


def test_system_req_wins_automatic_after_auto_has_last_good() -> None:
    """REQ remains Automatic writer even when SP_LEVEL_AUTO has last_good."""
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.apply_input("SP_LEVEL_REQ", 0.28, QualityStatus.GOOD)
    image.apply_input("SP_LEVEL_AUTO", 0.12, QualityStatus.GOOD)
    image.apply_input("LEVEL_MODE", 1.0, QualityStatus.GOOD)
    image.apply_input("LT_TANK", 0.15, QualityStatus.GOOD)
    image.apply_input("LT_RES", 0.20, QualityStatus.GOOD)
    image.apply_input("FT_INLET", 0.0, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    assert float(image.get_value("SP_LEVEL")) == pytest.approx(0.28, abs=0.02)


def test_system_skid_scan_manual_uses_sp_level_man() -> None:
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    for tag, val in (
        ("LEVEL_MODE", 0.0),
        ("SP_LEVEL_MAN", 0.31),
        ("SP_LEVEL_AUTO", 0.20),
        ("SP_LEVEL_REQ", 0.20),
        ("LT_TANK", 0.15),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    assert float(image.get_value("SP_LEVEL")) == pytest.approx(0.31, abs=0.02)


def test_system_flow_man_publishes_sp_flow_override() -> None:
    """Flow MAN mode publishes muxed SP_FLOW (CMD_SPEED still cascade PI this scan)."""
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    for tag, val in (
        ("LEVEL_MODE", 1.0),
        ("FLOW_MODE", 0.0),
        ("SP_LEVEL_REQ", 0.20),
        ("SP_FLOW_MAN", 4.5),
        ("LT_TANK", 0.15),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    assert float(image.get_value("SP_FLOW")) == pytest.approx(4.5, abs=0.01)


def test_system_tunings_applied_into_skid_cascade() -> None:
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    defaults = CascadeConfig()
    image.apply_input("LEVEL_KP", 55.0, QualityStatus.GOOD)
    image.apply_input("FLOW_KI", 3.5, QualityStatus.GOOD)
    image.apply_input("LT_TANK", 0.15, QualityStatus.GOOD)
    image.apply_input("LT_RES", 0.20, QualityStatus.GOOD)
    image.apply_input("FT_INLET", 0.0, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic(image)
    cascade = logic.skid.config.cascade
    assert cascade.level_kp == pytest.approx(55.0)
    assert cascade.level_ki == pytest.approx(defaults.level_ki)
    assert cascade.flow_ki == pytest.approx(3.5)


def test_system_runtime_snapshot_has_tags() -> None:
    snap = OperatorRuntime().snapshot()
    assert "tags" in snap
    assert "LT_TANK" in snap["tags"]
    assert "LEVEL_MODE" in snap["tags"] or "SP_LEVEL_REQ" in snap["tags"]
    assert snap["status"] in ("offline", "stopped", "running", "fault")


def test_system_canvas_polls_runtime() -> None:
    html = Path("plcassistant/app/_canvas.py").read_text(encoding="utf-8")
    assert "api/runtime" in html
    assert "api/schedule/status" in html
    assert "online-strip" in html
    assert "pollOnline" in html
    assert "live-watch" in html
    assert "saved_signature" in html or "progCount" in html


def test_system_lovelace_operate_has_block_list_card() -> None:
    text = Path("custom_components/plcassistant/lovelace/plcassistant.yaml").read_text(
        encoding="utf-8"
    )
    assert "plcassistant_dashboard_version: 19" in text
    assert "custom:plcassistant-block-list-card" in text


def test_system_pid_card_js_exists() -> None:
    pid = Path("custom_components/plcassistant/www/pid-loop-card.js")
    block = Path("custom_components/plcassistant/www/block-list-card.js")
    assert pid.is_file()
    assert block.is_file()
    text = pid.read_text(encoding="utf-8")
    assert "plcassistant-pid-card" in text
    assert "customCards" in text
    assert "plcassistant-block-list-card" in block.read_text(encoding="utf-8")
    assert FLOW_LOOP.mode == "FLOW_MODE"
