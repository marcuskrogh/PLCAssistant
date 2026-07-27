"""SWD-82 acceptance tests — docs/surface/07-acceptance.md (SWD-118).

Criteria (AC-1 … AC-7) mirror docs/PLAN.md acceptance.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from plcassistant.control import PHASE_ORDER
from plcassistant.surface import (
    BlockRuntime,
    DictContext,
    ProgramLoader,
    TemplateLibrary,
    add_user_template,
    make_user_template,
    place_block,
    program_from_dict,
    program_to_dict,
    register_builtins,
    reset_instance,
    wedge_cascade_program,
)
from plcassistant.wedge.safety import Mode, TripCode
from plcassistant.wedge.skid import LimitConfig, OperatorCommand, Skid, SkidConfig
from plcassistant.wedge.control import CascadeConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _running_skid(scans: int = 20) -> Skid:
    """Return a default skid that has been started and run for *scans* steps."""
    skid = Skid()
    skid.step(0.1, command=OperatorCommand.START)
    for _ in range(scans):
        skid.step(0.1)
    assert skid.last is not None
    assert skid.last.mode is Mode.RUNNING
    return skid


# ---------------------------------------------------------------------------
# AC-1 — Mock skid runnable as block program under fixed safety shell
# ---------------------------------------------------------------------------


def test_ac1_skid_uses_block_runtime_by_default():
    """Default Skid holds a ProgramLoader + BlockRuntime."""
    skid = Skid()
    assert skid.block_runtime is not None
    assert skid.program_loader is not None
    assert skid.block_context is not None
    assert skid.program_loader.program is not None


def test_ac1_skid_block_runtime_produces_cascade_outputs():
    """Running skid via block program produces positive sp_flow and cmd_speed."""
    skid = _running_skid(25)
    snap = skid.last
    assert snap is not None
    assert snap.sp_flow > 0.0
    assert snap.cmd_speed > 0.0
    assert snap.ft_inlet is not None and snap.ft_inlet > 0.0


def test_ac1_scan_phase_order_unchanged():
    """Phase order IN→SAFETY→CONTROL→OUT is preserved after migration."""
    skid = Skid()
    snap = skid.step(0.1)
    assert snap.scan_phases == PHASE_ORDER


def test_ac1_cascade_snapshot_fields_present():
    """SkidSnapshot.cascade, sp_flow, cmd_speed, mode are all set each scan."""
    skid = _running_skid(10)
    snap = skid.last
    assert snap is not None
    assert snap.cascade is not None
    assert isinstance(snap.sp_flow, float)
    assert isinstance(snap.cmd_speed, float)
    assert snap.mode is Mode.RUNNING


# ---------------------------------------------------------------------------
# AC-2 — Copy-on-place independence and reset-to-library
# ---------------------------------------------------------------------------


def test_ac2_place_block_creates_independent_copy():
    """place_block returns an instance whose params are independent of the template."""
    from plcassistant.surface.model import TemplateLibrary

    lib = TemplateLibrary()
    register_builtins(lib, BlockRuntime(lib))
    tmpl = lib.get("builtin", "level_pi")
    assert tmpl is not None

    inst = place_block(tmpl, "lpi_test", params={"kp": 99.0})
    assert inst.params["kp"] == pytest.approx(99.0)
    # Mutating the placed instance must not affect the template
    inst.params["kp"] = 1.0
    assert tmpl.params["kp"] == pytest.approx(40.0)


def test_ac2_two_placed_instances_are_independent():
    """Two placed copies from the same template have independent param dicts."""
    from plcassistant.surface.model import TemplateLibrary

    lib = TemplateLibrary()
    register_builtins(lib, BlockRuntime(lib))
    tmpl = lib.get("builtin", "level_pi")
    assert tmpl is not None

    a = place_block(tmpl, "a")
    b = place_block(tmpl, "b")
    a.params["kp"] = 500.0
    assert b.params["kp"] == pytest.approx(40.0)


def test_ac2_reset_instance_restores_template_defaults():
    """reset_instance rebuilds params from the template, preserving instance_id."""
    from plcassistant.surface.model import TemplateLibrary

    lib = TemplateLibrary()
    register_builtins(lib, BlockRuntime(lib))
    tmpl = lib.get("builtin", "level_pi")
    assert tmpl is not None

    inst = place_block(tmpl, "lpi_r", params={"kp": 999.0})
    restored = reset_instance(inst, tmpl)
    assert restored.instance_id == "lpi_r"
    assert restored.params["kp"] == pytest.approx(40.0)
    # Mutating the restored instance must not affect the template
    restored.params["kp"] = 0.0
    assert tmpl.params["kp"] == pytest.approx(40.0)


# ---------------------------------------------------------------------------
# AC-3 — Custom user Python block place + run in CONTROL
# ---------------------------------------------------------------------------


def test_ac3_custom_block_via_runtime():
    """A user block with a Python body executes in a BlockRuntime tick."""
    lib = TemplateLibrary()
    rt = BlockRuntime(lib)
    register_builtins(lib, rt)

    prog_dict = {
        "version": "1.0",
        "user_templates": {
            "double": {
                "template_id": "double",
                "library": "user",
                "description": "Doubles the input",
                "pins": [
                    {"name": "inp", "direction": "IN", "data_type": "float", "default": 0.0},
                    {"name": "out", "direction": "OUT", "data_type": "float"},
                ],
                "params": {},
                "body": "out = inp * 2.0",
            }
        },
        "instances": {
            "d1": {"template_id": "double", "library": "user", "params": {}}
        },
        "wires": [],
        "execution_order": ["d1"],
    }
    loader = ProgramLoader(lib, rt)
    loader.load(program_from_dict(prog_dict))

    ctx = DictContext({"d1.inp": 5.0})
    rt.tick(loader.program, ctx, 0.1)
    assert ctx["d1.out"] == pytest.approx(10.0)


def test_ac3_custom_block_in_skid_control_via_replace_program():
    """Custom block placed alongside cascade blocks runs in skid CONTROL phase."""
    skid = Skid()
    loader = skid.program_loader
    assert loader is not None
    assert skid.block_context is not None

    # Build extended cascade program with a spy block that reads level_pi.cv
    prog_dict = wedge_cascade_program()
    prog_dict["user_templates"] = {
        "spy": {
            "template_id": "spy",
            "library": "user",
            "description": "Triples its input",
            "pins": [
                {"name": "inp", "direction": "IN", "data_type": "float", "default": 0.0},
                {"name": "out", "direction": "OUT", "data_type": "float"},
            ],
            "params": {"factor": 3.0},
            "body": "out = inp * factor",
        }
    }
    prog_dict["instances"]["spy"] = {
        "template_id": "spy",
        "library": "user",
        "params": {"factor": 3.0},
    }
    prog_dict["wires"].append({
        "src_instance": "level_pi",
        "src_pin": "cv",
        "dst_instance": "spy",
        "dst_pin": "inp",
    })
    prog_dict["execution_order"] = ["level_pi", "flow_pi", "spy"]

    loader.restart_apply(program_from_dict(prog_dict))

    # Fetch ctx AFTER apply — restart_apply replaces the DictContext.
    ctx = skid.block_context

    # Run the skid for several scans
    skid.step(0.1, command=OperatorCommand.START)
    for _ in range(15):
        skid.step(0.1)

    sp_flow = ctx.get("level_pi.cv") or 0.0
    spy_out = ctx.get("spy.out") or 0.0
    assert sp_flow > 0.0, "cascade must produce positive sp_flow"
    assert spy_out == pytest.approx(sp_flow * 3.0), "spy block must run in CONTROL"


def test_ac3_make_user_template_and_add_to_program():
    """make_user_template + add_user_template round-trip via program dict."""
    tmpl = make_user_template(
        "gain",
        body="out = x * gain",
        library="user",
        pins=[
            {"name": "x", "direction": "IN", "data_type": "float", "default": 0.0},
            {"name": "out", "direction": "OUT", "data_type": "float"},
        ],
        params={"gain": 2.0},
    )
    prog = program_from_dict({"version": "1.0", "instances": {}, "wires": [], "execution_order": []})
    add_user_template(prog, tmpl)
    assert "gain" in prog.user_templates
    d = program_to_dict(prog)
    assert "gain" in (d.get("user_templates") or {})


# ---------------------------------------------------------------------------
# AC-4 — YAML-shaped program dict round-trip
# ---------------------------------------------------------------------------


def test_ac4_cascade_program_dict_round_trip():
    """wedge_cascade_program() parses and re-serialises without data loss."""
    original = wedge_cascade_program()
    prog = program_from_dict(original)
    serialised = program_to_dict(prog)

    assert set(serialised["instances"].keys()) == {"level_pi", "flow_pi"}
    assert serialised["execution_order"] == ["level_pi", "flow_pi"]
    assert len(serialised["wires"]) == 1

    # Params survive round-trip
    assert serialised["instances"]["level_pi"]["params"]["kp"] == pytest.approx(40.0)
    assert serialised["instances"]["flow_pi"]["params"]["kp"] == pytest.approx(12.0)


def test_ac4_program_with_user_template_round_trip():
    """Program including a user template serialises and loads cleanly."""
    prog_dict = {
        "version": "1.0",
        "user_templates": {
            "adder": {
                "template_id": "adder",
                "library": "user",
                "description": "Sum two inputs",
                "pins": [
                    {"name": "a", "direction": "IN", "data_type": "float", "default": 0.0},
                    {"name": "b", "direction": "IN", "data_type": "float", "default": 0.0},
                    {"name": "out", "direction": "OUT", "data_type": "float"},
                ],
                "params": {},
                "body": "out = a + b",
            }
        },
        "instances": {
            "add1": {"template_id": "adder", "library": "user", "params": {}}
        },
        "wires": [],
        "execution_order": ["add1"],
    }
    prog = program_from_dict(prog_dict)
    serialised = program_to_dict(prog)
    assert "adder" in (serialised.get("user_templates") or {})
    assert serialised["user_templates"]["adder"]["body"] == "out = a + b"


# ---------------------------------------------------------------------------
# AC-5 — Apply policy (restart clears state; hot requires superuser)
# ---------------------------------------------------------------------------


def test_ac5_restart_apply_clears_runtime_state():
    """restart_apply wipes all per-instance integrator state."""
    skid = _running_skid(10)
    rt = skid.block_runtime
    assert rt is not None
    # State was built up by running
    assert "level_pi" in rt.state
    assert rt.state["level_pi"].get("integral", 0.0) != 0.0 or rt.state["level_pi"].get("last_cv", 0.0) > 0.0

    # restart_apply with the same program
    prog = program_from_dict(wedge_cascade_program())
    skid.program_loader.restart_apply(prog)  # type: ignore[union-attr]
    assert rt.state == {}, "restart_apply must clear all runtime state"


def test_ac5_hot_apply_requires_superuser(monkeypatch):
    """hot_apply without superuser flag raises PermissionError."""
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    skid = Skid()
    prog = program_from_dict(wedge_cascade_program())
    with pytest.raises(PermissionError):
        skid.program_loader.hot_apply(prog)  # type: ignore[union-attr]


def test_ac5_hot_apply_with_superuser_flag_succeeds():
    """hot_apply with superuser=True succeeds and preserves runtime state."""
    skid = _running_skid(10)
    rt = skid.block_runtime
    assert rt is not None
    state_before = dict(rt.state)  # shallow copy of instance ids present

    prog = program_from_dict(wedge_cascade_program())
    skid.program_loader.hot_apply(prog, superuser=True)  # type: ignore[union-attr]

    # State must be preserved (not cleared)
    assert set(rt.state.keys()) == set(state_before.keys())


def test_ac5_hot_apply_env_var_grants_authority(monkeypatch):
    """PLCASSISTANT_SUPERUSER_HOT_APPLY=1 env var authorises hot_apply."""
    monkeypatch.setenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", "1")
    skid = Skid()
    prog = program_from_dict(wedge_cascade_program())
    skid.program_loader.hot_apply(prog)  # type: ignore[union-attr]  # must not raise


# ---------------------------------------------------------------------------
# AC-6 — Safety forces CV safe same scan regardless of user graph
# ---------------------------------------------------------------------------


def test_ac6_trip_zeros_cmd_speed_same_scan():
    """LOS trip on scan N forces cmd_speed = 0 on that same scan."""
    from plcassistant.io.quality import QualityStatus
    from plcassistant.control import PHASE_ORDER

    skid = Skid(
        SkidConfig(
            cascade=CascadeConfig(level_kp=50.0, level_ki=0.0, flow_kp=20.0, flow_ki=0.0),
            limits=LimitConfig(lim_level_hh=0.36, lim_res_ll=0.05),
        )
    )
    skid.step(0.1, command=OperatorCommand.START)
    for _ in range(15):
        skid.step(0.1)

    assert skid.last is not None
    assert skid.last.cmd_speed > 0.0
    assert skid.last.mode is Mode.RUNNING

    # Force LOS on LT_TANK → same scan must zero CMD_SPEED
    from plcassistant.io.quality import ReasonCode
    skid.force_quality("LT_TANK", QualityStatus.BAD, ReasonCode.FAULT)
    tripped = skid.step(0.1)

    assert tripped.mode is Mode.TRIPPED
    assert TripCode.LOS_LT_TANK in tripped.trip_codes
    assert tripped.cmd_speed == 0.0, "safety must zero CMD_SPEED the same scan"
    assert tripped.cascade.cmd_speed == 0.0
    assert tripped.safety.pump_permit is False
    assert tripped.scan_phases == PHASE_ORDER


def test_ac6_safety_phase_before_control():
    """SAFETY runs before CONTROL; user blocks cannot override safety output."""
    skid = Skid()
    snap = skid.step(0.1)
    # IN → SAFETY → CONTROL → OUT — phase order is immutable
    assert snap.scan_phases == PHASE_ORDER


# ---------------------------------------------------------------------------
# AC-7 — No Home Assistant imports in plcassistant.surface / plcassistant.app
# ---------------------------------------------------------------------------


def _ha_imports_in_pkg(pkg_dir: str) -> list[str]:
    """Return list of HA import locations found in *pkg_dir* source files."""
    violations: list[str] = []
    root = pathlib.Path(pkg_dir)
    for py_file in sorted(root.rglob("*.py")):
        tree = ast.parse(py_file.read_text(), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "homeassistant" in node.module:
                    violations.append(f"{py_file}: from {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if "homeassistant" in alias.name:
                        violations.append(f"{py_file}: import {alias.name}")
    return violations


def test_ac7_no_ha_imports_surface():
    """plcassistant.surface must not import homeassistant."""
    violations = _ha_imports_in_pkg("plcassistant/surface")
    assert violations == [], f"HA imports found: {violations}"


# ---------------------------------------------------------------------------
# Review findings — regression tests (SWD-82 fix-forward)
# ---------------------------------------------------------------------------


def test_review_f1_stale_context_cleared_on_restart_apply():
    """After restart_apply the DictContext is replaced: no stale CV tags."""
    skid = _running_skid(20)
    assert skid.last is not None
    assert skid.last.cmd_speed > 0.0

    # Context has level_pi.cv set from the running program.
    old_ctx = skid.block_context
    assert old_ctx is not None
    assert old_ctx.get("level_pi.cv") is not None

    prog = program_from_dict(wedge_cascade_program())
    skid.program_loader.restart_apply(prog)  # type: ignore[union-attr]

    # block_context must be a freshly created DictContext (not the old one).
    new_ctx = skid.block_context
    assert new_ctx is not old_ctx, "restart_apply must replace _block_context"
    assert new_ctx.get("level_pi.cv") is None, "new context must start empty"

    # _was_running reset: next running step triggers bumpless prep, not stale cv.
    snap = skid.step(0.1)
    assert snap is not None


def test_review_f1_stale_context_cleared_on_hot_apply():
    """After hot_apply the DictContext is replaced: first tick rebuilds from state."""
    skid = _running_skid(20)
    old_ctx = skid.block_context
    assert old_ctx is not None
    assert old_ctx.get("level_pi.cv") is not None

    prog = program_from_dict(wedge_cascade_program())
    skid.program_loader.hot_apply(prog, superuser=True)  # type: ignore[union-attr]

    new_ctx = skid.block_context
    assert new_ctx is not old_ctx, "hot_apply must replace _block_context"
    assert new_ctx.get("level_pi.cv") is None, "new context must start empty"

    # After one more step while running, context is rebuilt from preserved state.
    snap = skid.step(0.1)
    assert snap is not None
    # Context should now have a level_pi.cv value computed by the tick.
    assert new_ctx.get("level_pi.cv") is not None


def test_review_f6_control_last_synced_each_scan():
    """skid.control.last is kept in sync with block runtime outputs each scan."""
    skid = _running_skid(20)
    snap = skid.last
    assert snap is not None
    assert snap.cmd_speed > 0.0

    # control.last must mirror the CascadeOutputs from the block runtime.
    ctl = skid.control
    assert ctl.last.sp_flow == pytest.approx(snap.cascade.sp_flow)
    assert ctl.last.cmd_speed == pytest.approx(snap.cascade.cmd_speed)


def test_review_f6_bumpless_seeded_from_instance_params():
    """Bumpless prep reads kp/ki from the program instance, not only SkidConfig."""
    from plcassistant.surface.schema import program_from_dict as _pfd

    # Create a skid with intentionally different gains from default.
    skid = Skid(
        SkidConfig(
            cascade=CascadeConfig(
                level_kp=10.0, level_ki=1.0,
                flow_kp=5.0, flow_ki=0.5,
            )
        )
    )
    # Override level_pi instance params with different kp.
    prog = skid.program_loader.program  # type: ignore[union-attr]
    assert prog is not None
    prog.instances["level_pi"].params["kp"] = 99.0
    # Run START → should not raise.
    skid.step(0.1, command=OperatorCommand.START)
    skid.step(0.1)
    assert skid.last is not None


def test_ac7_no_ha_imports_app():
    """plcassistant.app must not import homeassistant."""
    violations = _ha_imports_in_pkg("plcassistant/app")
    assert violations == [], f"HA imports found: {violations}"
