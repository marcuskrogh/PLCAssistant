"""Built-in block library for the wedge cascade (SWD-115 / SWD-180 / SWD-360).

Registers one generic ``PID`` template.  The default tank program places two
PID copies (kept at instance ids ``level_pi`` and ``flow_pi`` for stable tags).

The factory equation is ISA-TR5.9 Parallel form with Bauer hybrid updates:
incremental when ``ki != 0`` (clamp anti-windup), positional + ``u0`` when
``ki = 0``. Default derivative on PV (``gamma = 0``). Required pins stay
``pv`` / ``sp`` / ``running`` / ``cv``.

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
from plcassistant.surface.runtime import BlockRuntime


PID_TEMPLATE_ID = "PID"

# Cascade wedge instance ids and CV limits (SWD-250).
CASCADE_LEVEL_INSTANCE_ID = "level_pi"
CASCADE_FLOW_INSTANCE_ID = "flow_pi"
CASCADE_SP_FLOW_MIN = 0.0
# Matches default plant ``q_pump_max`` (L/min). Soft-PLC repair may override
# from the HA-config plant capacity bridge when the model changes (SWD-251).
CASCADE_SP_FLOW_MAX = 8.0
CASCADE_CMD_SPEED_MIN = 0.0
CASCADE_CMD_SPEED_MAX = 100.0


# Pre-SWD-360 factory equation (positional + conditional integration).
# Kept so program migration can recognise stock copies and rewrite them.
PID_EQUATION_LEGACY = """# Generic PID; PI when kd = td = 0.
running_flag = bool(running)
prev_integral = state("integral", 0.0)
integral = 0.0 if not running_flag else prev_integral
bumpless_pending = False if not running_flag else bool(state("bumpless_pending", False))
last_cv = state("last_cv", 0.0)
error = sp - pv
p_term = kp * error
tentative_i = integral if bumpless_pending else integral + error * dt
derivative = 0.0 if dt <= 0.0 else (error - state("last_error", error)) / dt
raw_cv = p_term + ki * tentative_i + (kd + kp * td) * derivative
clamped_cv = clamp(raw_cv, cv_min, cv_max)
stopped_cv = last_cv if hold_when_stopped else 0.0
cv = clamped_cv if running_flag else stopped_cv
can_integrate = running_flag and (clamped_cv == raw_cv or ((raw_cv > cv_max and error <= 0.0) or (raw_cv < cv_min and error >= 0.0)))
integral = tentative_i if can_integrate else integral
bumpless_pending = False
last_error = error if running_flag else state("last_error", error)
last_cv = cv
"""

# ISA-TR5.9 Parallel + Bauer hybrid (incremental when ki != 0).
# td is retained for compatibility and is unused (Parallel uses kd only).
PID_EQUATION = """# ISA-TR5.9 Parallel; Bauer hybrid incremental/positional.
dir_sign = -1.0 if bool(direct_acting) else 1.0
dt_ok = bool(dt > 0.0)
ep = dir_sign * (beta * sp - pv)
ei = dir_sign * (sp - pv)
yd = gamma * sp - pv
last_ep = state("last_ep", 0.0)
last_yd = state("last_yd", yd)
last_uff = state("last_uff", uff)
last_cv = state("last_cv", u0)
pending = bool(state("bumpless_pending", False))
dt_safe = dt if dt_ok else 1.0
dup = kp * (ep - last_ep)
dui = ki * ei * dt if dt_ok and (not pending) else 0.0
dud = kd * dir_sign * (yd - last_yd) / dt_safe if dt_ok else 0.0
duff = uff - last_uff
use_inc = bool((ki > 0.0) or (ki < 0.0))
raw_inc = last_cv + dup + dui + dud + duff
raw_pos = u0 + kp * ep + dud + uff
raw = raw_inc if use_inc else raw_pos
clamped = clamp(raw, cv_min, cv_max)
tracked = clamp(utrack, cv_min, cv_max)
cv_run = tracked if bool(track) else clamped
cv_stop = last_cv if bool(hold_when_stopped) else 0.0
cv = cv_run if bool(running) else cv_stop
bumpless_pending = False
last_ep = ep
last_yd = yd
last_uff = uff
last_cv = cv
"""


def is_factory_pid_equation(equation: str) -> bool:
    """Return True when *equation* is empty or a known factory PID body."""
    text = str(equation or "").strip()
    if not text:
        return True
    known = {PID_EQUATION.strip(), PID_EQUATION_LEGACY.strip()}
    return text in known


# ---------------------------------------------------------------------------
# Shared helpers (removed native PI callables — equation-driven PID only)
# ---------------------------------------------------------------------------


def pid_template() -> BlockTemplate:
    """Return a fresh factory PID template."""
    return BlockTemplate(
        template_id=PID_TEMPLATE_ID,
        library="builtin",
        description=(
            "PID controller (ISA-TR5.9 Parallel). Hybrid incremental/positional; "
            "set kd=0 for PI. Derivative on PV by default (gamma=0)."
        ),
        pins=[
            PinSpec("pv", PinDirection.IN, "float", 0.0),
            PinSpec("sp", PinDirection.IN, "float", 0.0),
            PinSpec("running", PinDirection.IN, "bool", False),
            PinSpec("uff", PinDirection.IN, "float", 0.0),
            PinSpec("track", PinDirection.IN, "bool", False),
            PinSpec("utrack", PinDirection.IN, "float", 0.0),
            PinSpec("cv", PinDirection.OUT, "float", 0.0),
        ],
        params=pid_default_params(),
        body=PID_EQUATION,
        is_builtin=True,
    )


def pid_default_params() -> dict[str, Any]:
    """Generic PID defaults used for new placements."""
    return {
        "form": "parallel",
        "kp": 1.0,
        "ki": 0.0,
        "kd": 0.0,
        "td": 0.0,
        "beta": 1.0,
        "gamma": 0.0,
        "u0": 0.0,
        "direct_acting": False,
        "cv_min": 0.0,
        "cv_max": 100.0,
        "hold_when_stopped": False,
        "isa_tag": "",
    }


def cascade_pid_cv_limits(
    instance_id: str,
    *,
    sp_flow_max: float | None = None,
) -> tuple[float, float] | None:
    """Return ``(cv_min, cv_max)`` for wedge cascade PI roles, or ``None``.

    Level CV is flow SP (L/min); pass ``sp_flow_max`` to track plant
    ``q_pump_max``. Flow CV is always CMD_SPEED % (0–100).
    """
    if instance_id == CASCADE_LEVEL_INSTANCE_ID:
        max_flow = CASCADE_SP_FLOW_MAX if sp_flow_max is None else float(sp_flow_max)
        return CASCADE_SP_FLOW_MIN, max_flow
    if instance_id == CASCADE_FLOW_INSTANCE_ID:
        return CASCADE_CMD_SPEED_MIN, CASCADE_CMD_SPEED_MAX
    return None


def pid_params_for_pi(
    *,
    kp: float,
    ki: float,
    cv_min: float,
    cv_max: float,
    hold_when_stopped: bool,
) -> dict[str, Any]:
    """Return PID params that reproduce the prior PI controller behavior."""
    params = pid_default_params()
    params.update(
        {
            "kp": kp,
            "ki": ki,
            "kd": 0.0,
            "td": 0.0,
            "cv_min": cv_min,
            "cv_max": cv_max,
            "hold_when_stopped": hold_when_stopped,
        }
    )
    return params


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
    del runtime  # PID is equation-driven; no native callable is required.
    library.register(pid_template())


# ---------------------------------------------------------------------------
# Cascade program factory
# ---------------------------------------------------------------------------


def wedge_cascade_program(
    *,
    level_kp: float = 40.0,
    level_ki: float = 5.0,
    flow_kp: float = 12.0,
    flow_ki: float = 2.0,
    sp_flow_min: float = CASCADE_SP_FLOW_MIN,
    sp_flow_max: float = CASCADE_SP_FLOW_MAX,
    cmd_speed_min: float = CASCADE_CMD_SPEED_MIN,
    cmd_speed_max: float = CASCADE_CMD_SPEED_MAX,
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
                "template_id": PID_TEMPLATE_ID,
                "library": "builtin",
                "params": {
                    **pid_params_for_pi(
                        kp=level_kp,
                        ki=level_ki,
                        cv_min=sp_flow_min,
                        cv_max=sp_flow_max,
                        hold_when_stopped=True,
                    ),
                    "isa_tag": "LIC",
                },
                "equation": PID_EQUATION,
                "x": 60.0,
                "y": 80.0,
            },
            "flow_pi": {
                "template_id": PID_TEMPLATE_ID,
                "library": "builtin",
                "params": {
                    **pid_params_for_pi(
                        kp=flow_kp,
                        ki=flow_ki,
                        cv_min=cmd_speed_min,
                        cv_max=cmd_speed_max,
                        hold_when_stopped=False,
                    ),
                    "isa_tag": "FIC",
                },
                "equation": PID_EQUATION,
                "x": 280.0,
                "y": 80.0,
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
        "datablocks": ["DB_Tank"],
    }


def wedge_softplc_project(
    *,
    level_kp: float = 40.0,
    level_ki: float = 5.0,
    flow_kp: float = 12.0,
    flow_ki: float = 2.0,
    sp_flow_min: float = CASCADE_SP_FLOW_MIN,
    sp_flow_max: float = CASCADE_SP_FLOW_MAX,
    cmd_speed_min: float = CASCADE_CMD_SPEED_MIN,
    cmd_speed_max: float = CASCADE_CMD_SPEED_MAX,
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
    "CASCADE_CMD_SPEED_MAX",
    "CASCADE_CMD_SPEED_MIN",
    "CASCADE_FLOW_INSTANCE_ID",
    "CASCADE_LEVEL_INSTANCE_ID",
    "CASCADE_SP_FLOW_MAX",
    "CASCADE_SP_FLOW_MIN",
    "PID_EQUATION",
    "PID_EQUATION_LEGACY",
    "PID_TEMPLATE_ID",
    "cascade_pid_cv_limits",
    "is_factory_pid_equation",
    "pid_default_params",
    "pid_params_for_pi",
    "pid_template",
    "register_builtins",
    "wedge_cascade_program",
    "wedge_softplc_project",
]
