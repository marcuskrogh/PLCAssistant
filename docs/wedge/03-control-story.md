# 03 — Control story spec

**Tracker:** [SWD-92](https://marcusknielsen.atlassian.net/browse/SWD-92)  
**Parent:** [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Specify the **automatic cascade** and operating modes for the v1 skid demo: level loop → flow setpoint → flow loop → pump speed. Exact PID/timing semantics are locked in SWD-85 ([`docs/control/`](../control/01-scan-scheduler.md)); this story defines **structure, modes, and observable behavior** for the skid demo.

## Cascade structure

```
  SP_LEVEL ──► [Level PI(D)] ──► SP_FLOW ──► [Flow PI(D)] ──► CMD_SPEED ──► pump
                  ▲                              ▲
               LT_TANK                        FT_INLET
```

| Loop | PV | SP | CV / output | Actuator path |
|------|----|----|-------------|----------------|
| Outer — level | `LT_TANK` | `SP_LEVEL` | `SP_FLOW` (clamped 0 … `SP_FLOW_MAX`) | — |
| Inner — flow | `FT_INLET` | `SP_FLOW` | `CMD_SPEED` (clamped 0 … `CMD_SPEED_MAX`) | VFD / pump |

Rules:

1. When **Running** and cascade enabled, level controller writes `SP_FLOW`.
2. Flow controller tracks `SP_FLOW` by writing `CMD_SPEED`.
3. When not Running, or when safety forces stop: `CMD_SPEED = 0` (and preferably freeze / track to zero cleanly).
4. Optional `SC_PUMP` is **monitoring only** in v1 (no closed speed loop required).

## Operating modes (`MODE`)

| Mode | Meaning | Pump | Cascade |
|------|---------|------|---------|
| `STOP` | Idle; no run request | `CMD_SPEED = 0` | Inactive; hold last SPs on HMI |
| `RUNNING` | Operator started; permissives were OK | Controllers write `CMD_SPEED` | Active (default cascade) |
| `TRIPPED` | Latched safety trip | `CMD_SPEED = 0` | Inactive until Reset → typically `STOP` |

Optional demo extensions (nice-to-have, not required for acceptance):

| Extension | Behavior |
|-----------|----------|
| `RUNNING` + flow-manual | Operator sets `SP_FLOW_MAN`; level loop bypassed; flow loop still tracks |
| `RUNNING` + speed-manual | Operator sets `CMD_SPEED` directly; both loops open — **out of mock acceptance bar** unless explicitly added later |

**v1 acceptance bar** uses: `STOP` ↔ `RUNNING` ↔ `TRIPPED` with full cascade when `RUNNING`.

## Start / Stop behavior (control side)

### Start (`HMI_START`)

Preconditions (must all be true — same as `PERM_OK` from safety):

- Not `TRIP_ACTIVE`
- Required PVs not BAD
- Levels within permissive bands (not already HH / LL)
- `MODE` is `STOP` (not already `RUNNING`)

On success:

1. `MODE ← RUNNING`
2. `RUNNING ← true`
3. Controllers enabled; bumpless preferred (initialize integrals so `CMD_SPEED` does not jump)

On failure: remain `STOP`; HMI may show “Start blocked” via `PERM_OK = false`.

### Stop (`HMI_STOP`)

- **Always** accepted from `RUNNING` (and from any non-tripped run intent).
- `MODE ← STOP`, `RUNNING ← false`, `CMD_SPEED ← 0`.
- Does **not** clear a latched trip (trip stays `TRIPPED` until Reset).

## Cascade behavioral requirements (demo)

| Scenario | Expected |
|----------|----------|
| Step up `SP_LEVEL` while `RUNNING` | `SP_FLOW` rises (within clamp); `CMD_SPEED` rises; `FT_INLET` tracks; `LT_TANK` moves toward SP |
| Step down `SP_LEVEL` | Opposite; tank drains via gravity while pump slows |
| Disturbance: increase drain (mock knob) | Level drops; cascade increases flow/speed to recover |
| Enter `STOP` | Speed → 0; tank drains toward equilibrium with pump off |

Quantitative tuning targets use demo-grade defaults; formal FB contract (sample time = scan `dt`, clamps, anti-windup, bumpless Start) is locked in [`docs/control/02-fb-pid.md`](../control/02-fb-pid.md). For mock acceptance, require **directionally correct** response within a few mock time-constants (see mock acceptance).

## Anti-windup / clamps (minimum)

- Clamp `SP_FLOW` to `[0, SP_FLOW_MAX]`
- Clamp `CMD_SPEED` to `[0, CMD_SPEED_MAX]`
- When `CMD_SPEED` saturated or not `RUNNING`, level/flow integrators must not wind unboundedly (**conditional integration** — [`docs/control/02-fb-pid.md`](../control/02-fb-pid.md))

## Scan & safety precedence

- Scan order: IN → SAFETY → CONTROL → OUT ([`docs/control/01-scan-scheduler.md`](../control/01-scan-scheduler.md))
- Safety before control so trips force CV=0 the **same** scan ([`docs/control/03-safety-precedence.md`](../control/03-safety-precedence.md))

## Out of this control story

- Multi-tank coordination
- Valve split-range
- Full ISA-88 batch sequencing
- Certified motion / drive profiles

## Implementation note (SWD-121)

As of SWD-82 the **CONTROL phase executes the block surface**
(`BlockRuntime` + `wedge_cascade_program`) instead of a
`CascadeController` directly. The cascade structure, mode/safety shell,
bumpless Start, and all behavioral requirements above are unchanged —
they are now fulfilled by the `level_pi` and `flow_pi` built-in blocks.

See [`docs/surface/06-wedge-migration.md`](../surface/06-wedge-migration.md)
for the full migration note and context-tag mapping.

## Related specs

- Tags: [`02-io-hmi-contract.md`](02-io-hmi-contract.md)
- Permissives & trips: [`04-safety-story.md`](04-safety-story.md)
- Acceptance: [`06-mock-acceptance.md`](06-mock-acceptance.md)
- Control semantics (SWD-85): [`docs/control/`](../control/01-scan-scheduler.md)
- Block surface migration (SWD-121): [`docs/surface/06-wedge-migration.md`](../surface/06-wedge-migration.md)
