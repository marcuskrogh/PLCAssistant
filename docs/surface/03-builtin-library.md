# Built-in Block Library (SWD-115 / SWD-180)

## Overview

The built-in library ships one generic **`PID`** template (`library="builtin"`,
`is_builtin=True`). Placement copies the current library definition onto the
instance (`equation` + `params`); library edits do not rewrite existing
instances.

Shipped templates may be overridden in the App **Library** editor (persist under
JSON `library.shipped_overrides`); **Reset to factory** restores `pid_template()`.
Global **custom** templates live under `library.custom` (`library="custom"`).

Registration: `register_builtins(library, runtime)` registers the PID template
only. Soft-PLC evaluates instance math equations each scan (see
`plcassistant.surface.equations`).

---

## Blocks

### `PID` — Generic PID Controller

Full PID with optional D (`kd`/`td` = 0 → PI). Pins and params:

| Pin | Direction | Type | Default | Notes |
|---|---|---|---|---|
| `pv` | IN | float | 0.0 | Process value |
| `sp` | IN | float | 0.0 | Setpoint |
| `running` | IN | bool | False | When false: reset integral; hold or zero `cv` per `hold_when_stopped` |
| `cv` | OUT | float | 0.0 | Manipulated variable (clamped) |

| Param | Default | Notes |
|---|---|---|
| `kp` | 1.0 | Proportional gain |
| `ki` | 0.0 | Integral gain (1/s) |
| `kd` | 0.0 | Derivative gain |
| `td` | 0.0 | Derivative time (combined with `kd`) |
| `cv_min` / `cv_max` | 0 / 100 | Output clamps |
| `hold_when_stopped` | false | true → hold last `cv` when stopped; false → `cv=0` |

Default math equation: `PID_EQUATION` in `plcassistant.surface.builtin`.

---

## Default tank cascade

The wedge tank program places **two PID copies** at stable instance ids
`level_pi` and `flow_pi` (tags stay stable; template id is `PID`):

- `level_pi`: level loop (`hold_when_stopped=true`, cascade gains)
- `flow_pi`: flow loop (`hold_when_stopped=false`)
- Wire: `level_pi.cv → flow_pi.sp`

Legacy YAML with `template_id: level_pi|flow_pi` is auto-migrated by
`program_from_dict` / `ProjectLoader` to PID copies.

Context tags (unchanged):

| Tag | Role |
|---|---|
| `level_pi.pv` / `.sp` / `.running` | Level PV, SP, permit |
| `flow_pi.pv` / `.running` | Flow PV, permit |
| `level_pi.cv` | Flow setpoint |
| `flow_pi.cv` | Speed command |

---

## App Library editor

Top nav **Library**: list shipped vs custom; edit equation/params; Reset factory
for shipped; create/delete custom. Persist in App JSON `library` (outside the
Soft-PLC project graph).
