# 08 — Preliminary packaging sketch

**Tracker:** [SWD-94](https://marcusknielsen.atlassian.net/browse/SWD-94) · revised [SWD-97](https://marcusknielsen.atlassian.net/browse/SWD-97)  
**Parent:** [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) · I/O Task [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Record the **working packaging shape** enough to host operator services and the HA entity ↔ tag path: **Home Assistant Add-on (Soft-PLC + live I/O image)** plus a **thin config integration** for bindings, units, and **mock/sim entities**. This is **not** a final freeze — full alternatives remain [SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84).

**SWD-86 revision:** mock/sim entities are owned by the **thin integration**, not by an Add-on mock-process engine. The Add-on always sees the same binding-fed image path for mock and field.

## Chosen shape (preliminary)

```
┌──────────────────────────────────────────────────────┐
│                   Home Assistant                     │
│  Lovelace HMI · Recorder/Historian · UI              │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │ Thin config integration                        │  │
│  │  · tag declarations & entity ↔ tag bindings    │  │
│  │  · unit conversion                             │  │
│  │  · mock/sim entities (entity mock, SWD-86)     │  │
│  │  · operator services (start/stop/reset/SPs)    │  │
│  └──────────────▲─────────────────────────────────┘  │
│                 │ HA APIs / services / entity state  │
└─────────────────┼────────────────────────────────────┘
                  │ same path: mock entities ≡ field
     ┌────────────▼────────────┐
     │  HA Add-on (app)        │
     │  · soft-PLC / scan loop │
     │  · control + safety     │
     │  · live I/O image (SoT) │
     │  · binding-agnostic     │
     └─────────────────────────┘
```

Contracts: [`docs/io/01-image-quality.md`](../io/01-image-quality.md) (image + quality) · [`docs/io/02-binding-model.md`](../io/02-binding-model.md) (bindings + config shape).

## Responsibility split

| Concern | Add-on (runtime) | Thin integration |
|---------|------------------|------------------|
| Scan / control / safety execution | **Owns** | No |
| Live I/O image each scan (source of truth) | **Owns** | Feeds/sinks via bindings at scan boundaries |
| Mock / sim **HA entities** (entity mock) | No special mock I/O path | **Owns** — entities mocked internally |
| Optional plant-model physics (SWD-83 `MockProcess`) | Not an Add-on I/O mode | May drive mock entity values / offline unit tests — see [`05-mock-process.md`](05-mock-process.md) |
| Tag declarations & entity ↔ tag bindings | Consumes binding-fed samples into image | **Owns** config UI / YAML |
| Unit conversion | Sees engineering units on tags | **Owns** at binding layer |
| Operator Start/Stop/Reset services | Implements commands on tags | **Owns** `services.yaml` / buttons calling add-on or entities |
| Lovelace dashboards | — | Documented examples; user-owned cards OK |
| Historian | — | Reuse HA recorder / Influx |
| Deep authoring UX / language | Out (SWD-82) | Out |

**Invariant:** mock path ≡ field path into the Add-on image. The Soft-PLC does not branch on “mock mode”; it only sees tag values and quality on the image.

## Config surface (minimum for mock acceptance)

Enough to run acceptance — not a full product installer. Align field names with [`docs/io/02-binding-model.md`](../io/02-binding-model.md) (`tags` / `bindings`).

```yaml
# Illustrative — schema owned by SWD-86 / thin integration; freeze in SWD-84
plcassistant:
  # Mock is an integration concern: mock entities (or a plant model behind them),
  # not an Add-on process-engine mode.
  tags:
    LT_TANK: { default: 0.15, unit: m }
    LT_RES: { default: 0.20, unit: m }
    FT_INLET: { default: 0.0, unit: L/min }
    CMD_SPEED: { default: 0.0, unit: pct }
    SP_LEVEL_REQ: { default: 0.15, unit: m }
    SP_LEVEL: { default: 0.15, unit: m }
  bindings:
    - tag: LT_TANK
      entity: sensor.mock_tank_level   # mock entity in thin integration
      direction: IN
    - tag: LT_RES
      entity: sensor.mock_res_level
      direction: IN
    - tag: FT_INLET
      entity: sensor.mock_inlet_flow
      direction: IN
    - tag: CMD_SPEED
      entity: number.mock_pump_speed
      direction: OUT
    - tag: SP_LEVEL_REQ
      entity: input_number.tank_sp
      direction: IN
    - tag: SP_LEVEL
      entity: sensor.tank_sp_active
      direction: OUT
  limits:
    LIM_LEVEL_HH: 0.36
    LIM_RES_LL: 0.05
  services:
    start: plcassistant.start
    stop: plcassistant.stop
    reset: plcassistant.reset
```

In mock, the thin integration **synthesizes** entity state (optionally via the SWD-83 plant model) and binds it like any field device. The Add-on image is still refreshed through the same IN/OUT binding path.

## Operator services (thin integration)

| Service | Maps to tag / action |
|---------|----------------------|
| `plcassistant.start` | Pulse `HMI_START` |
| `plcassistant.stop` | Pulse `HMI_STOP` |
| `plcassistant.reset` | Pulse `HMI_RESET` |
| setpoint writes | HA `number` / `input_number` → request tag (`IN`); active SP via `OUT` |

## Why this split

- Add-on: long-running Soft-PLC, deterministic scan, live image — awkward as pure Python integration alone.
- Thin integration: HA config/entity UX, bindings, units, and mock entities — without stuffing full runtime into `configuration.yaml`.
- Mock and field share one image path, so control/safety stay binding-agnostic.
- Keeps door open to swap packaging after SWD-84 without rewriting the skid specs.

## Explicit non-goals for this sketch

- Choosing exact language/runtime stack inside the add-on
- Publishing a store-ready add-on release
- Exhaustive comparison of pure integration vs Supervisor vs external box (SWD-84)
- Final entity-registry UX (remaining SWD-86 packages / stub)
- Implementing the thin-integration stub (SWD-99)

## Scan / timebase (demo)

- Prefer injectable `dt` on the Soft-PLC scan (no wall-clock hard-coding in core).
- Demo responsiveness: scan / sim step **≤ 100 ms** (aligns with [`05-mock-process.md`](05-mock-process.md) timebase for plant-model steps behind mock entities).
- Control and safety may share the same scan; coarser rates are fine if documented.

## Hosting mock acceptance

To host [`06-mock-acceptance.md`](06-mock-acceptance.md) under this packaging shape:

1. Thin integration exposes mock entities (and optional plant model behind them)
2. Bindings map those entities to the skid tag contract — same path as field
3. Add-on runs control + safety on the live image only
4. Fault injection / level nudges act on mock entities or plant-model knobs in the integration (not a special Add-on I/O branch)
5. Integration services for Start/Stop/Reset visible to Lovelace

Until the stub lands (SWD-99), SWD-83 acceptance remains green via `plcassistant.wedge` tag API / unit tests.

## Related specs

- I/O image & quality: [`docs/io/01-image-quality.md`](../io/01-image-quality.md)
- Binding model: [`docs/io/02-binding-model.md`](../io/02-binding-model.md)
- Follow-on / physical: [`07-follow-on.md`](07-follow-on.md)
- Mock / plant model: [`05-mock-process.md`](05-mock-process.md)
- Plan: [`docs/PLAN.md`](../PLAN.md)
