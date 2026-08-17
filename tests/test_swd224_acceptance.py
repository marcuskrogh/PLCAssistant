"""SWD-224: Start drives PID CVs via common tag↔pin wirings."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path("custom_components/plcassistant")


def test_unit_tag_pin_wire_format_round_trip_and_apply() -> None:
    """One format covers all wirings — no per-tag bridge tests required."""
    from plcassistant.surface.io_wires import (
        IoDir,
        TagPinWire,
        apply_io_wires_in,
        apply_io_wires_out,
        tag_pin_wires_from_list,
        validate_tag_pin_wires,
        wedge_cascade_io_wires,
    )

    raw = [w.to_dict() for w in wedge_cascade_io_wires()]
    wires = tag_pin_wires_from_list(raw)
    validate_tag_pin_wires(wires)
    assert all(isinstance(w, TagPinWire) for w in wires)
    assert {w.direction for w in wires} == {IoDir.IN, IoDir.OUT}

    tags = {
        "LT_TANK": 0.15,
        "FT_INLET": 0.0,
        "_SHELL.LEVEL_SP": 0.30,
        "_SHELL.RUNNING": True,
        "_SHELL.FLOW_SP_OVERRIDE": 4.0,
    }
    pins: dict[str, object] = {}
    n_in = apply_io_wires_in(
        wires, get_tag=tags.__getitem__, set_pin=pins.__setitem__
    )
    assert n_in == sum(1 for w in wires if w.direction is IoDir.IN)
    # Generic: every IN wire landed in pins under instance.pin
    for w in wires:
        if w.direction is IoDir.IN:
            assert pins[w.context_key] == tags[w.tag]

    # Simulate PID outs then apply OUT wires generically
    pins["level_pi.cv"] = 2.5
    pins["flow_pi.cv"] = 40.0
    out: dict[str, object] = {}
    n_out = apply_io_wires_out(
        wires, get_pin=pins.__getitem__, set_tag=out.__setitem__
    )
    assert n_out == sum(1 for w in wires if w.direction is IoDir.OUT)
    for w in wires:
        if w.direction is IoDir.OUT:
            assert out[w.tag] == pins[w.context_key]


def test_unit_duplicate_in_wire_rejected() -> None:
    from plcassistant.surface.io_wires import (
        IoDir,
        TagPinWire,
        validate_tag_pin_wires,
    )

    with pytest.raises(ValueError, match="multiple IN"):
        validate_tag_pin_wires(
            [
                TagPinWire("A", "x", "pv", IoDir.IN),
                TagPinWire("B", "x", "pv", IoDir.IN),
            ]
        )


def test_system_start_drives_pid_cvs_via_io_wires() -> None:
    """RUNNING + Level Man SP≠PV + Flow Auto → SP_FLOW_AUTO and CMD_SPEED rise."""
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus
    from plcassistant.surface.io_wires import wedge_cascade_io_wires

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 0.0),
        ("FLOW_MODE", 1.0),
        ("SP_LEVEL_MAN", 0.30),
        ("LT_TANK", 0.15),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    assert logic.skid.io_wires == wedge_cascade_io_wires()
    logic.enqueue_operator("start")
    logic(image)
    assert image.get_value("MODE") == "RUNNING"
    # First scan may be bumpless-zero; CVs must move within 30 scans.
    for _ in range(30):
        logic(image)
    assert float(image.get_value("SP_FLOW_AUTO")) > 0.5
    assert float(image.get_value("CMD_SPEED")) > 0.0
    # Shell still owns running enable through the common map.
    assert logic.skid.block_context is not None
    assert logic.skid.block_context["level_pi.running"] is True
    assert logic.skid.block_context["flow_pi.running"] is True


def test_system_faceplate_gains_reach_live_pid_instances() -> None:
    """LEVEL_KP/FLOW_KP image tags must update executing instance params."""
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 0.0),
        ("FLOW_MODE", 1.0),
        ("SP_LEVEL_MAN", 0.30),
        ("LEVEL_KP", 55.0),
        ("LEVEL_KI", 7.0),
        ("FLOW_KP", 18.0),
        ("FLOW_KI", 3.0),
        ("LT_TANK", 0.15),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    prog = logic.skid.program_loader.program  # type: ignore[union-attr]
    assert prog.instances["level_pi"].params["kp"] == pytest.approx(55.0)
    assert prog.instances["level_pi"].params["ki"] == pytest.approx(7.0)
    assert prog.instances["flow_pi"].params["kp"] == pytest.approx(18.0)
    assert prog.instances["flow_pi"].params["ki"] == pytest.approx(3.0)
    # Sync-before-bumpless: retuned Start must move level CV quickly.
    for _ in range(3):
        logic(image)
    assert float(image.get_value("SP_FLOW_AUTO")) > 0.05


def test_unit_prefer_context_falls_back_to_wire_when_absent() -> None:
    from plcassistant.surface.builtin import register_builtins, wedge_cascade_program
    from plcassistant.surface.model import TemplateLibrary
    from plcassistant.surface.runtime import BlockRuntime, DictContext
    from plcassistant.surface.schema import program_from_dict

    lib = TemplateLibrary()
    rt = BlockRuntime(lib)
    register_builtins(lib, rt)
    prog = program_from_dict(wedge_cascade_program())
    ctx = DictContext(
        {
            "level_pi.pv": 0.0,
            "level_pi.sp": 1.0,
            "level_pi.running": True,
            "flow_pi.pv": 0.0,
            "flow_pi.running": True,
            # flow_pi.sp intentionally absent while prefer_context asks for it
        }
    )
    rt.tick(prog, ctx, 0.1, prefer_context={("flow_pi", "sp")})
    level_cv = float(ctx["level_pi.cv"])
    flow_cv = float(ctx["flow_pi.cv"])
    assert level_cv > 0.0
    # Missing prefer_context value must use cascade wire (level CV → flow SP),
    # not pin default 0 — so flow sees a positive SP and drives CV.
    assert flow_cv > 0.0


def test_system_flow_manual_prefer_context_does_not_mutate_wires() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 0.0),
        ("FLOW_MODE", 0.0),
        ("SP_LEVEL_MAN", 0.15),
        ("SP_FLOW_MAN", 5.0),
        ("LT_TANK", 0.15),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    prog = logic.skid.program_loader.program  # type: ignore[union-attr]
    wires_before = list(prog.wires)
    logic.enqueue_operator("start")
    logic(image)
    for _ in range(20):
        logic(image)
    assert list(prog.wires) == wires_before
    assert float(image.get_value("CMD_SPEED")) > 1.0


def test_system_app_version_0_1_44() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.55"' in manifest
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.55"' in config
    docker = Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.55" in docker
    dash = (ROOT / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 28" in dash
