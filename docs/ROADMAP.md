# Roadmap: PLCAssistant — virtual PLC for Home Assistant

## Goals

- Run **PLC-style control** where sensors and actuators are **Home Assistant entities** bound as PLC I/O.
- Deliver core PLC capabilities: cyclic (or equivalent) logic, timers/counters, structured programs, and low-level write/read of bound entities.
- Reuse the HA stack for **HMI** (Lovelace / custom dashboards / tablet kiosk) and **historian** (InfluxDB + Grafana) instead of inventing parallel systems.

### Success criteria

- An operator can bind HA entities to PLC tags, load a control program, and drive equipment through those entities.
- Equipment panels can be built in Lovelace (including kiosk mode) against the same entities/tags.
- Long-term trends are available via InfluxDB → Grafana without a custom historian.

## Scope

### In

- Soft-PLC (or strong PLC equivalent) whose tags bind to HA entities
- Engineering path to author/deploy control logic
- Packaging as a Home Assistant **HACS integration and HAOS/Supervised addon** (hybrid)
- Patterns/docs for historian + HMI on existing HA tooling

### Out

- Full industrial SCADA replacement
- Hard real-time / safety-certified PLC guarantees on commodity HA hosts
- Replacing InfluxDB, Grafana, or Lovelace with a custom stack
- Primary focus on bridging *physical* PLCs into HA (already covered by existing S7/Modbus/TwinCAT integrations)

## Conceptual model

```text
HA devices / integrations
        │  entities (sensors, switches, …)
        ▼
┌───────────────────────────┐
│ HA Core + thin HACS integ.│  ← bindings SoT, diagnostics, services
└───────────────┬───────────┘
                │ WebSocket / REST (control plane)
                ▼
┌───────────────────────────┐
│ Addon: I/O HAL + OpenPLC  │  ← scan cycle, tags, timers
└───────────────┬───────────┘
                │
                ├─► Lovelace / kiosk dashboards  (HMI)
                └─► InfluxDB → Grafana           (historian)
```

## Landscape (explore findings)

Existing work mostly fills *adjacent* niches, not this product:

| Approach | Role vs PLCAssistant |
|----------|----------------------|
| HA Modbus / S7 / TwinCAT integrations | HA as **client of a real PLC** — opposite I/O ownership |
| OpenPLC (+ Modbus) with HA | Soft-PLC is real; HA usually **HMI/SCADA client**, not the I/O fabric |
| ST for Home Assistant (ST→YAML) | IEC **language feel**, but **event-driven HA automations**, not a scan-cycle PLC |
| FUXA (HA addon) | **SCADA/HMI**, not a PLC runtime |
| Node-RED / ladder bridges | Possible soft logic, but not a first-class HA entity↔PLC-tag product |

**Gap:** no mature product treats HA entities as the field I/O of a soft-PLC with PLC semantics, while deliberately leaning on Lovelace + Influx/Grafana for HMI and history.

## Suggested phases

| Phase | Topic | Notes | Issue |
|-------|-------|-------|-------|
| 1 | Architecture & approach selection | **Shipped:** ADR [`ARCHITECTURE.md`](ARCHITECTURE.md), [`IO_HAL.md`](IO_HAL.md), [`PACKAGING.md`](PACKAGING.md), [`HANDOFF.md`](HANDOFF.md). Prior plan: [`PLAN_SWD-70.md`](PLAN_SWD-70.md). Research: [`RESEARCH.md`](RESEARCH.md). PR [#3](https://github.com/marcuskrogh/PLCAssistant/pull/3) | [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70) ✅ |
| 2 | HA entity I/O bridge | **Implemented:** [`PLAN.md`](PLAN.md) · [`BRIDGE.md`](BRIDGE.md) · `packages/plcassistant_contract/` · `custom_components/plcassistant/` | [SWD-71](https://marcusknielsen.atlassian.net/browse/SWD-71) |
| 3 | PLC program execution | Runtime lifecycle, timers/counters, at least one IEC-style language path | [SWD-69](https://marcusknielsen.atlassian.net/browse/SWD-69) |
| 4 | Operator surfaces | Lovelace/kiosk HMI patterns + InfluxDB/Grafana historian patterns | [SWD-68](https://marcusknielsen.atlassian.net/browse/SWD-68) |
| 5 | Delivery packaging | HACS integration **and** HAOS addon + minimal demo | [SWD-67](https://marcusknielsen.atlassian.net/browse/SWD-67) |

### Sequencing rationale

Architecture first (phase 1) unlocks the I/O bridge shape (phase 2) and runtime choice (phase 3). HMI/historian (phase 4) mostly *documents and scaffolds* existing HA capabilities once tags/entities are stable. Packaging (phase 5) ships an MVP once the control path works end-to-end.

## Open questions

Resolved by [`docs/PLAN_SWD-70.md`](PLAN_SWD-70.md) / SWD-70:

- Soft-PLC engine → **wrap OpenPLC Runtime** in addon (fallback: minimal custom scan if blocked)
- Determinism → **soft / best-effort**; no safety cert
- Languages MVP → **OpenPLC Editor** (LD/ST/FBD as upstream supports)
- Fail-safe → configurable per binding (hold last / force safe)
- Packaging → **addon + thin HACS integration**

Resolved by [`docs/PLAN.md`](PLAN.md) / SWD-71 define:

- Binding UI vs YAML → **UI config entry / options** primary; YAML out of MVP
- Shared contract lib → **ship `plcassistant_contract`**
- Sync before addon → HTTP client + test double; graceful unavailable

Still open (deferred):

- OpenPLC redistribution/license check before SWD-69
- Default scan period confirmation / overrun metrics (SWD-69; proposal 100 ms)
- Supervisor ingress auto-discovery (SWD-67; manual URL in SWD-71)
- Optional Modbus server (post-MVP)

## Assumptions (working)

- Prefer **real PLC semantics** (scan cycle + IEC-style programming) over pure event-driven automation transpile, matching “all the capabilities of a PLC.”
- HA remains the device/integration fabric; PLCAssistant owns control logic over entity state/services.
- Historian and HMI reuse InfluxDB/Grafana and Lovelace rather than inventing new UI/storage.

## Tracker

- Provider: jira
- Story: [SWD-66](https://marcusknielsen.atlassian.net/browse/SWD-66)
- Tasks: [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70), [SWD-71](https://marcusknielsen.atlassian.net/browse/SWD-71), [SWD-69](https://marcusknielsen.atlassian.net/browse/SWD-69), [SWD-68](https://marcusknielsen.atlassian.net/browse/SWD-68), [SWD-67](https://marcusknielsen.atlassian.net/browse/SWD-67)

## Next

`/ship SWD-71` — Merge I/O bridge after CLEAN review-fix.
