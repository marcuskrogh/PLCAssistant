# Built-in Block Library (SWD-115)

## Overview

The built-in library ships read-only `BlockTemplate` objects and native
Python callables registered in a `TemplateLibrary`. Blocks in this library
carry `library="builtin"` and `is_builtin=True`; they cannot be edited
in-place.

Registration happens at startup via `register_builtins(library, runtime)`.

---

## Blocks

### `level_pi` — Level PI Controller

Outer loop of the wedge cascade. Compares measured level (`pv`) to a level
setpoint (`sp`) and outputs a flow setpoint (`cv`).

| Pin | Direction | Type | Default | Notes |
|---|---|---|---|---|
| `pv` | IN | float | 0.0 | Measured tank level (m) |
| `sp` | IN | float | 0.0 | Level setpoint (m) |
| `running` | IN | bool | False | Pump permit; false → hold `cv`, reset integral |
| `cv` | OUT | float | — | Flow setpoint (L/min, clamped to `[cv_min, cv_max]`) |

| Param | Default | Notes |
|---|---|---|
| `kp` | 40.0 | Proportional gain (L/min per m error) |
| `ki` | 5.0 | Integral gain (1/s) |
| `cv_min` | 0.0 | Lower clamp for output (L/min) |
| `cv_max` | 6.0 | Upper clamp for output (L/min) |

**Behaviour:**

- `running=True`: PI step with conditional anti-windup (same gains/clamps as
  `CascadeController` defaults).
- `running=False`: reset integral, hold last `cv`, bumpless flag cleared.
- State: `integral` (float), `last_cv` (float), `bumpless_pending` (bool).

---

### `flow_pi` — Flow PI Controller

Inner loop of the wedge cascade. Compares measured flow (`pv`) to a flow
setpoint (`sp`, normally wired from `level_pi.cv`) and outputs a speed
command (`cv`).

| Pin | Direction | Type | Default | Notes |
|---|---|---|---|---|
| `pv` | IN | float | 0.0 | Measured flow (L/min) |
| `sp` | IN | float | 0.0 | Flow setpoint (L/min) |
| `running` | IN | bool | False | Pump permit; false → force `cv = 0`, reset integral |
| `cv` | OUT | float | — | Speed command (%, clamped to `[cv_min, cv_max]`) |

| Param | Default | Notes |
|---|---|---|
| `kp` | 12.0 | Proportional gain (% per L/min error) |
| `ki` | 2.0 | Integral gain (1/s) |
| `cv_min` | 0.0 | Lower clamp (%) |
| `cv_max` | 100.0 | Upper clamp (%) |

**Behaviour:**

- `running=True`: PI step with conditional anti-windup.
- `running=False`: reset integral, output `cv = 0.0` (pump off).
- State: `integral` (float), `last_cv` (float).

---

## PI math (shared)

Both blocks use `_pi_step`:

```
error     = sp - pv
raw_cv    = kp * error + ki * (integral + error * dt)
cv        = clamp(raw_cv, cv_min, cv_max)
```

**Conditional anti-windup:** update integral only when output is not
saturated in the same direction as the error:

```python
if cv == raw_cv or (
    (raw_cv > cv_max and error <= 0)
    or (raw_cv < cv_min and error >= 0)
):
    integral += error * dt
```

This matches `CascadeController` exactly and enables cascade parity tests.

---

## Registration

```python
from plcassistant.surface.model import TemplateLibrary
from plcassistant.surface.runtime import BlockRuntime
from plcassistant.surface.builtin import register_builtins

library = TemplateLibrary()
runtime = BlockRuntime(library)
register_builtins(library, runtime)
```

---

## Cascade program factory

`wedge_cascade_program(**gains)` returns a YAML-shaped `dict` (passable to
`program_from_dict`) wiring `level_pi.cv → flow_pi.sp`:

```yaml
version: "1.0"
instances:
  level_pi:
    template_id: level_pi
    library: builtin
    params: {kp: 40.0, ki: 5.0, cv_min: 0.0, cv_max: 6.0}
  flow_pi:
    template_id: flow_pi
    library: builtin
    params: {kp: 12.0, ki: 2.0, cv_min: 0.0, cv_max: 100.0}
wires:
  - {src_instance: level_pi, src_pin: cv,
     dst_instance: flow_pi,  dst_pin: sp}
execution_order: [level_pi, flow_pi]
```

Context tags consumed each tick:

| Tag | Meaning |
|---|---|
| `level_pi.pv` | Measured tank level (LT_TANK) |
| `level_pi.sp` | Level setpoint (SP_LEVEL) |
| `level_pi.running` | Pump permit |
| `flow_pi.pv` | Measured inlet flow (FT_INLET) |
| `flow_pi.running` | Pump permit (same signal, set by caller) |

Context tags written each tick:

| Tag | Meaning |
|---|---|
| `level_pi.cv` | Flow setpoint (SP_FLOW) |
| `flow_pi.cv` | Speed command (CMD_SPEED) |

---

## Cascade parity

For the same gains and inputs, one `tick` of `[level_pi → flow_pi]` produces
numerically identical outputs to one `CascadeController.step()` call.
This is verified in `tests/test_surface_builtin.py`.

---

## Seams

| Future package | How it uses the library |
|---|---|
| SWD-116 Runtime | Calls `register_builtins` at startup; routes callables per template_id. |
| SWD-121 Skid migration | Replaces `CascadeController.step()` with `runtime.tick` on cascade program. |
| SWD-115 extension | Additional stock blocks (PID, On/Off, ramp) registered the same way. |
