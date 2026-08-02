"""SWD-221: cascade defaults + cold-start reliability + faceplate wiring."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path("custom_components/plcassistant")


def test_unit_cascade_mode_defaults() -> None:
    from plcassistant.io.datablock import default_tank_datablock_catalog

    block = default_tank_datablock_catalog().get("DB_Tank")
    assert block is not None
    assert float(block.tags["LEVEL_MODE"].default) == pytest.approx(0.0)
    assert float(block.tags["FLOW_MODE"].default) == pytest.approx(1.0)

    meta = (ROOT / "number.py").read_text(encoding="utf-8")
    level = meta.split('"LEVEL_MODE":', 1)[1].split('"SP_FLOW_MAN"', 1)[0]
    flow = meta.split('"FLOW_MODE":', 1)[1].split('"LEVEL_KP"', 1)[0]
    assert '"default": 0.0' in level
    assert '"default": 1.0' in flow


def test_unit_skid_defaults_drive_cascade_on_start() -> None:
    """Level Man + Flow Auto defaults → Start publishes non-zero SP_FLOW/CMD."""
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    # Defaults from datablock: LEVEL_MODE=0, FLOW_MODE=1, SP_LEVEL_MAN=0.20
    image.apply_input("LEVEL_MODE", 0.0, QualityStatus.GOOD)
    image.apply_input("FLOW_MODE", 1.0, QualityStatus.GOOD)
    image.apply_input("SP_LEVEL_MAN", 0.25, QualityStatus.GOOD)
    image.apply_input("LT_TANK", 0.15, QualityStatus.GOOD)
    image.apply_input("LT_RES", 0.20, QualityStatus.GOOD)
    image.apply_input("FT_INLET", 0.0, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    assert image.get_value("MODE") == "RUNNING"
    for _ in range(20):
        logic(image)
    assert float(image.get_value("SP_LEVEL")) == pytest.approx(0.25)
    assert float(image.get_value("SP_FLOW")) > 0.0
    assert float(image.get_value("CMD_SPEED")) > 0.0


def test_integration_no_per_entity_hydrate_publish() -> None:
    text = (ROOT / "number.py").read_text(encoding="utf-8")
    assert "async def async_seed_operator_defaults" in text
    assert "default_operator_in_seeds" in text
    added = text.split("async def async_added_to_hass", 1)[1]
    seed = added.split("async def _on_tag_in", 1)[0]
    assert "do not" in seed.lower() or "batch-seeded" in seed
    assert "await self._publish_in_tag(self._tag, eng)" not in seed


def test_system_setup_defers_plant_and_seeds() -> None:
    init = (ROOT / "__init__.py").read_text(encoding="utf-8")
    assert "async_seed_operator_defaults" in init
    assert "lovelace_cards_registered" in init
    assert "if not await _async_register_frontend_card" in init or (
        "if not await _async_register_frontend_card(hass, base, version)" in init
    )
    # Plant start must come after forward_entry_setups.
    fwd = init.index("async_forward_entry_setups")
    start = init.index("await plant_sim.async_start()")
    assert fwd < start
    sim = (ROOT / "dynamics" / "simulator.py").read_text(encoding="utf-8")
    assert "_POLL_S = 0.1" in sim


def test_integration_level_faceplate_auto_writes_req() -> None:
    pid = (ROOT / "pid_loop.py").read_text(encoding="utf-8")
    level = pid.split("_LEVEL = {", 1)[1].split("_FLOW = {", 1)[0]
    assert '"sp_auto": "SP_LEVEL_REQ"' in level
    assert '"sp_auto_entity": "number.plcassistant_sp_level_req"' in level
    number = (ROOT / "number.py").read_text(encoding="utf-8")
    assert 'elif self._tag == "SP_LEVEL_AUTO"' in number
    assert 'await self._publish_in_tag("SP_LEVEL_REQ", eng)' in number


def test_system_operate_board_man_primary() -> None:
    dash = (ROOT / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 23" in dash
    assert "Level SP Man (default)" in dash
    assert "Level SP Auto (request)" in dash
    # Man appears in Operate before REQ.
    operate = dash.split("title: Operate", 1)[1].split("title: Level PID", 1)[0]
    assert operate.index("sp_level_man") < operate.index("sp_level_req")
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.44"' in manifest
