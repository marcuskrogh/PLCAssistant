# SWD-82 Acceptance Checklist

Mirrors the acceptance criteria in [`docs/PLAN.md`](../PLAN.md).  
Test file: `tests/test_swd82_acceptance.py`.

---

## Criteria

### AC-1 — Mock skid runnable as block program under fixed safety shell

- [ ] `Skid()` initialises with `BlockRuntime` + `wedge_cascade_program` by default.
- [ ] Scan phase order is `IN → SAFETY → CONTROL → OUT` (unchanged).
- [ ] Running the skid for N scans produces positive `sp_flow` and `cmd_speed`.
- [ ] `SkidSnapshot.scan_phases == PHASE_ORDER` every scan.

### AC-2 — Copy-on-place independence and reset-to-library

- [ ] `place_block(template, id)` returns a new `BlockInstance` with a deep copy of params.
- [ ] Mutating the placed instance's params does **not** affect the originating template.
- [ ] `reset_instance(instance, template)` restores params to template defaults.
- [ ] Mutating the reset instance does **not** affect the template.

### AC-3 — Custom user Python block place + run in CONTROL

- [ ] `make_user_template` creates a `BlockTemplate` with a Python body.
- [ ] The template can be embedded in a `Program` via `add_user_template` or `program_from_dict`.
- [ ] The program (including the custom block) is loaded via `ProgramLoader.restart_apply`.
- [ ] After a scan tick the custom block's output pin is written to the context.

### AC-4 — YAML-shaped program dict round-trip

- [ ] `program_from_dict(wedge_cascade_program())` parses without error.
- [ ] `program_to_dict(program_from_dict(d))` re-serialises to a structurally equivalent dict.

### AC-5 — Apply policy

- [ ] `ProgramLoader.restart_apply(program)` clears all `BlockRuntime` state.
- [ ] After `restart_apply`, `runtime.state` is empty (integrals cleared).
- [ ] `ProgramLoader.hot_apply(program)` without superuser raises `PermissionError`.
- [ ] `ProgramLoader.hot_apply(program, superuser=True)` succeeds and preserves state.

### AC-6 — Safety forces CV safe regardless of user graph

- [ ] A LOS trip (e.g. force LT_TANK BAD) on scan N sets `cmd_speed = 0` on **the same** scan N.
- [ ] `SkidSnapshot.cascade.cmd_speed == 0` and `SkidSnapshot.cmd_speed == 0` when tripped.
- [ ] The safety/mode shell runs in `SAFETY` phase **before** `CONTROL`; user blocks cannot override.

### AC-7 — No Home Assistant imports

- [ ] `plcassistant.surface` package files contain no `import homeassistant` or `from homeassistant` statements.
- [ ] `plcassistant.app` package files contain no `import homeassistant` or `from homeassistant` statements.

---

## Test commands

```bash
# Full suite (must stay green)
python3 -m pytest -q

# SWD-82 acceptance only
python3 -m pytest tests/test_swd82_acceptance.py -v
```
