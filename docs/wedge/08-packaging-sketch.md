# 08 — Preliminary packaging sketch

**Tracker:** [SWD-94](https://marcusknielsen.atlassian.net/browse/SWD-94)  
**Parent:** [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Record the **working packaging shape** enough to host the mock path and operator services: **Home Assistant Add-on (runtime + mock)** plus a **thin config integration** for bindings. This is **not** a final freeze — full alternatives remain [SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84).

## Chosen shape (preliminary)

```
┌──────────────────────────────────────────┐
│              Home Assistant              │
│  Lovelace HMI · Recorder/Historian · UI  │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ Thin config integration            │  │
│  │  · entity ↔ tag bindings           │  │
│  │  · operator services               │  │
│  │    (start/stop/reset/setpoints)    │  │
│  └──────────────▲─────────────────────┘  │
│                 │ HA APIs / services      │
└─────────────────┼────────────────────────┘
                  │
     ┌────────────▼────────────┐
     │  HA Add-on (app)        │
     │  · soft-PLC / scan loop │
     │  · control + safety     │
     │  · mock process engine  │
     │  · tag image / state    │
     └─────────────────────────┘
```

## Responsibility split

| Concern | Add-on (runtime) | Thin integration |
|---------|------------------|------------------|
| Scan / control / safety execution | **Owns** | No |
| Mock process engine | **Owns** | May expose switches to enable/inject |
| Tag image (`LT_TANK`, `CMD_SPEED`, …) | **Owns** source of truth | Maps to HA entities |
| Entity discovery & binding config | Consumes binding table | **Owns** config UI / YAML |
| Operator Start/Stop/Reset services | Implements commands on tags | **Owns** `services.yaml` / buttons calling add-on or entities |
| Lovelace dashboards | — | Documented examples; user-owned cards OK |
| Historian | — | Reuse HA recorder / Influx |
| Deep authoring UX / language | Out (SWD-82) | Out |

## Config surface (minimum for mock acceptance)

Enough to run acceptance — not a full product installer.

```yaml
# Illustrative only — exact schema TBD with SWD-86 / SWD-84
plcassistant:
  mode: mock   # mock | field
  skid: gravity_tank_v1
  bindings:
    LT_TANK: sensor.mock_tank_level      # or omit when mock synthesizes
    LT_RES: sensor.mock_res_level
    FT_INLET: sensor.mock_inlet_flow
    CMD_SPEED: number.mock_pump_speed
    # SC_PUMP optional
  setpoints:
    SP_LEVEL: input_number.tank_sp
  limits:
    LIM_LEVEL_HH: 0.36
    LIM_RES_LL: 0.05
  services:
    start: plcassistant.start
    stop: plcassistant.stop
    reset: plcassistant.reset
```

Mock mode may **synthesize** PVs inside the add-on and still mirror them to HA entities for HMI.

## Operator services (thin integration)

| Service | Maps to tag / action |
|---------|----------------------|
| `plcassistant.start` | Pulse `HMI_START` |
| `plcassistant.stop` | Pulse `HMI_STOP` |
| `plcassistant.reset` | Pulse `HMI_RESET` |
| setpoint writes | HA `number` / `input_number` → `SP_LEVEL` (etc.) |

## Why this split

- Add-on: long-running process, mock physics, deterministic scan — awkward as pure Python integration alone.
- Thin integration: stays on HA’s config/entity UX without stuffing full runtime into `configuration.yaml`.
- Keeps door open to swap packaging after SWD-84 without rewriting the skid specs.

## Explicit non-goals for this sketch

- Choosing exact language/runtime stack inside the add-on
- Publishing a store-ready add-on release
- Exhaustive comparison of pure integration vs Supervisor vs external box (SWD-84)
- Final entity-registry UX (SWD-86)

## Scan / timebase (demo)

- Prefer injectable `dt` on the soft-PLC / mock loop (no wall-clock hard-coding in core).
- Demo responsiveness: scan / sim step **≤ 100 ms** (aligns with [`05-mock-process.md`](05-mock-process.md) timebase).
- Control and safety may share the same scan; coarser rates are fine if documented.

## Hosting mock acceptance

The add-on must support:

1. Enable `mode: mock`
2. Run control + safety on the skid tag contract
3. Fault injection for LOS / level nudges
4. Integration services for Start/Stop/Reset visible to Lovelace

See [`06-mock-acceptance.md`](06-mock-acceptance.md).

## Related specs

- Follow-on / physical: [`07-follow-on.md`](07-follow-on.md)
- Mock requirements: [`05-mock-process.md`](05-mock-process.md)
- Plan open items: [`docs/PLAN.md`](../PLAN.md)
