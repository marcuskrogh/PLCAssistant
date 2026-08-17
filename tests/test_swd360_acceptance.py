"""SWD-360: ISA-TR5.9 Parallel PID contract, Bauer hybrid, glyph, faceplate CO."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from plcassistant.surface.builtin import (
    PID_EQUATION,
    PID_EQUATION_LEGACY,
    PID_TEMPLATE_ID,
    is_factory_pid_equation,
    pid_default_params,
    pid_template,
    wedge_cascade_program,
)
from plcassistant.surface.equations import evaluate_equation
from plcassistant.surface.schema import program_from_dict

ROOT = Path(__file__).resolve().parents[1]
CANVAS = ROOT / "plcassistant" / "app" / "_canvas.py"
CARD = ROOT / "custom_components" / "plcassistant" / "www" / "pid-loop-card.js"
PYPROJECT = ROOT / "pyproject.toml"


def _pid_pins(**overrides: object) -> dict[str, object]:
    pins: dict[str, object] = {
        "pv": 0.0,
        "sp": 0.0,
        "running": True,
        "uff": 0.0,
        "track": False,
        "utrack": 0.0,
    }
    pins.update(overrides)
    return pins


def _eval(params: dict, pins: dict, state: dict, dt: float = 0.1) -> float:
    tmpl = pid_template()
    out = evaluate_equation(PID_EQUATION, tmpl, pins, params, state, dt)
    return float(out["cv"])


def test_unit_pid_declares_parallel_form_and_2dof_defaults() -> None:
    tmpl = pid_template()
    params = tmpl.params
    assert params["form"] == "parallel"
    assert params["beta"] == pytest.approx(1.0)
    assert params["gamma"] == pytest.approx(0.0)
    assert params["u0"] == pytest.approx(0.0)
    assert params["direct_acting"] is False
    pin_names = [p.name for p in tmpl.pins]
    assert pin_names[:3] == ["pv", "sp", "running"]
    assert pin_names[-1] == "cv"
    assert {"uff", "track", "utrack"} <= set(pin_names)
    defaults = {p.name: p.default for p in tmpl.pins}
    assert defaults["uff"] == pytest.approx(0.0)
    assert defaults["track"] is False
    assert defaults["utrack"] == pytest.approx(0.0)
    assert tmpl.body == PID_EQUATION
    assert "ISA Technical Report 5.9" in tmpl.description
    assert "Parallel" in tmpl.description
    assert is_factory_pid_equation(PID_EQUATION_LEGACY)
    assert is_factory_pid_equation("")
    assert not is_factory_pid_equation("cv = 42.0")


def test_unit_hybrid_incremental_clamps_then_unwinds() -> None:
    params = pid_default_params()
    params.update(
        {
            "kp": 0.0,
            "ki": 20.0,
            "kd": 0.0,
            "cv_min": 0.0,
            "cv_max": 10.0,
        }
    )
    state: dict = {}
    pins = _pid_pins(pv=0.0, sp=100.0, running=True)
    cv = 0.0
    for _ in range(40):
        cv = _eval(params, pins, state, 0.1)
    assert cv == pytest.approx(10.0)
    for _ in range(10):
        cv = _eval(params, pins, state, 0.1)
        assert cv == pytest.approx(10.0)
    reverse = _pid_pins(pv=100.0, sp=0.0, running=True)
    cv = _eval(params, reverse, state, 0.1)
    assert cv < 10.0


def test_unit_positional_when_ki_zero_uses_u0() -> None:
    params = pid_default_params()
    params.update({"kp": 2.0, "ki": 0.0, "kd": 0.0, "u0": 5.0, "cv_min": -50.0, "cv_max": 50.0})
    state: dict = {}
    cv = _eval(params, _pid_pins(pv=0.0, sp=10.0, running=True), state, 0.1)
    assert cv == pytest.approx(25.0)


def test_unit_incremental_includes_p_on_first_scan() -> None:
    params = pid_default_params()
    params.update({"kp": 2.0, "ki": 1.0, "kd": 0.0, "cv_min": -100.0, "cv_max": 100.0})
    cv = _eval(params, _pid_pins(pv=0.0, sp=10.0, running=True), {}, 0.1)
    assert cv == pytest.approx(21.0)


def test_unit_derivative_on_pv_does_not_kick_on_sp_step() -> None:
    base = pid_default_params()
    base.update(
        {
            "kp": 1.0,
            "ki": 0.5,
            "kd": 4.0,
            "gamma": 0.0,
            "beta": 1.0,
            "cv_min": -100.0,
            "cv_max": 100.0,
        }
    )
    settle = _pid_pins(pv=50.0, sp=50.0, running=True)
    state_d: dict = {}
    state_p: dict = {}
    params_d = copy.deepcopy(base)
    params_p = copy.deepcopy(base)
    params_p["kd"] = 0.0
    for _ in range(5):
        _eval(params_d, settle, state_d, 0.1)
        _eval(params_p, settle, state_p, 0.1)
    step = _pid_pins(pv=50.0, sp=60.0, running=True)
    cv_d = _eval(params_d, step, state_d, 0.1)
    cv_p = _eval(params_p, step, state_p, 0.1)
    assert cv_d == pytest.approx(cv_p, abs=1e-9)


def test_unit_migrates_legacy_factory_pid_equation_and_fills_params() -> None:
    raw = {
        "version": "1.0",
        "name": "Tank",
        "instances": {
            "level_pi": {
                "template_id": PID_TEMPLATE_ID,
                "library": "builtin",
                "params": {"kp": 40.0, "ki": 5.0, "kd": 0.0, "cv_min": 0.0, "cv_max": 8.0},
                "equation": PID_EQUATION_LEGACY,
            },
            "custom_pid": {
                "template_id": PID_TEMPLATE_ID,
                "library": "builtin",
                "params": {"kp": 3.0, "ki": 1.0},
                "equation": "cv = 7.0",
            },
        },
        "wires": [],
        "execution_order": ["level_pi", "custom_pid"],
    }
    prog = program_from_dict(raw)
    level = prog.instances["level_pi"]
    assert level.params["form"] == "parallel"
    assert level.params["beta"] == pytest.approx(1.0)
    assert level.params["gamma"] == pytest.approx(0.0)
    assert level.params["kp"] == pytest.approx(40.0)
    assert level.equation == PID_EQUATION
    custom = prog.instances["custom_pid"]
    assert custom.equation == "cv = 7.0"
    assert custom.params["form"] == "parallel"


def test_unit_wedge_cascade_keeps_pi_gains_and_isa_tags() -> None:
    prog = program_from_dict(wedge_cascade_program())
    assert prog.instances["level_pi"].params["kp"] == pytest.approx(40.0)
    assert prog.instances["level_pi"].params["ki"] == pytest.approx(5.0)
    assert prog.instances["level_pi"].params["kd"] == pytest.approx(0.0)
    assert prog.instances["level_pi"].params["isa_tag"] == "LIC"
    assert prog.instances["flow_pi"].params["isa_tag"] == "FIC"
    assert prog.instances["level_pi"].equation == PID_EQUATION


def test_unit_canvas_pid_uses_isa_three_mode_glyph() -> None:
    canvas = CANVAS.read_text(encoding="utf-8")
    assert "appendIsaPidChrome" in canvas
    assert "isa-pid" in canvas
    assert "isa-pid-p" in canvas
    assert "isa-pid-i" in canvas
    assert "isa-pid-d" in canvas
    assert "isa-pid-diff" in canvas
    assert "inst.template_id === 'PID'" in canvas
    idx = canvas.find("const isPid")
    assert idx != -1
    chunk = canvas[idx : idx + 900]
    true_branch = chunk.split("} else {")[0]
    assert "appendIsaPidChrome" in true_branch
    assert "block-rect" not in true_branch


def test_unit_faceplate_labels_pv_sp_co() -> None:
    text = CARD.read_text(encoding="utf-8")
    assert "<span>CO</span>" in text
    assert "<span>CV</span>" not in text
    assert "<span>PV</span>" in text
    assert "Active SP" in text
    assert 'data-mode="' in text


def test_unit_default_pytest_still_excludes_live() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    assert "not live" in text
    assert "addopts" in text


def test_unit_app_version_is_0_1_55() -> None:
    assert 'version: "0.1.55"' in (ROOT / "plc_assistant" / "config.yaml").read_text(
        encoding="utf-8"
    )
    manifest = (ROOT / "custom_components" / "plcassistant" / "manifest.json").read_text(
        encoding="utf-8"
    )
    assert '"0.1.55"' in manifest


def test_unit_incremental_includes_constant_uff() -> None:
    params = pid_default_params()
    params.update({"kp": 0.0, "ki": 1.0, "kd": 0.0, "cv_min": 0.0, "cv_max": 100.0})
    cv = _eval(params, _pid_pins(pv=0.0, sp=0.0, running=True, uff=25.0), {}, 0.1)
    assert cv == pytest.approx(25.0)


def test_unit_legacy_last_error_prevents_p_kick() -> None:
    params = pid_default_params()
    params.update({"kp": 10.0, "ki": 0.1, "kd": 0.0, "cv_min": -100.0, "cv_max": 100.0})
    pins = _pid_pins(pv=0.0, sp=5.0, running=True)
    cv = _eval(params, pins, {"last_error": 5.0}, 0.1)
    assert cv == pytest.approx(0.05)


def test_unit_direct_acting_flips_error_sign() -> None:
    params = pid_default_params()
    params.update(
        {
            "kp": 2.0,
            "ki": 0.0,
            "kd": 0.0,
            "u0": 0.0,
            "direct_acting": True,
            "cv_min": -50.0,
            "cv_max": 50.0,
        }
    )
    cv = _eval(params, _pid_pins(pv=0.0, sp=10.0, running=True), {}, 0.1)
    assert cv == pytest.approx(-20.0)


def test_unit_dt_zero_skips_integral_keeps_p() -> None:
    params = pid_default_params()
    params.update({"kp": 2.0, "ki": 100.0, "kd": 0.0, "cv_min": -100.0, "cv_max": 100.0})
    cv = _eval(params, _pid_pins(pv=0.0, sp=10.0, running=True), {}, 0.0)
    assert cv == pytest.approx(20.0)


def test_unit_upgrade_shipped_pid_adds_bauer_pins() -> None:
    from plcassistant.surface.builtin import (
        PID_EQUATION_LEGACY,
        upgrade_builtin_pid_template,
    )
    from plcassistant.surface.model import BlockTemplate, PinDirection, PinSpec

    old = BlockTemplate(
        template_id=PID_TEMPLATE_ID,
        library="builtin",
        description="old",
        pins=[
            PinSpec("pv", PinDirection.IN, "float", 0.0),
            PinSpec("sp", PinDirection.IN, "float", 0.0),
            PinSpec("running", PinDirection.IN, "bool", False),
            PinSpec("cv", PinDirection.OUT, "float", 0.0),
        ],
        params={"kp": 3.0, "ki": 1.0},
        body=PID_EQUATION_LEGACY,
        is_builtin=True,
    )
    up = upgrade_builtin_pid_template(old)
    names = [p.name for p in up.pins]
    assert {"uff", "track", "utrack", "cv"} <= set(names)
    assert up.params["form"] == "parallel"
    assert up.params["kp"] == pytest.approx(3.0)
    assert up.body == PID_EQUATION


def test_system_hybrid_cascade_cvs_move() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

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
    logic.enqueue_operator("start")
    for _ in range(40):
        logic(image)
    assert float(image.get_value("SP_FLOW_AUTO")) > 0.5
    assert float(image.get_value("CMD_SPEED")) > 0.0
    assert float(image.get_value("SP_FLOW_AUTO")) <= 8.0
    assert float(image.get_value("CMD_SPEED")) <= 100.0


def test_dual_tree_isa_pid_glyph_and_faceplate() -> None:
    root_canvas = (ROOT / "plcassistant" / "app" / "_canvas.py").read_text(encoding="utf-8")
    mirror_canvas = (
        ROOT / "plc_assistant" / "plcassistant" / "app" / "_canvas.py"
    ).read_text(encoding="utf-8")
    for label, text in (("root", root_canvas), ("mirror", mirror_canvas)):
        assert "appendIsaPidChrome" in text, label
        assert "isa-pid-p" in text, label
    root_card = CARD.read_text(encoding="utf-8")
    mirror_card = (
        ROOT
        / "plc_assistant"
        / "custom_components"
        / "plcassistant"
        / "www"
        / "pid-loop-card.js"
    ).read_text(encoding="utf-8")
    for label, text in (("root", root_card), ("mirror", mirror_card)):
        assert "<span>CO</span>" in text, label
        assert "<span>CV</span>" not in text, label
