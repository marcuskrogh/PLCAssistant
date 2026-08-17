"""Tests for built-in block library (SWD-115).

Covers:
- register_builtins populates library and runtime callables
- LevelPI: running=True produces correct PI output
- LevelPI: running=False holds last cv and incremental state
- FlowPI: running=True produces correct PI output
- FlowPI: running=False forces cv=0 and clears incremental pending
- Anti-windup: integral frozen when output is clamped into saturation
- Cascade parity: [level_pi → flow_pi] numerically matches CascadeController
  for several scenarios (running, not-running, clamps)
- wedge_cascade_program(): loads with program_from_dict; runs with runtime
- wedge_cascade_program() with custom gains matches CascadeController
- Templates are marked is_builtin=True
- No HA imports
"""

from __future__ import annotations

import pytest

from plcassistant.surface.builtin import register_builtins, wedge_cascade_program
from plcassistant.surface.model import TemplateLibrary
from plcassistant.surface.runtime import BlockRuntime, DictContext
from plcassistant.surface.schema import program_from_dict
from plcassistant.wedge.control import CascadeConfig, CascadeController


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_runtime() -> tuple[TemplateLibrary, BlockRuntime]:
    lib = TemplateLibrary()
    runtime = BlockRuntime(lib)
    register_builtins(lib, runtime)
    return lib, runtime


def _cascade_runtime_and_program(
    *,
    level_kp: float = 40.0,
    level_ki: float = 5.0,
    flow_kp: float = 12.0,
    flow_ki: float = 2.0,
    sp_flow_min: float = 0.0,
    sp_flow_max: float = 6.0,
    cmd_speed_min: float = 0.0,
    cmd_speed_max: float = 100.0,
):
    """Return (runtime, program) for a cascade with the given gains."""
    lib, runtime = _make_runtime()
    prog = program_from_dict(
        wedge_cascade_program(
            level_kp=level_kp,
            level_ki=level_ki,
            flow_kp=flow_kp,
            flow_ki=flow_ki,
            sp_flow_min=sp_flow_min,
            sp_flow_max=sp_flow_max,
            cmd_speed_min=cmd_speed_min,
            cmd_speed_max=cmd_speed_max,
        )
    )
    return runtime, prog


def _cascade_context(
    *,
    lt_tank: float,
    sp_level: float,
    ft_inlet: float,
    running: bool,
) -> DictContext:
    return DictContext({
        "level_pi.pv": lt_tank,
        "level_pi.sp": sp_level,
        "level_pi.running": running,
        "flow_pi.pv": ft_inlet,
        "flow_pi.running": running,
    })


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_builtins_populates_library():
    lib, _ = _make_runtime()
    assert ("builtin", "PID") in lib
    assert ("builtin", "level_pi") not in lib
    assert ("builtin", "flow_pi") not in lib


def test_register_builtins_templates_are_builtin():
    lib, _ = _make_runtime()
    tmpl = lib.get("builtin", "PID")
    assert tmpl is not None and tmpl.is_builtin is True
    assert tmpl.body


def test_register_builtins_templates_have_expected_pins():
    lib, _ = _make_runtime()
    tmpl = lib.get("builtin", "PID")
    assert tmpl is not None
    pin_names = [p.name for p in tmpl.pins]
    assert "pv" in pin_names
    assert "sp" in pin_names
    assert "running" in pin_names
    assert "cv" in pin_names


# ---------------------------------------------------------------------------
# LevelPI: standalone
# ---------------------------------------------------------------------------


def test_level_pi_running_produces_positive_cv():
    """When level is below setpoint and running=True, cv > 0."""
    lib, runtime = _make_runtime()
    prog = program_from_dict({
        "version": "1.0",
        "instances": {
            "lp": {
                "template_id": "level_pi",
                "library": "builtin",
                "params": {"kp": 40.0, "ki": 5.0, "cv_min": 0.0, "cv_max": 6.0},
            }
        },
        "wires": [],
        "execution_order": ["lp"],
    })
    ctx = DictContext({
        "lp.pv": 0.15,
        "lp.sp": 0.20,
        "lp.running": True,
    })
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("lp.cv") > 0.0


def test_level_pi_not_running_holds_last_cv():
    """running=False: hold last cv, do not advance integral."""
    lib, runtime = _make_runtime()
    prog = program_from_dict({
        "version": "1.0",
        "instances": {
            "lp": {
                "template_id": "level_pi",
                "library": "builtin",
                "params": {"kp": 40.0, "ki": 5.0, "cv_min": 0.0, "cv_max": 6.0},
            }
        },
        "wires": [],
        "execution_order": ["lp"],
    })
    ctx = DictContext({"lp.pv": 0.10, "lp.sp": 0.20, "lp.running": True})
    runtime.tick(prog, ctx, 0.1)
    held_cv = ctx.get("lp.cv")
    assert held_cv > 0.0

    # Stop
    ctx.set("lp.running", False)
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("lp.cv") == pytest.approx(held_cv)


def test_level_pi_not_running_holds_incremental_state():
    """running=False holds last cv (level) and clears bumpless_pending."""
    lib, runtime = _make_runtime()
    prog = program_from_dict({
        "version": "1.0",
        "instances": {
            "lp": {
                "template_id": "level_pi",
                "library": "builtin",
                "params": {"kp": 40.0, "ki": 5.0, "cv_min": 0.0, "cv_max": 6.0},
            }
        },
        "wires": [],
        "execution_order": ["lp"],
    })
    ctx = DictContext({"lp.pv": 0.10, "lp.sp": 0.20, "lp.running": True})
    for _ in range(10):
        runtime.tick(prog, ctx, 0.1)
    held_cv = ctx.get("lp.cv")
    ctx.set("lp.running", False)
    runtime.tick(prog, ctx, 0.1)
    state = runtime.state.get("lp", {})
    assert ctx.get("lp.cv") == pytest.approx(held_cv)
    assert state.get("u_old") == pytest.approx(held_cv)
    assert state.get("bumpless_pending") is False
    assert "integral" not in state


def test_level_pi_cv_clamped_to_cv_max():
    """CV never exceeds cv_max regardless of large error."""
    lib, runtime = _make_runtime()
    prog = program_from_dict({
        "version": "1.0",
        "instances": {
            "lp": {
                "template_id": "level_pi",
                "library": "builtin",
                "params": {"kp": 1000.0, "ki": 100.0, "cv_min": 0.0, "cv_max": 6.0},
            }
        },
        "wires": [],
        "execution_order": ["lp"],
    })
    ctx = DictContext({"lp.pv": 0.0, "lp.sp": 1.0, "lp.running": True})
    for _ in range(5):
        runtime.tick(prog, ctx, 0.1)
    assert ctx.get("lp.cv") == pytest.approx(6.0)


# ---------------------------------------------------------------------------
# FlowPI: standalone
# ---------------------------------------------------------------------------


def test_flow_pi_running_produces_positive_cv():
    lib, runtime = _make_runtime()
    prog = program_from_dict({
        "version": "1.0",
        "instances": {
            "fp": {
                "template_id": "flow_pi",
                "library": "builtin",
                "params": {"kp": 12.0, "ki": 2.0, "cv_min": 0.0, "cv_max": 100.0},
            }
        },
        "wires": [],
        "execution_order": ["fp"],
    })
    ctx = DictContext({"fp.pv": 0.0, "fp.sp": 3.0, "fp.running": True})
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("fp.cv") > 0.0


def test_flow_pi_not_running_forces_cv_zero():
    lib, runtime = _make_runtime()
    prog = program_from_dict({
        "version": "1.0",
        "instances": {
            "fp": {
                "template_id": "flow_pi",
                "library": "builtin",
                "params": {"kp": 12.0, "ki": 2.0, "cv_min": 0.0, "cv_max": 100.0},
            }
        },
        "wires": [],
        "execution_order": ["fp"],
    })
    ctx = DictContext({"fp.pv": 0.0, "fp.sp": 3.0, "fp.running": True})
    runtime.tick(prog, ctx, 0.1)
    ctx.set("fp.running", False)
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("fp.cv") == pytest.approx(0.0)


def test_flow_pi_not_running_zeros_incremental_state():
    """running=False forces cv=0 (flow) and clears bumpless_pending."""
    lib, runtime = _make_runtime()
    prog = program_from_dict({
        "version": "1.0",
        "instances": {
            "fp": {
                "template_id": "flow_pi",
                "library": "builtin",
                "params": {"kp": 12.0, "ki": 2.0, "cv_min": 0.0, "cv_max": 100.0},
            }
        },
        "wires": [],
        "execution_order": ["fp"],
    })
    ctx = DictContext({"fp.pv": 0.0, "fp.sp": 3.0, "fp.running": True})
    for _ in range(10):
        runtime.tick(prog, ctx, 0.1)
    ctx.set("fp.running", False)
    runtime.tick(prog, ctx, 0.1)
    state = runtime.state.get("fp", {})
    assert ctx.get("fp.cv") == pytest.approx(0.0)
    assert state.get("u_old") == pytest.approx(0.0)
    assert state.get("bumpless_pending") is False
    assert "integral" not in state


# ---------------------------------------------------------------------------
# Cascade parity: [level_pi → flow_pi] == CascadeController
# ---------------------------------------------------------------------------


def _step_cascade(
    runtime: BlockRuntime,
    prog,
    ctx: DictContext,
    dt: float,
) -> tuple[float, float]:
    """Tick the cascade and return (sp_flow, cmd_speed)."""
    runtime.tick(prog, ctx, dt)
    sp_flow = ctx.get("level_pi.cv")
    cmd_speed = ctx.get("flow_pi.cv")
    return sp_flow, cmd_speed


@pytest.mark.parametrize("dt", [0.05, 0.1, 0.2])
def test_cascade_parity_single_running_step(dt: float):
    """First RUNNING tick: cascade blocks match CascadeController exactly."""
    cfg = CascadeConfig(
        level_kp=40.0, level_ki=5.0,
        flow_kp=12.0, flow_ki=2.0,
        sp_flow_min=0.0, sp_flow_max=6.0,
        cmd_speed_min=0.0, cmd_speed_max=100.0,
    )
    ctrl = CascadeController(cfg)
    lt_tank, ft_inlet, sp_level = 0.15, 0.5, 0.20

    expected = ctrl.step(dt, lt_tank=lt_tank, ft_inlet=ft_inlet,
                         sp_level=sp_level, running=True)

    runtime, prog = _cascade_runtime_and_program()
    ctx = _cascade_context(lt_tank=lt_tank, sp_level=sp_level,
                           ft_inlet=ft_inlet, running=True)
    sp_flow, cmd_speed = _step_cascade(runtime, prog, ctx, dt)

    assert sp_flow == pytest.approx(expected.sp_flow, rel=1e-9)
    assert cmd_speed == pytest.approx(expected.cmd_speed, rel=1e-9)


def test_cascade_parity_multiple_running_steps():
    """After several ticks, cascade blocks match CascadeController."""
    cfg = CascadeConfig(
        level_kp=40.0, level_ki=5.0,
        flow_kp=12.0, flow_ki=2.0,
        sp_flow_min=0.0, sp_flow_max=6.0,
        cmd_speed_min=0.0, cmd_speed_max=100.0,
    )
    ctrl = CascadeController(cfg)
    runtime, prog = _cascade_runtime_and_program()

    lt_tank, ft_inlet, sp_level, dt = 0.12, 0.0, 0.22, 0.1

    for _ in range(20):
        # Both controllers receive identical inputs each step.
        expected = ctrl.step(dt, lt_tank=lt_tank, ft_inlet=ft_inlet,
                             sp_level=sp_level, running=True)
        ctx = _cascade_context(lt_tank=lt_tank, sp_level=sp_level,
                               ft_inlet=ft_inlet, running=True)
        sp_flow, cmd_speed = _step_cascade(runtime, prog, ctx, dt)

        assert sp_flow == pytest.approx(expected.sp_flow, rel=1e-9, abs=1e-12)
        assert cmd_speed == pytest.approx(expected.cmd_speed, rel=1e-9, abs=1e-12)

        # Advance the simulated process for the next iteration (same for both).
        ft_inlet = ft_inlet + 0.05 * (sp_flow - ft_inlet) * dt
        lt_tank = lt_tank + 0.01 * ft_inlet * dt


def test_cascade_parity_not_running():
    """not running → cmd_speed=0, sp_flow held; matches CascadeController."""
    cfg = CascadeConfig(
        level_kp=40.0, level_ki=5.0,
        flow_kp=12.0, flow_ki=2.0,
    )
    ctrl = CascadeController(cfg)
    runtime, prog = _cascade_runtime_and_program()

    lt_tank, ft_inlet, sp_level, dt = 0.10, 0.0, 0.20, 0.1

    # One running step to establish state
    ctrl.step(dt, lt_tank=lt_tank, ft_inlet=ft_inlet, sp_level=sp_level, running=True)
    ctx = _cascade_context(lt_tank=lt_tank, sp_level=sp_level,
                           ft_inlet=ft_inlet, running=True)
    _step_cascade(runtime, prog, ctx, dt)

    # Now stop
    expected_stop = ctrl.step(dt, lt_tank=lt_tank, ft_inlet=ft_inlet,
                              sp_level=sp_level, running=False)
    ctx.set("level_pi.running", False)
    ctx.set("flow_pi.running", False)
    sp_flow, cmd_speed = _step_cascade(runtime, prog, ctx, dt)

    assert cmd_speed == pytest.approx(0.0, abs=1e-9)
    assert sp_flow == pytest.approx(expected_stop.sp_flow, rel=1e-9, abs=1e-9)


def test_cascade_parity_clamp_sp_flow():
    """When level error forces sp_flow > cv_max, it is clamped; matches CascadeController."""
    cfg = CascadeConfig(
        level_kp=1000.0, level_ki=0.0,  # huge gain to saturate immediately
        flow_kp=12.0, flow_ki=2.0,
        sp_flow_min=0.0, sp_flow_max=6.0,
        cmd_speed_min=0.0, cmd_speed_max=100.0,
    )
    ctrl = CascadeController(cfg)
    runtime, prog = _cascade_runtime_and_program(
        level_kp=1000.0, level_ki=0.0,
        sp_flow_max=6.0,
    )
    lt_tank, ft_inlet, sp_level, dt = 0.0, 0.0, 1.0, 0.1

    expected = ctrl.step(dt, lt_tank=lt_tank, ft_inlet=ft_inlet,
                         sp_level=sp_level, running=True)
    ctx = _cascade_context(lt_tank=lt_tank, sp_level=sp_level,
                           ft_inlet=ft_inlet, running=True)
    sp_flow, cmd_speed = _step_cascade(runtime, prog, ctx, dt)

    assert sp_flow == pytest.approx(expected.sp_flow, rel=1e-9)
    assert sp_flow == pytest.approx(6.0, abs=1e-9)  # clamped
    assert cmd_speed == pytest.approx(expected.cmd_speed, rel=1e-9)


def test_cascade_parity_anti_windup():
    """With integral enabled, anti-windup keeps integrals in sync with CascadeController."""
    cfg = CascadeConfig(
        level_kp=40.0, level_ki=5.0,
        flow_kp=12.0, flow_ki=2.0,
        sp_flow_min=0.0, sp_flow_max=6.0,
        cmd_speed_min=0.0, cmd_speed_max=100.0,
    )
    ctrl = CascadeController(cfg)
    runtime, prog = _cascade_runtime_and_program()

    lt_tank, ft_inlet, sp_level, dt = 0.0, 0.0, 1.0, 0.1  # large error → saturate

    for _ in range(15):
        expected = ctrl.step(dt, lt_tank=lt_tank, ft_inlet=ft_inlet,
                             sp_level=sp_level, running=True)
        ctx = _cascade_context(lt_tank=lt_tank, sp_level=sp_level,
                               ft_inlet=ft_inlet, running=True)
        sp_flow, cmd_speed = _step_cascade(runtime, prog, ctx, dt)

        assert sp_flow == pytest.approx(expected.sp_flow, rel=1e-6, abs=1e-9)
        assert cmd_speed == pytest.approx(expected.cmd_speed, rel=1e-6, abs=1e-9)


# ---------------------------------------------------------------------------
# wedge_cascade_program()
# ---------------------------------------------------------------------------


def test_wedge_cascade_program_valid_program_from_dict():
    """Factory output loads without error via program_from_dict."""
    lib, runtime = _make_runtime()
    prog_dict = wedge_cascade_program()
    prog = program_from_dict(prog_dict)
    assert "level_pi" in prog.instances
    assert "flow_pi" in prog.instances
    assert prog.execution_order == ["level_pi", "flow_pi"]
    assert len(prog.wires) == 1
    wire = prog.wires[0]
    assert wire.src_instance == "level_pi" and wire.src_pin == "cv"
    assert wire.dst_instance == "flow_pi" and wire.dst_pin == "sp"


def test_wedge_cascade_program_runs_without_error():
    lib, runtime = _make_runtime()
    prog = program_from_dict(wedge_cascade_program())
    ctx = _cascade_context(lt_tank=0.15, sp_level=0.20, ft_inlet=0.5, running=True)
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("level_pi.cv") is not None
    assert ctx.get("flow_pi.cv") is not None


def test_wedge_cascade_program_custom_gains_match_cascade_controller():
    """Custom-gain factory output is numerically identical to CascadeController."""
    kw = dict(
        level_kp=50.0, level_ki=4.0,
        flow_kp=15.0, flow_ki=3.0,
        sp_flow_min=0.0, sp_flow_max=8.0,
        cmd_speed_min=0.0, cmd_speed_max=100.0,
    )
    cfg = CascadeConfig(
        level_kp=kw["level_kp"], level_ki=kw["level_ki"],
        flow_kp=kw["flow_kp"], flow_ki=kw["flow_ki"],
        sp_flow_min=kw["sp_flow_min"], sp_flow_max=kw["sp_flow_max"],
        cmd_speed_min=kw["cmd_speed_min"], cmd_speed_max=kw["cmd_speed_max"],
    )
    ctrl = CascadeController(cfg)
    runtime, prog = _cascade_runtime_and_program(**kw)

    lt_tank, ft_inlet, sp_level, dt = 0.12, 0.0, 0.25, 0.1
    expected = ctrl.step(dt, lt_tank=lt_tank, ft_inlet=ft_inlet,
                         sp_level=sp_level, running=True)
    ctx = _cascade_context(lt_tank=lt_tank, sp_level=sp_level,
                           ft_inlet=ft_inlet, running=True)
    sp_flow, cmd_speed = _step_cascade(runtime, prog, ctx, dt)

    assert sp_flow == pytest.approx(expected.sp_flow, rel=1e-9)
    assert cmd_speed == pytest.approx(expected.cmd_speed, rel=1e-9)


def test_wedge_cascade_program_instance_params_match_gains():
    """Instance params in the factory dict match the supplied gains."""
    d = wedge_cascade_program(level_kp=99.0, flow_ki=7.0)
    assert d["instances"]["level_pi"]["params"]["kp"] == 99.0
    assert d["instances"]["flow_pi"]["params"]["ki"] == 7.0


# ---------------------------------------------------------------------------
# No HA imports
# ---------------------------------------------------------------------------


def test_no_ha_imports_in_builtin():
    import sys

    mod = sys.modules.get("plcassistant.surface.builtin")
    if mod is not None:
        for attr in dir(mod):
            assert "homeassistant" not in attr.lower(), (
                f"builtin module references homeassistant symbol: {attr}"
            )
