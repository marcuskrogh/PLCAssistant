"""SWD-223: Flow Manual drives CMD; Level CV is SP_FLOW_AUTO."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path("custom_components/plcassistant")


def test_system_flow_manual_sp_drives_cmd_when_level_error_zero() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 1.0),
        ("FLOW_MODE", 0.0),
        ("SP_LEVEL_REQ", 0.15),  # SP ≈ PV → level CV ≈ 0
        ("SP_FLOW_MAN", 5.0),
        ("CO_FLOW_MAN", 40.0),
        ("LT_TANK", 0.15),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    for _ in range(30):
        logic(image)
    assert image.get_value("MODE") == "RUNNING"
    assert float(image.get_value("SP_FLOW")) == pytest.approx(5.0)
    assert float(image.get_value("SP_FLOW_AUTO")) == pytest.approx(0.0, abs=0.05)
    assert float(image.get_value("CMD_SPEED")) > 1.0


def test_system_flow_manual_zero_does_not_hide_level_cv() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 1.0),
        ("FLOW_MODE", 0.0),
        ("SP_LEVEL_REQ", 0.30),
        ("SP_FLOW_MAN", 0.0),
        ("CO_FLOW_MAN", 0.0),
        ("LT_TANK", 0.15),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    for _ in range(25):
        logic(image)
    assert float(image.get_value("SP_FLOW")) == pytest.approx(0.0)
    assert float(image.get_value("SP_FLOW_AUTO")) > 0.5
    # Flow Man CO=0 → CMD tracks 0, but level CV remains visible on AUTO tag.
    assert float(image.get_value("CMD_SPEED")) == pytest.approx(0.0, abs=0.5)


def test_system_flow_auto_cascade_still_engages() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 1.0),
        ("FLOW_MODE", 1.0),
        ("SP_LEVEL_REQ", 0.30),
        ("LT_TANK", 0.15),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    for _ in range(25):
        logic(image)
    assert float(image.get_value("SP_FLOW_AUTO")) > 0.5
    assert float(image.get_value("SP_FLOW")) == pytest.approx(
        float(image.get_value("SP_FLOW_AUTO")), abs=1e-6
    )
    assert float(image.get_value("CMD_SPEED")) > 0.0


def test_integration_level_cv_is_sp_flow_auto() -> None:
    from plcassistant.io.pid_loop import LEVEL_LOOP

    assert LEVEL_LOOP.cv == "SP_FLOW_AUTO"
    pid = (ROOT / "pid_loop.py").read_text(encoding="utf-8")
    level = pid.split("_LEVEL = {", 1)[1].split("_FLOW = {", 1)[0]
    assert '"cv": "SP_FLOW_AUTO"' in level
    assert '"cv_entity": "sensor.plcassistant_sp_flow_auto"' in level


def test_system_app_version_0_1_43() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.60"' in manifest
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.60"' in config
