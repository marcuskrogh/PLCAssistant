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

### `PID` — ISA-TR5.9 Parallel controller

ISA-TR5.9 **Parallel** form (`form: parallel`) with independent `kp` / `ki` /
`kd`. Bauer hybrid math: incremental when `ki ≠ 0` (clamp anti-windup),
positional + bias `u0` when `ki = 0`. Default two-degree-of-freedom weights
are `beta=1` (P on error) and `gamma=0` (derivative on PV). Required pins stay
`pv`, `sp`, `running`, `cv` so existing wires and tags remain valid. Optional
Bauer pins `uff`, `track`, and `utrack` default safe when unwired.

`running` is the permit/enable pin (wedge Start), not output Manual. Lovelace
Man / Auto / Rem remains a setpoint-source mux outside the function block.

| Pin | Direction | Type | Default | Notes |
|---|---|---|---|---|
| `pv` | IN | float | 0.0 | Process value |
| `sp` | IN | float | 0.0 | Setpoint |
| `running` | IN | bool | False | When false: hold last `cv` or force 0 per `hold_when_stopped` |
| `uff` | IN | float | 0.0 | Feed-forward (inside the clamp) |
| `track` | IN | bool | False | When true, `cv` follows `utrack` |
| `utrack` | IN | float | 0.0 | Tracking target |
| `cv` | OUT | float | 0.0 | Controller output (CO); clamped |

| Param | Default | Notes |
|---|---|---|
| `form` | `parallel` | ISA-TR5.9 algorithm name (Standard/Series later) |
| `kp` | 1.0 | Proportional gain |
| `ki` | 0.0 | Integral gain (1/s). `ki = 0` selects positional form |
| `kd` | 0.0 | Derivative gain |
| `td` | 0.0 | Legacy; unused in Parallel form (kept so old copies load) |
| `beta` | 1.0 | Setpoint weight on P |
| `gamma` | 0.0 | Setpoint weight on D (`0` = D on PV) |
| `u0` | 0.0 | Positional bias when `ki = 0` |
| `direct_acting` | false | Default reverse (`SP − PV`) |
| `cv_min` / `cv_max` | 0 / 100 | Output clamps |
| `hold_when_stopped` | false | true → hold last `cv` when stopped; false → `cv=0` |
| `isa_tag` | `""` | Optional Diagram tag (e.g. LIC, FIC) |

Default math equation: `PID_EQUATION` in `plcassistant.surface.builtin`.
Stock copies that still have the pre-hybrid factory equation are rewritten on
load; custom instance equations are kept, with missing params filled.

---

## Default tank cascade

The wedge tank program places **two PID copies** at stable instance ids
`level_pi` and `flow_pi` (tags stay stable; template id is `PID`):

- `level_pi`: level loop (`hold_when_stopped=true`, cascade gains, `isa_tag=LIC`)
- `flow_pi`: flow loop (`hold_when_stopped=false`, `isa_tag=FIC`)
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
