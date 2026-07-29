# 05 — Mock process requirements

**Tracker:** [SWD-90](https://marcusknielsen.atlassian.net/browse/SWD-90)  
**Parent:** [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Require a **first-class mock / simulated process** for the gravity-drained tank skid — not a one-off test hack. Mock is the delivery bar for SWD-83; the product must keep mocking as a supported path for later examples.

## Two layers of “mock” (do not conflate)

| Layer | Owner | Role |
|-------|--------|------|
| **Entity mock + stand-alone simulator (SWD-145 / SWD-146)** | Thin HA integration | Synthesizes HA entity values/quality and (from SWD-146) runs configurable plant dynamics; bindings feed Soft-PLC via MQTT like field devices. Mock path ≡ field path into the image. |
| **Plant model library (SWD-83)** | `plcassistant.wedge` `MockProcess` | Offline / unit-test physics helper. **Not** used on the live HA App scan path (SWD-145: Soft-PLC is mock-unaware; live App uses `HeldProcess` + plant IN). |

Packaging ownership: [`docs/packaging/01-shape.md`](../packaging/01-shape.md) (SWD-145). Image / binding contracts: [`docs/io/01-image-quality.md`](../io/01-image-quality.md), [`docs/io/02-binding-model.md`](../io/02-binding-model.md).

**Live process gap:** Until SWD-146 ships the integration simulator, live plant PVs stay static (defaults / manual Number entities). Offline wedge acceptance still uses `MockProcess`.

## First-class capability

| Requirement | Detail |
|-------------|--------|
| Selectable field vs mock entities | Thin integration can expose mock entities or bind real field entities; Soft-PLC control/safety logic is unchanged (binding-agnostic image) |
| Same tag contract | Mock publishes/consumes the tags in [`02-io-hmi-contract.md`](02-io-hmi-contract.md) (per-tag quality; no `*_BAD` tags) |
| Injectable faults | Operator or test harness can force bad quality / LOS, raise/lower levels, and adjust drain/pump curves for scenarios |
| Deterministic enough | Same scenario steps yield the same qualitative outcomes (trips, direction of cascade) |
| HA-visible | Mock PVs/commands appear as HA entities on the same HMI/binding path used for field acceptance |

Mocking is a **system requirement** for PLCAssistant: future multi-tank examples should reuse the same **integration-owned** simulator approach (`MockProcess` remains an offline library).

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
| `force_quality("LT_TANK", BAD, fault)` | Sets `LT_TANK` quality to BAD; freeze or NaN last PV |
| `force_quality("LT_RES", BAD, fault)` | Sets `LT_RES` quality to BAD |
| `force_quality("FT_INLET", BAD, fault)` | Sets `FT_INLET` quality to BAD |
| `force_LT_TANK_BAD` (wrapper) | Thin alias → `force_quality("LT_TANK", BAD, fault)` |
| `force_LT_RES_BAD` (wrapper) | Thin alias → `force_quality("LT_RES", BAD, fault)` |
| `force_FT_INLET_BAD` (wrapper) | Thin alias → `force_quality("FT_INLET", BAD, fault)` |
| `nudge_h_tank` | Add delta to tank level (for HH scenario) |
| `nudge_h_res` | Add delta to reservoir (for LL scenario) |
| `set_K_DRAIN` | Disturbance for cascade demo |

Clearing an injector restores normal quality / physics. There are no separate `*_BAD` tags — quality lives on each PV ([`docs/io/01-image-quality.md`](../io/01-image-quality.md)).

## Timebase

- Plant-model simulation step ≤ 100 ms recommended for demo responsiveness
- Soft-PLC control/safety scan is independent of how mock entities are produced; document chosen rates in packaging notes

## What mock must prove

See [`06-mock-acceptance.md`](06-mock-acceptance.md): Start/Stop, cascade response, HH, LL, each LOS, latch/reset.

## Non-goals

- CFD / 3D hydraulics
- Perfect SI unit purity if documented conversions are consistent
- Emulating every VFD fault code
- An Add-on-owned mock I/O branch distinct from the field binding path (superseded by SWD-86 / SWD-97)

## Related specs

- Packaging host (mock ownership): [`08-packaging-sketch.md`](08-packaging-sketch.md)
- Physical follow-on: [`07-follow-on.md`](07-follow-on.md)
