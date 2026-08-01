"""Built-in block library for the wedge cascade (SWD-115).

Registers ``level_pi`` and ``flow_pi`` templates and callables.
Provides ``wedge_cascade_program()`` factory for the default cascade program.

PI math mirrors ``CascadeController`` gains, clamps, and anti-windup so that
a wired ``[level_pi → flow_pi]`` program is numerically equivalent to one
``CascadeController.step()`` for the same inputs and gains.

No Home Assistant dependency; no hard-wired Skid.
"""

from __future__ import annotations

from typing import Any

from plcassistant.surface.model import (
    BlockTemplate,
    PinDirection,
    PinSpec,
    TemplateLibrary,
)
from plcassistant.surface.runtime import BlockCallable, BlockRuntime


# ---------------------------------------------------------------------------
# Shared PI helpers
# ---------------------------------------------------------------------------


def _clamp(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return float(value)


def _pi_step(
    pv: float,
    sp: float,
    kp: float,
    ki: float,
    cv_min: float,
    cv_max: float,
    state: dict,
    dt: float,
) -> float:
    """One PI step with conditional anti-windup.

    State keys consumed/updated:
        ``integral``       — accumulated integral term (float, default 0.0)
        ``bumpless_pending`` — skip I advance on this scan (bool, default False)

    Returns the clamped CV.  Updates ``state`` in-place.
    """
    integral: float = state.get("integral", 0.0)
    bumpless_pending: bool = state.get("bumpless_pending", False)

    error = sp - pv
    raw_p = kp * error
    if bumpless_pending:
        tentative_i = integral
    else:
        tentative_i = integral + error * dt

    raw_cv = raw_p + ki * tentative_i
    cv = _clamp(raw_cv, cv_min, cv_max)

    # Conditional anti-windup: accumulate only when not pushing further into
    # saturation (matches CascadeController exactly).
    if cv == raw_cv or (
        (raw_cv > cv_max and error <= 0) or (raw_cv < cv_min and error >= 0)
    ):
        state["integral"] = tentative_i

    state["bumpless_pending"] = False
    return cv


# ---------------------------------------------------------------------------
# LevelPI callable
# ---------------------------------------------------------------------------


def _level_pi_fn(
    pins: dict[str, Any],
    params: dict[str, Any],
    state: dict,
    dt: float,
) -> dict[str, Any]:
    """Level PI controller callable.

    Not running → reset integral, hold last ``cv`` (preserves SP_FLOW).
    Running     → PI step with conditional anti-windup.
    """
    running: bool = bool(pins.get("running", False))
    pv: float = float(pins.get("pv", 0.0))
    sp: float = float(pins.get("sp", 0.0))

    kp: float = float(params.get("kp", 40.0))
    ki: float = float(params.get("ki", 5.0))
    cv_min: float = float(params.get("cv_min", 0.0))
    cv_max: float = float(params.get("cv_max", 6.0))

    last_cv: float = state.get("last_cv", 0.0)

    if not running:
        state["integral"] = 0.0
        state["bumpless_pending"] = False
        return {"cv": last_cv}

    cv = _pi_step(pv, sp, kp, ki, cv_min, cv_max, state, dt)
    state["last_cv"] = cv
    return {"cv": cv}


# ---------------------------------------------------------------------------
# FlowPI callable
# ---------------------------------------------------------------------------


def _flow_pi_fn(
    pins: dict[str, Any],
    params: dict[str, Any],
    state: dict,
    dt: float,
) -> dict[str, Any]:
    """Flow PI controller callable.

    Not running → reset integral, force ``cv = 0`` (CMD_SPEED = 0).
    Running     → PI step with conditional anti-windup.
    """
    running: bool = bool(pins.get("running", False))
    pv: float = float(pins.get("pv", 0.0))
    sp: float = float(pins.get("sp", 0.0))

    kp: float = float(params.get("kp", 12.0))
    ki: float = float(params.get("ki", 2.0))
    cv_min: float = float(params.get("cv_min", 0.0))
    cv_max: float = float(params.get("cv_max", 100.0))

    if not running:
        state["integral"] = 0.0
        state["bumpless_pending"] = False
        state["last_cv"] = 0.0
        return {"cv": 0.0}

    cv = _pi_step(pv, sp, kp, ki, cv_min, cv_max, state, dt)
    state["last_cv"] = cv
    return {"cv": cv}


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------


_LEVEL_PI_TEMPLATE = BlockTemplate(
    template_id="level_pi",
    library="builtin",
    description=(
        "Level PI controller — outer loop of the wedge cascade. "
        "Compares measured level (pv) to setpoint (sp) and outputs "
        "a flow setpoint (cv)."
    ),
    pins=[
        PinSpec("pv", PinDirection.IN, "float", 0.0),
        PinSpec("sp", PinDirection.IN, "float", 0.0),
        PinSpec("running", PinDirection.IN, "bool", False),
        PinSpec("cv", PinDirection.OUT, "float"),
    ],
    params={
        "kp": 40.0,
        "ki": 5.0,
        "cv_min": 0.0,
        "cv_max": 6.0,
    },
    body="",
    is_builtin=True,
)

_FLOW_PI_TEMPLATE = BlockTemplate(
    template_id="flow_pi",
    library="builtin",
    description=(
        "Flow PI controller — inner loop of the wedge cascade. "
        "Compares measured flow (pv) to flow setpoint (sp, normally wired "
        "from level_pi.cv) and outputs a speed command (cv)."
    ),
    pins=[
        PinSpec("pv", PinDirection.IN, "float", 0.0),
        PinSpec("sp", PinDirection.IN, "float", 0.0),
        PinSpec("running", PinDirection.IN, "bool", False),
        PinSpec("cv", PinDirection.OUT, "float"),
    ],
    params={
        "kp": 12.0,
        "ki": 2.0,
        "cv_min": 0.0,
        "cv_max": 100.0,
    },
    body="",
    is_builtin=True,
)


# ---------------------------------------------------------------------------
# Public registration entry-point
# ---------------------------------------------------------------------------


def register_builtins(library: TemplateLibrary, runtime: BlockRuntime) -> None:
    """Register all built-in templates and callables.

    Call once at startup before any ``runtime.tick()``::

        library = TemplateLibrary()
        runtime = BlockRuntime(library)
        register_builtins(library, runtime)
    """
    library.register(_LEVEL_PI_TEMPLATE)
    library.register(_FLOW_PI_TEMPLATE)

    runtime.register_callable("builtin", "level_pi", _level_pi_fn)
    runtime.register_callable("builtin", "flow_pi", _flow_pi_fn)


# ---------------------------------------------------------------------------
# Cascade program factory
# ---------------------------------------------------------------------------


def wedge_cascade_program(
    *,
    level_kp: float = 40.0,
    level_ki: float = 5.0,
    flow_kp: float = 12.0,
    flow_ki: float = 2.0,
    sp_flow_min: float = 0.0,
    sp_flow_max: float = 6.0,
    cmd_speed_min: float = 0.0,
    cmd_speed_max: float = 100.0,
) -> dict:
    """Return a YAML-shaped dict for the default Level→Flow cascade program.

    Load with ``program_from_dict(wedge_cascade_program())`` after calling
    ``register_builtins``.

    Context tags consumed each tick:

    * ``level_pi.pv``     — measured tank level  (map from LT_TANK)
    * ``level_pi.sp``     — level setpoint        (map from SP_LEVEL)
    * ``level_pi.running``— pump permit
    * ``flow_pi.pv``      — measured inlet flow   (map from FT_INLET)
    * ``flow_pi.running`` — pump permit (same signal)

    Context tags written each tick:

    * ``level_pi.cv``  — flow setpoint   (SP_FLOW)
    * ``flow_pi.cv``   — speed command   (CMD_SPEED)
    """
    return {
        "version": "1.0",
        "name": "Tank",
        "description": "Default tank level-flow cascade program.",
        "instances": {
            "level_pi": {
                "template_id": "level_pi",
                "library": "builtin",
                "params": {
                    "kp": level_kp,
                    "ki": level_ki,
                    "cv_min": sp_flow_min,
                    "cv_max": sp_flow_max,
                },
            },
            "flow_pi": {
                "template_id": "flow_pi",
                "library": "builtin",
                "params": {
                    "kp": flow_kp,
                    "ki": flow_ki,
                    "cv_min": cmd_speed_min,
                    "cv_max": cmd_speed_max,
                },
            },
        },
        "wires": [
            {
                "src_instance": "level_pi",
                "src_pin": "cv",
                "dst_instance": "flow_pi",
                "dst_pin": "sp",
            }
        ],
        "execution_order": ["level_pi", "flow_pi"],
    }


def wedge_softplc_project(
    *,
    level_kp: float = 40.0,
    level_ki: float = 5.0,
    flow_kp: float = 12.0,
    flow_ki: float = 2.0,
    sp_flow_min: float = 0.0,
    sp_flow_max: float = 6.0,
    cmd_speed_min: float = 0.0,
    cmd_speed_max: float = 100.0,
    scan_period_s: float = 0.1,
    program_id: str = "tank",
    task_id: str = "main",
) -> dict:
    """Return a YAML-shaped Soft-PLC project with one tank Program under Main Task."""
    from plcassistant.surface.model import DEFAULT_WEDGE_PROGRAM_ID, MAIN_TASK_ID

    pid = program_id or DEFAULT_WEDGE_PROGRAM_ID
    tid = task_id or MAIN_TASK_ID
    return {
        "version": "2.0",
        "scan_period_s": scan_period_s,
        "programs": {
            pid: wedge_cascade_program(
                level_kp=level_kp,
                level_ki=level_ki,
                flow_kp=flow_kp,
                flow_ki=flow_ki,
                sp_flow_min=sp_flow_min,
                sp_flow_max=sp_flow_max,
                cmd_speed_min=cmd_speed_min,
                cmd_speed_max=cmd_speed_max,
            ),
        },
        "tasks": [{"id": tid, "priority": 1, "programs": [pid]}],
    }


__all__ = [
    "register_builtins",
    "wedge_cascade_program",
    "wedge_softplc_project",
]
