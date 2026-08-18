"""SWD-383: flow cascade slave defaults to Remote, not Automatic."""

from __future__ import annotations

from pathlib import Path

import pytest

from plcassistant.io.pid_loop import FLOW_LOOP, SpSourceMode

ROOT = Path("custom_components/plcassistant")


def test_unit_flow_mode_default_is_remote() -> None:
    from plcassistant.io.datablock import default_tank_datablock_catalog

    block = default_tank_datablock_catalog().get("DB_Tank")
    assert block is not None
    assert float(block.tags["LEVEL_MODE"].default) == pytest.approx(1.0)
    assert float(block.tags["FLOW_MODE"].default) == pytest.approx(2.0)
    assert "SP_FLOW_REQ" in block.tags
    assert FLOW_LOOP.sp_auto == "SP_FLOW_REQ"
    assert FLOW_LOOP.sp_rem == "SP_FLOW_AUTO"

    meta = (ROOT / "number.py").read_text(encoding="utf-8")
    flow = meta.split('"FLOW_MODE":', 1)[1].split('"LEVEL_KP"', 1)[0]
    assert '"default": 2.0' in flow
    assert '"object_id": "plcassistant_sp_flow_req"' in meta

    pid = (ROOT / "pid_loop.py").read_text(encoding="utf-8")
    flow_spec = pid.split("_FLOW = {", 1)[1].split("DEMO_PID_LOOPS", 1)[0]
    assert '"sp_auto": "SP_FLOW_REQ"' in flow_spec
    assert '"sp_auto_entity": "number.plcassistant_sp_flow_req"' in flow_spec
    assert '"sp_rem": "SP_FLOW_AUTO"' in flow_spec
    assert '"sp_rem_entity": "sensor.plcassistant_sp_flow_auto"' in flow_spec
    assert (
        'self._attr_native_value = "remote" if loop_id == "flow" else "automatic"'
        in pid
    )


def test_unit_missing_flow_mode_defaults_remote() -> None:
    from plcassistant.app.skid_scan import _resolve_flow_mode

    class _FakeImage:
        def names(self) -> tuple[str, ...]:
            return ()

        def get_value(self, name: str) -> object:
            raise KeyError(name)

    assert _resolve_flow_mode(_FakeImage()) is SpSourceMode.REMOTE


def test_system_flow_remote_cascade_on_start() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 1.0),
        ("FLOW_MODE", 2.0),
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
    assert image.get_value("MODE") == "RUNNING"
    assert float(image.get_value("SP_FLOW_AUTO")) > 0.5
    assert float(image.get_value("SP_FLOW")) == pytest.approx(
        float(image.get_value("SP_FLOW_AUTO")), abs=1e-6
    )
    assert float(image.get_value("CMD_SPEED")) > 0.0


def test_system_flow_auto_uses_local_sp_not_cascade() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 1.0),
        ("FLOW_MODE", 1.0),
        ("SP_LEVEL_REQ", 0.30),
        ("SP_FLOW_REQ", 4.0),
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
    assert float(image.get_value("SP_FLOW")) == pytest.approx(4.0)
    assert float(image.get_value("SP_FLOW_AUTO")) > 0.5
    assert float(image.get_value("SP_FLOW")) != pytest.approx(
        float(image.get_value("SP_FLOW_AUTO")), abs=0.2
    )
    assert float(image.get_value("CMD_SPEED")) > 0.0


def test_system_app_version_0_1_66() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.66"' in manifest
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.66"' in config
    docker = Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.66" in docker
    dual = Path("plc_assistant/custom_components/plcassistant/manifest.json")
    assert '"0.1.66"' in dual.read_text(encoding="utf-8")
