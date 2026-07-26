# Implementation plan: Architecture & approach selection (SWD-70)

## Summary

Lock PLCAssistant’s phase-1 architecture: a **scan-cycle soft-PLC** packaged as a **Home Assistant OS/Supervised addon**, with a **thin Core (HACS) integration** for config and entity exposure. Prefer **wrapping OpenPLC Runtime** for IEC 61131 execution, and differentiate on a first-class **HA entity I/O HAL** (WebSocket primary; Modbus optional mirror). Explicitly **out**: ST→HA-automation transpile as the runtime, hard real-time/safety certification, and replacing Lovelace/Influx/Grafana.

This phase delivers architecture artifacts only (no soft-PLC product code beyond docs/contracts). Downstream Tasks SWD-71 / SWD-69 / SWD-68 / SWD-67 implement against these decisions.

## Scope

### In

- Architecture decision: runtime engine, packaging split, I/O ownership model
- I/O HAL contract: entity→input tag, output tag→service, freshness/availability, fail-safe policy
- Non-goals: determinism, safety, historian/HMI ownership
- Handoff notes that constrain SWD-71 (I/O bridge), SWD-69 (runtime), SWD-68 (HMI/historian), SWD-67 (packaging)
- Written architecture record under `docs/` (ADR / architecture doc)

### Out

- Implementing the addon, OpenPLC wrapper, or HACS integration (later Tasks)
- Building a custom ladder/ST IDE (use OpenPLC Editor for MVP)
- Shipping ST_HA_Automation-style transpile as primary control path
- Designing Lovelace/Grafana dashboards in detail (SWD-68)
- Physical PLC client features as the product focus

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Control paradigm** | IEC 61131-style **scan cycle** (read inputs → logic → write outputs) | Matches “all capabilities of a PLC”; research rejects event-transpile as substitute ([docs/RESEARCH.md](RESEARCH.md)) |
| **Runtime engine (MVP)** | **Wrap OpenPLC Runtime** inside a Supervisor addon | Real IEC languages/editor; recognized soft-PLC; faster than greenfield scan VM |
| **Fallback** | If OpenPLC packaging/license/I/O-plugin friction blocks MVP, document pivot to a **minimal custom scan runtime** (ST or boolean subset only) under Open items — do not silently switch | Keeps decision explicit |
| **Packaging** | **Hybrid**: addon = soft-PLC process; **thin HACS/Core integration** = config UI, binding registry, diagnostic entities | Matches AppDaemon/Node-RED precedent; isolates cyclic runtime from Core |
| **I/O ownership** | **HA entities are field I/O** of the soft-PLC | Product white space vs Modbus/S7 (opposite) and OpenPLC-as-default-I/O |
| **I/O transport (primary)** | Core **WebSocket / REST** (addon uses Supervisor Core API proxy) | Rich entity state + service calls; fits entity model |
| **I/O transport (optional)** | Expose soft-PLC tags on **Modbus TCP** for FUXA / external tools; not required for MVP entity control | Compose path; secondary |
| **Authoring (MVP)** | **OpenPLC Editor** (LD/ST/FBD as supported upstream) | Avoid building IDE in phase 1–3 |
| **Transpile / Node-RED / redPlc / ST_HA** | **Adjacent, not runtime** | May document interop later; not the architecture |
| **HMI** | **Lovelace / kiosk** primary; FUXA optional later | Reuse; out of SWD-70 build |
| **Historian** | **InfluxDB + Grafana** via entity state export | Reuse; out of SWD-70 build |
| **Determinism** | **Soft real-time / best-effort scan**; no SCHED_FIFO or cycle-time SLAs on commodity HA hosts | HA entity latency dominates |
| **Safety** | **Not safety-rated**; configurable fail-safe on stale/unavailable inputs | Document operator responsibility |

## I/O model (contract sketch)

```text
Scan cycle (addon soft-PLC):
  1. Sample bound HA entity states → input tags (%I / IA)
  2. Execute program (OpenPLC)
  3. Apply output tags (%Q / QA) → HA services / writable entities
  4. Sleep until next cycle (configured period, best-effort)
```

| Direction | Mapping | Notes |
|-----------|---------|-------|
| Input | `entity_id` + optional attribute → tag | Coerce bool/number/string; track `last_seen`, `available` |
| Output | tag → service (`domain.service`) or entity write | Idempotent writes preferred; rate-limit churn |
| Memory | Internal PLC memory; optional mirror to `input_*` helpers | Operator setpoints / overrides |
| Stale / unavailable | Per-binding policy: **hold last**, **force 0/false**, or **force configured safe value**; optionally force outputs to safe | Default: hold last for inputs; safe-off for critical outputs when configured |
| Diagnostics | Integration entities: scan overruns, bridge lag, binding errors | For Lovelace troubleshooting |

Exact schema and config UX are specified in work package 2 and implemented under **SWD-71**.

## Packaging blueprint

| Component | Responsibility |
|-----------|----------------|
| **Supervisor addon** | Run OpenPLC (or fallback runtime); scan loop; WebSocket client to Core; optional Modbus server |
| **HACS integration** | Config entries for PLC instance + bindings; expose diagnostic sensors; start/stop/reload services; store binding registry |
| **OpenPLC Editor** | External engineering tool (MVP); upload program to runtime API |
| **HA Core** | Device fabric, Lovelace, Influx export — unchanged |

Container install targets: **HAOS / Supervised** first. Container/Docker Compose users may run the runtime image manually (document in SWD-67); not a blocker for architecture lock.

## Constraints

- Must not require replacing Lovelace, InfluxDB, or Grafana
- Must not claim hard real-time or SIL/safety certification
- Prefer upstream OpenPLC over forking unless a thin I/O plugin / wrapper is required
- Architecture docs must be enough for SWD-71/SWD-69 to start without re-litigating paradigm
- Repo currently docs/skills-first; architecture artifacts live under `docs/`

## Acceptance criteria

1. A single architecture decision record exists under `docs/` stating the Decisions table above (no unresolved “option lists” for MVP path).
2. I/O HAL contract is written with directions, freshness/fail-safe policies, and diagnostic expectations sufficient for SWD-71.
3. Packaging blueprint (addon vs integration responsibilities) is written and matches the hybrid decision.
4. Non-goals (determinism, safety, HMI/historian ownership, transpile-as-runtime) are explicit in the ADR.
5. Downstream Task notes: SWD-71 / SWD-69 descriptions (or ADR “Implications” section) reference this plan’s decisions.
6. `docs/ROADMAP.md` phase-1 row points at `PLAN.md` + ADR; open questions that this phase closed are marked resolved.

## Work packages

1. **ADR — architecture decision record** — Persist locked decisions, alternatives considered (transpile, redPlc, in-Core scan, greenfield VM), and why OpenPLC-wrap + hybrid packaging won for MVP.
2. **I/O HAL contract** — Formalize binding model, coercion, freshness/availability, fail-safe policies, diagnostics; leave UI details to SWD-71.
3. **Packaging blueprint** — Addon ↔ integration API boundary, Supervisor token/Core proxy usage, config ownership, lifecycle (install/start/stop/update).
4. **Downstream handoff** — Update ROADMAP open questions; annotate implications for SWD-71/69/68/67 in ADR or Task comments.

## Open items

- OpenPLC Runtime v4 **license / addon redistribution** constraints — verify before SWD-69 implement; if blocking, trigger documented fallback (minimal custom scan runtime).
- Exact **default scan period** and overrun metrics — propose in I/O/runtime contract; tune in SWD-69.
- Whether MVP bindings are **UI-only**, YAML, or both — defer to SWD-71 (prefer UI config entry).
- Optional Modbus server in MVP vs post-MVP — default **post-MVP** unless cheap with OpenPLC defaults.

## Tracker

- Provider: jira
- Story: [SWD-66](https://marcusknielsen.atlassian.net/browse/SWD-66)
- Task: [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70)
- Sub-tasks: [SWD-73](https://marcusknielsen.atlassian.net/browse/SWD-73) (ADR), [SWD-74](https://marcusknielsen.atlassian.net/browse/SWD-74) (I/O HAL), [SWD-75](https://marcusknielsen.atlassian.net/browse/SWD-75) (packaging), [SWD-72](https://marcusknielsen.atlassian.net/browse/SWD-72) (downstream handoff)
- Inputs: [docs/RESEARCH.md](RESEARCH.md), [docs/ROADMAP.md](ROADMAP.md)

## Next

`/review-fix SWD-70` — Review architecture docs and auto-fix until clean.

**Implemented:** [ARCHITECTURE.md](ARCHITECTURE.md) · [IO_HAL.md](IO_HAL.md) · [PACKAGING.md](PACKAGING.md) · [HANDOFF.md](HANDOFF.md)
