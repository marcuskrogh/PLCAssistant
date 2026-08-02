# Wedge Skid Migration onto Block Program (SWD-121)

## Summary

The mock skid's **CONTROL phase** now executes the built-in
`wedge_cascade_program()` via `BlockRuntime` instead of calling
`CascadeController.step` directly. The fixed mode/safety shell
(`IN → SAFETY → CONTROL → OUT`) is unchanged.

---

## Architecture

```
Skid.step(dt)
  └─ ScanShell.run(dt, on_in, on_safety, on_control, on_out)
       ├─ IN:      snapshot process measurements
       ├─ SAFETY:  SafetyLayer.evaluate(…)  → SafetyState (unchanged)
       ├─ CONTROL: BlockRuntime.tick(program, context, dt)  ← migrated
       └─ OUT:     safety precedence; process.step(cmd_speed)
```

`BlockRuntime` is the default CONTROL executor.
`CascadeController` remains available as a `Skid.control` attribute for
API compatibility and is used as a fallback when a controller is
explicitly injected via `Skid(control=…)`.

---

## Context Tag Mapping

Each scan the skid applies a declarative **tag↔pin** map
(`TagPinWire` / `wedge_cascade_io_wires()`, SWD-224) before ticking:

| Tag / shell signal | Pin | Dir |
|--------------------|-----|-----|
| `LT_TANK` | `level_pi.pv` | IN |
| `_SHELL.LEVEL_SP` (`skid.sp_level`) | `level_pi.sp` | IN |
| `_SHELL.RUNNING` (`pump_permit`) | `level_pi.running` / `flow_pi.running` | IN |
| `FT_INLET` | `flow_pi.pv` | IN |
| `_SHELL.FLOW_SP_OVERRIDE` (Flow Man/Rem) | `flow_pi.sp` | IN (optional) |
| `level_pi.cv` | `SP_FLOW_AUTO` | OUT |
| `flow_pi.cv` | `CMD_SPEED` | OUT |

Shared helpers `apply_io_wires_in` / `apply_io_wires_out` are the only bridge —
tests cover the format once, not each wire individually.

`flow_pi.sp` is normally wired from `level_pi.cv` inside the program. Flow
Man/Rem uses `prefer_context` on the runtime tick (no `program.wires` mutation).

Faceplate KP/KI update `CascadeConfig` and are **synced into live instance
params** each CONTROL tick so BlockRuntime sees the tuned gains.

---

## Bumpless Start

On the **rising edge** of `pump_permit` (not running → running),
`Skid._prepare_bumpless_blocks` pre-seeds the PI integrators so the
first RUNNING scan matches the held outputs:

- `target_sp_flow` = last `level_pi.cv` output (or 0.0 on first start)
- `target_cmd_speed` = 0.0 (always restart from rest)

This mirrors the `CascadeController.prepare_bumpless` logic exactly and
is implemented via `BlockRuntime.set_instance_state`.

---

## Integrator Reset

When not running (`pump_permit = False`), `running=False` is passed to
each PI block. The built-in callables reset their integrals and hold
(level_pi) or zero (flow_pi) their output — matching the old
`CascadeController.reset_integrators` behaviour.

---

## Public API Changes

### Added to `Skid`

| Property           | Type              | Notes                                       |
|--------------------|-------------------|---------------------------------------------|
| `block_runtime`    | `BlockRuntime`    | Runtime instance (None if fallback path)    |
| `program_loader`   | `ProgramLoader`   | Loader holding active Program (None if fallback) |
| `block_context`    | `DictContext`     | Shared tag context per scan (None if fallback) |

### Preserved (no change)

- `SkidSnapshot` fields: `sp_flow`, `cmd_speed`, `cascade`, `scan_phases`, etc.
- `OperatorCommand` enum
- `Skid.control` attribute (`CascadeController`, kept for compatibility)

### Added to `BlockRuntime`

| Method                              | Notes                                      |
|-------------------------------------|--------------------------------------------|
| `set_instance_state(id, updates)`   | Pre-seed per-instance state (bumpless start) |

---

## Replacing the Program at Runtime

The skid can run any compatible `Program` — not just the default cascade.
Use `skid.program_loader.restart_apply(new_program)` (clears state) or
`skid.program_loader.hot_apply(new_program, superuser=True)` (preserves
state). The program must write `level_pi.cv` and `flow_pi.cv` to the
context for the skid to read `sp_flow` and `cmd_speed`.

```python
from plcassistant.surface import program_from_dict, wedge_cascade_program

skid = Skid()
# Build a modified cascade program and hot-apply it:
new_prog = program_from_dict(wedge_cascade_program(level_kp=60.0))
skid.program_loader.restart_apply(new_prog)
```

---

## See Also

- `docs/surface/02-runtime.md` — block runtime contract
- `docs/surface/03-builtin-library.md` — built-in block library
- `docs/surface/04-apply-policy.md` — restart / hot-apply
- `docs/wedge/03-control-story.md` — updated control story
