# 05 — Mock process requirements

**Tracker:** [SWD-90](https://marcusknielsen.atlassian.net/browse/SWD-90)  
**Parent:** [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Require a **first-class mock / simulated process** for the gravity-drained tank skid — not a one-off test hack. Mock is the delivery bar for SWD-83; the product must keep mocking as a supported path for later examples.

## First-class capability

| Requirement | Detail |
|-------------|--------|
| Selectable mode | Runtime can run against **mock process** or **bound field I/O** without rewriting control/safety logic |
| Same tag contract | Mock publishes/consumes the tags in [`02-io-hmi-contract.md`](02-io-hmi-contract.md) |
| Injectable faults | Operator or test harness can force `*_BAD`, raise/lower levels, and adjust drain/pump curves for scenarios |
| Deterministic enough | Same scenario steps yield the same qualitative outcomes (trips, direction of cascade) |
| HA-visible | Mock PVs/commands appear on the HMI path used for acceptance (entities or add-on state exposed to HA) |

Mocking is a **system requirement** for PLCAssistant: future multi-tank examples should reuse the same mock hosting approach.

## Physics sketch (lumped)

State variables:

- `h_tank` → published as `LT_TANK`
- `h_res` → published as `LT_RES`

Flows (L/min; convert consistently with areas in m² — use liters and dm³ carefully in implementation):

```
q_in   = f_pump(CMD_SPEED, h_res)     # ~ Q_PUMP_MAX * (CMD_SPEED/100) * derate(h_res)
q_drain = K_DRAIN * sqrt(max(h_tank, 0))

dh_tank/dt = (q_in - q_drain) / A_TANK_compat
dh_res/dt  = (q_drain - q_in) / A_RES_compat
```

Constraints:

- Clamp `h_tank ∈ [0, H_TANK_MAX]`, `h_res ∈ [0, H_RES_MAX]`
- Mass conservation: water leaving the tank enters the reservoir and vice versa (closed inventory)
- When `CMD_SPEED = 0`, `q_in = 0` (ignore leakage for v1)
- Optional: mild first-order lag on `FT_INLET` toward `q_in` (e.g. τ ≈ 0.5–1.0 s) so the flow loop has something to do
- Optional: `SC_PUMP` tracks `CMD_SPEED` with small lag/noise

### Suggested defaults

Align with [`01-reference-process.md`](01-reference-process.md):

| Param | Default |
|-------|---------|
| `A_TANK` | 0.05 m² |
| `A_RES` | 0.10 m² |
| `H_TANK_MAX` | 0.40 m |
| `H_RES_MAX` | 0.30 m |
| `Q_PUMP_MAX` | 8.0 L/min |
| `K_DRAIN` | choose so mid-level drain ≈ 2 L/min |
| Initial `h_tank` | 0.15 m |
| Initial `h_res` | 0.20 m |

### Pump derate on low reservoir

Even before `LL_RES` trip, `f_pump` may reduce delivery as `h_res` approaches `LIM_RES_LL` so the mock looks plausible. Trip still owns hard stop.

## Fault injection API (minimum)

Expose via config, service, or test panel:

| Injector | Effect |
|----------|--------|
| `force_LT_TANK_BAD` | Sets `LT_TANK_BAD`; freeze or NaN last PV |
| `force_LT_RES_BAD` | Sets `LT_RES_BAD` |
| `force_FT_INLET_BAD` | Sets `FT_INLET_BAD` |
| `nudge_h_tank` | Add delta to tank level (for HH scenario) |
| `nudge_h_res` | Add delta to reservoir (for LL scenario) |
| `set_K_DRAIN` | Disturbance for cascade demo |

Clearing an injector restores normal quality / physics.

## Timebase

- Simulation step ≤ 100 ms recommended for demo responsiveness
- Control/safety scan may share the add-on loop or run coarser; document chosen rates in packaging notes

## What mock must prove

See [`06-mock-acceptance.md`](06-mock-acceptance.md): Start/Stop, cascade response, HH, LL, each LOS, latch/reset.

## Non-goals

- CFD / 3D hydraulics
- Perfect SI unit purity if documented conversions are consistent
- Emulating every VFD fault code

## Related specs

- Packaging host: [`08-packaging-sketch.md`](08-packaging-sketch.md)
- Physical follow-on: [`07-follow-on.md`](07-follow-on.md)
