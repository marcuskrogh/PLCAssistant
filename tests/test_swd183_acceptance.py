"""SWD-183 acceptance: PID SP-source modes, faceplates, App online, Lovelace cards."""

from __future__ import annotations

from pathlib import Path

import pytest

from plcassistant.app.default_image import declare_default_image
from plcassistant.app.skid_scan import SkidImageLogic
from plcassistant.io.datablock import default_tank_datablock_catalog
from plcassistant.io.pid_loop import (
    FLOW_LOOP,
    LEVEL_LOOP,
    SpSourceMode,
    apply_sp_write,
    faceplate_from_image_tags,
    select_active_sp,
)
from plcassistant.app.operator_runtime import OperatorRuntime


# --- unit -----------------------------------------------------------------


def test_unit_select_active_sp_modes() -> None:
    assert select_active_sp("manual", sp_man=0.1, sp_auto=0.2, sp_rem=0.3) == pytest.approx(0.1)
    assert select_active_sp(1, sp_man=0.1, sp_auto=0.2, sp_rem=0.3) == pytest.approx(0.2)
    assert select_active_sp(SpSourceMode.REMOTE, sp_man=0.1, sp_auto=0.2, sp_rem=0.3) == pytest.approx(
        0.3
    )


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
        "FLOW_KP",
        "FLOW_KI",
    ):
        assert tag in block.tags
    tags = {b.tag for b in block.bindings}
    assert "LEVEL_MODE" in tags
    assert "FLOW_MODE" in tags
    assert "SP_FLOW_AUTO" in tags


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
