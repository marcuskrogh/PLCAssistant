"""SWD-381: SP ramping in backend, settings, and orange SP bar."""

from __future__ import annotations

from pathlib import Path

import pytest

from plcassistant.control.ramp import ramp_setpoint
from plcassistant.io.pid_loop import (
    FLOW_LOOP,
    LEVEL_LOOP,
    PID_FACEPLATE_PARAM_KEYS,
    PID_OPERATOR_PARAM_KEYS,
    all_operator_param_tag_names,
)
from plcassistant.wedge.control import CascadeConfig
from tests.pid_faceplate_chrome import ELEMENTS, faceplate_chrome_source

ROOT = Path("custom_components/plcassistant")


def test_unit_ramp_setpoint_instant_when_rate_or_dt_nonpositive() -> None:
    assert ramp_setpoint(0.20, 0.35, 0.0, 0.1) == 0.35
    assert ramp_setpoint(0.20, 0.35, 0.05, 0.0) == 0.35
    assert ramp_setpoint(0.20, 0.35, -1.0, 0.1) == 0.35


def test_unit_ramp_setpoint_clips_to_rate_and_snaps_inside_one_scan() -> None:
    assert ramp_setpoint(0.20, 0.35, 0.05, 0.1) == pytest.approx(0.205)
    assert ramp_setpoint(0.35, 0.20, 0.05, 0.1) == pytest.approx(0.345)
    assert ramp_setpoint(0.348, 0.35, 0.05, 0.1) == pytest.approx(0.35)


def test_unit_sp_ramp_is_faceplate_path_not_pid_equation_param() -> None:
    assert "sp_ramp_max" not in PID_OPERATOR_PARAM_KEYS
    assert "sp_ramp_max" in PID_FACEPLATE_PARAM_KEYS
    assert LEVEL_LOOP.sp_ramp_max == "LEVEL_SP_RAMP_MAX"
    assert FLOW_LOOP.sp_ramp_max == "FLOW_SP_RAMP_MAX"
    tags = all_operator_param_tag_names()
    assert "LEVEL_SP_RAMP_MAX" in tags
    assert "FLOW_SP_RAMP_MAX" in tags
    params = CascadeConfig(level_sp_ramp_max=0.05, flow_sp_ramp_max=1.0)
    assert "sp_ramp_max" not in params.instance_operator_params("level_pi")
    assert "sp_ramp_max" not in params.instance_operator_params("flow_pi")


def test_unit_level_sp_out_ramps_when_set_exceeds_rate() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    image.apply_input("LEVEL_MODE", 1.0, QualityStatus.GOOD)
    image.apply_input("FLOW_MODE", 1.0, QualityStatus.GOOD)
    image.apply_input("SP_LEVEL_REQ", 0.20, QualityStatus.GOOD)
    image.apply_input("LEVEL_SP_RAMP_MAX", 0.05, QualityStatus.GOOD)
    image.apply_input("LT_TANK", 0.15, QualityStatus.GOOD)
    image.apply_input("LT_RES", 0.20, QualityStatus.GOOD)
    image.apply_input("FT_INLET", 0.0, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic(image)
    assert float(image.get_value("SP_LEVEL")) == pytest.approx(0.20)
    image.apply_input("SP_LEVEL_REQ", 0.35, QualityStatus.GOOD)
    logic(image)
    assert float(image.get_value("SP_LEVEL")) == pytest.approx(0.205)
    logic(image)
    assert float(image.get_value("SP_LEVEL")) == pytest.approx(0.210)


def test_unit_zero_ramp_rate_stays_instant() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    image.apply_input("LEVEL_MODE", 1.0, QualityStatus.GOOD)
    image.apply_input("SP_LEVEL_REQ", 0.20, QualityStatus.GOOD)
    image.apply_input("LEVEL_SP_RAMP_MAX", 0.0, QualityStatus.GOOD)
    image.apply_input("LT_TANK", 0.15, QualityStatus.GOOD)
    image.apply_input("LT_RES", 0.20, QualityStatus.GOOD)
    image.apply_input("FT_INLET", 0.0, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic(image)
    image.apply_input("SP_LEVEL_REQ", 0.35, QualityStatus.GOOD)
    logic(image)
    assert float(image.get_value("SP_LEVEL")) == pytest.approx(0.35)


def test_unit_settings_has_ramp_pane_and_orange_sp_segment() -> None:
    chrome = faceplate_chrome_source()
    assert 'data-pane="ramp"' in chrome
    assert 'data-pane-panel="ramp"' in chrome
    assert 'data-tune="sp_ramp_max"' in chrome
    assert "data-sp-ramp" in chrome
    assert "--pid-ramp" in chrome
    assert "pid-vbar-ramp" in chrome
    js = ELEMENTS.read_text(encoding="utf-8")
    assert "export function rampSetpoint" in js
    assert "export function pidSpRampVisible" in js
    assert "SWD-381" not in js


def test_unit_ha_numbers_and_compound_sensor_wire_sp_ramp() -> None:
    number = (ROOT / "number.py").read_text(encoding="utf-8")
    catalog = (ROOT / "datablocks" / "catalog.py").read_text(encoding="utf-8")
    sensor = (ROOT / "pid_loop.py").read_text(encoding="utf-8")
    card = (ROOT / "www" / "pid-loop-card.js").read_text(encoding="utf-8")
    for tag in ("LEVEL_SP_RAMP_MAX", "FLOW_SP_RAMP_MAX"):
        assert f'"{tag}"' in number
        assert tag in catalog
    assert '"sp_ramp_max"' in sensor
    assert "sp_target" in sensor
    assert "spTarget" in card
    sandbox = Path("tools/pid-faceplate/sandbox.js").read_text(encoding="utf-8")
    assert "rampSetpoint" in sandbox
    assert "sp_ramp_max" in sandbox
    assert "SWD-381" not in sandbox
