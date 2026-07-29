"""Skid-backed Soft-PLC scan body (SWD-133)."""

from __future__ import annotations

from plcassistant.app.default_image import declare_default_image
from plcassistant.app.skid_scan import SkidImageLogic
from plcassistant.io.quality import QualityStatus
from plcassistant.wedge.skid import Mode


def test_skid_image_logic_start_moves_flow_and_tank():
    image = declare_default_image()
    image.begin_inputs()
    image.apply_input("SP_LEVEL_REQ", 0.20, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    assert logic.skid.last is not None
    assert logic.skid.last.mode is Mode.RUNNING
    for _ in range(20):
        logic(image)
    assert float(image.get_value("SP_FLOW")) > 0.0
    assert float(image.get_value("CMD_SPEED")) > 0.0
    assert float(image.get_value("LT_TANK")) > 0.0


def test_skid_image_logic_stop_zeros_cmd():
    image = declare_default_image()
    image.apply_input("SP_LEVEL_REQ", 0.20, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    for _ in range(10):
        logic(image)
    logic.enqueue_operator("stop")
    logic(image)
    assert logic.skid.last.mode is Mode.STOP
    assert float(image.get_value("CMD_SPEED")) == 0.0
