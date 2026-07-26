# 01 — Reference process spec

**Tracker:** [SWD-88](https://marcusknielsen.atlassian.net/browse/SWD-88)  
**Parent:** [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Define the **v1 lab / hobby skid** as a single, implementable process narrative: one process tank, one reservoir, recycled water, pump-only actuation, gravity drain. Later multi-tank examples must remain possible; this doc does not constrain them beyond “out of v1.”

## Process narrative

Closed recycled loop:

1. Water sits in the **reservoir**.
2. A **variable-speed inlet pump** (VFD or equivalent) lifts water from the reservoir into the **process tank**.
3. The process tank drains by **gravity** through a fixed (non-actuated) outlet path back to the reservoir.
4. No outlet pump and no control valve in v1 — the only continuous actuator is pump speed.

```
  ┌─────────────┐     CMD_SPEED / SC_PUMP      ┌──────────────┐
  │  Reservoir  │ ──► VFD + inlet pump ──────► │ Process tank │
  │   LT_RES    │         FT_INLET             │   LT_TANK    │
  └──────▲──────┘                              └──────┬───────┘
         │         gravity drain (fixed Cv)           │
         └────────────────────────────────────────────┘
```

## Equipment boundaries

| Item | In v1 | Notes |
|------|-------|-------|
| Process tank | Yes | Single volume; level measured as `LT_TANK` |
| Reservoir | Yes | Supply / return sump; level measured as `LT_RES` |
| Inlet pump + variable speed drive | Yes | Command `CMD_SPEED`; optional feedback `SC_PUMP` |
| Inlet flow sensor | Yes | Volumetric flow `FT_INLET` |
| Gravity drain path | Yes | Fixed hydraulic resistance (orifice / hose / valve locked open) |
| Outlet pump | **No** | Deferred |
| Modulating control valve | **No** | Deferred (four-tank / split-valve later) |
| Second process tank | **No** | Deferred (two-tank later) |

## Inventory / capacity (design defaults for mock & physical)

These are **reference defaults** for mock physics and later BOM sizing — not hard product limits.

| Parameter | Symbol | Default | Unit |
|-----------|--------|---------|------|
| Process tank cross-section | `A_TANK` | 0.05 | m² |
| Process tank max height | `H_TANK_MAX` | 0.40 | m |
| Reservoir cross-section | `A_RES` | 0.10 | m² |
| Reservoir max height | `H_RES_MAX` | 0.30 | m |
| Gravity drain coefficient | `K_DRAIN` | tuned so idle drain ~ 1–3 L/min at mid level | L/min per √m |
| Pump max delivery | `Q_PUMP_MAX` | 8.0 | L/min at `CMD_SPEED = 100%` |
| Nominal level span | — | 0 … `H_TANK_MAX` | m |

Levels may be exposed to operators as **meters** or **% of span**; internal control should use a consistent engineering unit (prefer m) with a documented span for %-display.

## Operating intent

- Hold **process tank level** near `SP_LEVEL` by cascading to an inlet **flow setpoint**, then to **pump speed**.
- Protect the pump and tank via the safety story (high tank, low reservoir, loss-of-signal).
- Operator runs the skid from HMI: Start / Stop / Reset / setpoints / live measurements.

## What “success” looks like on this skid

1. Mock (this Task): operator Start/Stop; cascade tracks level & flow; each required trip latches and needs reset.
2. Physical (follow-on): same behaviors on wired sensors/actuators — required for overall product success, not this Task’s done bar.

## Explicit non-goals (this example)

- Treating the home as the process plant
- Two-tank cascade or interacting tanks
- Four-tank / split-valve demonstrations
- SIL-rated safety architecture

## Related specs

- I/O tags: [`02-io-hmi-contract.md`](02-io-hmi-contract.md)
- Cascade behavior: [`03-control-story.md`](03-control-story.md)
- Trips: [`04-safety-story.md`](04-safety-story.md)
- Mock physics: [`05-mock-process.md`](05-mock-process.md)
