# Architecture decision record: PLCAssistant MVP

**Status:** Accepted  
**Date:** 2026-07-26  
**Task:** [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70)  
**Plan:** [docs/PLAN.md](PLAN.md)  
**Research:** [docs/RESEARCH.md](RESEARCH.md)

## Context

PLCAssistant aims to provide PLC-style control where **Home Assistant entities** are the field sensors and actuators, while reusing Lovelace (HMI) and InfluxDB/Grafana (historian). Phase 1 must lock the control paradigm, runtime engine, packaging, and I/O ownership so later phases do not re-litigate fundamentals.

## Decision summary

| Topic | Decision |
|-------|----------|
| Control paradigm | IEC 61131-style **scan cycle** |
| Runtime (MVP) | **Wrap OpenPLC Runtime** in a Supervisor **addon** |
| Packaging | **Hybrid**: addon (runtime) + thin **HACS/Core integration** (config, bindings, diagnostics) |
| I/O ownership | HA entities are the soft-PLC’s field I/O |
| I/O transport | Primary: Core **WebSocket/REST**; optional later: **Modbus TCP** tag expose |
| Authoring (MVP) | **OpenPLC Editor** (external) |
| HMI / historian | **Reuse** Lovelace/kiosk and InfluxDB/Grafana; do not replace |
| Determinism / safety | Soft real-time only; **not** safety-rated |

Detailed I/O rules: [docs/IO_HAL.md](IO_HAL.md).  
Packaging boundaries: [docs/PACKAGING.md](PACKAGING.md).

## System context

```text
┌─────────────────────────────────────────────────────────────┐
│ Home Assistant Core                                         │
│  devices → entities ←── thin PLCAssistant integration       │
│  Lovelace / kiosk (HMI)     InfluxDB export → Grafana       │
└───────────────┬─────────────────────────────────────────────┘
                │ WebSocket / REST (Supervisor proxy)
                ▼
┌─────────────────────────────────────────────────────────────┐
│ PLCAssistant addon                                          │
│  Entity I/O HAL  ↔  OpenPLC Runtime (scan cycle)            │
│  Program load via OpenPLC API   [optional Modbus later]     │
└─────────────────────────────────────────────────────────────┘
                ▲
                │ upload program
         OpenPLC Editor (PC)
```

## Alternatives considered

### A. ST → native HA automation transpile (e.g. ST_HA_Automation)

- **Pros:** Stays inside Core; familiar HA deploy story; IEC *language* feel.  
- **Cons:** Event-driven runtime, not scan-cycle PLC semantics; weak fit for continuous interlocks.  
- **Verdict:** **Rejected as MVP runtime.** May remain an adjacent authoring idea later.

### B. redPlc + Node-RED as the product

- **Pros:** Ladder UX; HA already has Node-RED addon.  
- **Cons:** Locked to Node-RED; glue-heavy entity binding; not a first-class HA entity HAL product.  
- **Verdict:** **Rejected as primary architecture.** Demand signal only.

### C. Soft-PLC scan loop inside Core / pyscript

- **Pros:** Single process; easy install for some users.  
- **Cons:** Crash/load risk to Core; poor isolation for cyclic work; atypical for heavy runtimes.  
- **Verdict:** **Rejected for MVP production path.** Possible spike only.

### D. Greenfield custom scan VM (no OpenPLC)

- **Pros:** Full control of tags/API/UX.  
- **Cons:** Large language/editor/runtime cost before any value.  
- **Verdict:** **Deferred fallback** if OpenPLC wrap is blocked (license/packaging/I/O plugin). Must be an explicit pivot, not silent.

### E. Wrap OpenPLC in addon + thin HACS integration + HA entity HAL *(chosen)*

- **Pros:** Real IEC stack and editor; packaging matches AppDaemon/Node-RED; differentiation on entity I/O; clear process boundary.  
- **Cons:** Upstream dependency; dual tooling (Editor + HA); license/redistribution must be verified.  
- **Verdict:** **Accepted for MVP.**

## Non-goals (explicit)

- Hard real-time guarantees, SCHED_FIFO SLAs, or certified safety (SIL) behaviour  
- Replacing Lovelace, InfluxDB, or Grafana  
- Primary product focus on bridging *physical* PLCs into HA (S7/TwinCAT/Modbus clients already exist)  
- Building a custom LD/ST IDE in phases 1–3  
- Using ST→YAML transpile or Node-RED as the control runtime  

## Fallback trigger

Before or during **SWD-69**, verify OpenPLC Runtime redistribution/license and feasibility of an HA entity I/O path (plugin or external HAL driving tags).

If blocked, pivot to a **minimal custom scan runtime** (boolean/ST subset, no full OpenPLC Editor requirement) and update this ADR with status **Superseded** / amendment — do not silently change approach mid-implement.

## Implications for later phases

| Task | Implication |
|------|-------------|
| [SWD-71](https://marcusknielsen.atlassian.net/browse/SWD-71) | Implement binding registry + WebSocket HAL per [IO_HAL.md](IO_HAL.md); UI config preferred |
| [SWD-69](https://marcusknielsen.atlassian.net/browse/SWD-69) | Package/run OpenPLC in addon; program lifecycle; scan metrics; license check |
| [SWD-68](https://marcusknielsen.atlassian.net/browse/SWD-68) | Document Lovelace/kiosk + Influx/Grafana patterns against bound entities; FUXA optional |
| [SWD-67](https://marcusknielsen.atlassian.net/browse/SWD-67) | Ship addon + HACS integration + install docs + minimal demo |

## Consequences

- Users on **HAOS / Supervised** are the primary install path.  
- Engineering workflow uses **OpenPLC Editor** externally for MVP.  
- Product success hinges on **entity↔tag binding UX** more than inventing another PLC language stack.  
- Operators must understand soft real-time and non-safety-rated limits.

## References

- [docs/PLAN.md](PLAN.md)  
- [docs/RESEARCH.md](RESEARCH.md)  
- [docs/ROADMAP.md](ROADMAP.md)  
- OpenPLC Runtime: https://github.com/Autonomy-Logic/openplc-runtime  
- HA app communication: https://developers.home-assistant.io/docs/apps/communication/
