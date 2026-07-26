# Downstream handoff — architecture → phases 2–5

**Source Task:** [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70)  
**Artifacts:** [ARCHITECTURE.md](ARCHITECTURE.md) · [IO_HAL.md](IO_HAL.md) · [PACKAGING.md](PACKAGING.md) · [PLAN.md](PLAN.md)

This note maps locked decisions to the next implementation Tasks so phase owners do not re-debate architecture.

---

## Implications by Task

### SWD-71 — Phase 2: I/O & entity bridge

| Implication | Source | Required behaviour |
|-------------|--------|-------------------|
| Transport = HA WebSocket/REST first | ADR decision summary | Implement entity read/write via Core APIs; Modbus TCP is **out of MVP** |
| Binding schema | [IO_HAL Binding model](IO_HAL.md#binding-model) | Persist `entity_id` ↔ PLC tag ↔ direction ↔ type ↔ fail-safe fields (`safe_value`, `critical`, …) |
| Scan I/O order | [IO_HAL Scan cycle](IO_HAL.md#scan-cycle-contract) | Bridge check → inputs (+ mirrors) → `execute_cycle()` → outputs (+ mirrors) |
| Fail-safe | [IO_HAL Fail-safe](IO_HAL.md#fail-safe-and-freshness) | Cold-start + unavailable/stale policies; on bridge fault apply `on_bridge_fault` only |
| Diagnostics | [IO_HAL Diagnostics](IO_HAL.md#diagnostics-integration-entities) | Expose named diagnostic entities; consume addon `GetStatus` / `StatusPush` |
| Ownership | [PACKAGING](PACKAGING.md#components) | SWD-71 ships **binding registry + sync client (`PutBindings`)** and preferably **`plcassistant_contract`** (pure coercion/fail-safe). **HAL loop hosts in the addon** (SWD-69); do not re-implement HAL inside HACS. Shared lib is schema + pure functions only. |

**Do not:** Treat Modbus as the primary path; invent a second binding model.

---

### SWD-69 — Phase 3: Soft-PLC runtime

| Implication | Source | Required behaviour |
|-------------|--------|-------------------|
| Wrap OpenPLC Runtime | ADR decision summary | Addon hosts OpenPLC (or documented fork); build program externally |
| Scan cycle | [IO_HAL Scan cycle](IO_HAL.md#scan-cycle-contract) | **HAL owns period**; call `SoftPlcRuntime.execute_cycle()` once per scan; soft RT only; honor integration `scan_period` (default proposal 100 ms) |
| I/O via HAL | IO_HAL | Runtime must not talk to entities directly — use HAL |
| Fallback | ADR fallback trigger | If OpenPLC blocked, minimal custom scan implementing the same `execute_cycle` port + same HAL — explicit ADR amendment |
| Authoring | ADR decision summary | OpenPLC Editor external; no in-HA ST IDE in MVP |
| Status API | [PACKAGING Control plane](PACKAGING.md#control-plane-abstract-ops) | Emit metrics for diagnostic entities (`GetStatus` / `StatusPush`) |

**Do not:** Transpile ST → HA automations as the runtime; claim hard RT or SIL; run a second OpenPLC autonomous I/O clock against HA bindings.

---

### SWD-68 — Phase 4: HMI & historian

| Implication | Source | Required behaviour |
|-------------|--------|-------------------|
| HMI = Lovelace (+ optional kiosk) | ADR decision summary | Dashboards bind to HA entities / PLC status entities |
| Historian = Influx + Grafana | ADR decision summary | Document patterns; optional export of scan metrics |
| FUXA | RESEARCH | Optional later — not MVP dependency |
| Diagnostics surfaces | [IO_HAL Diagnostics](IO_HAL.md#diagnostics-integration-entities) | Use diagnostic entities already owned by SWD-71/69 |

**Do not:** Build a custom SCADA shell in MVP; require FUXA for first demo.

---

### SWD-67 — Phase 5: Packaging & distribution

| Implication | Source | Required behaviour |
|-------------|--------|-------------------|
| Dual packaging | ADR + PACKAGING | **Addon (runtime) and HACS (config/UI)** — both required |
| Ingress / auth | [PACKAGING Supervisor](PACKAGING.md#supervisor--core-communication) | Prefer Supervisor proxy; document token handling |
| Control plane | [PACKAGING Control plane](PACKAGING.md#control-plane-abstract-ops) | Implement abstract ops over HTTP/ingress adapters |
| Lifecycle | [PACKAGING Lifecycle](PACKAGING.md#lifecycle) | Install order, program upload then Reload/Start, config reload |
| Docs for install | [PACKAGING Install targets](PACKAGING.md#install-targets) | README paths for HAOS users |

**Do not:** Ship runtime-only without a config surface, or HACS-only without a process host.

---

## Acceptance for WP4

- [x] This handoff exists and links all architecture docs  
- [x] ROADMAP phase 1 points at ARCHITECTURE (and related)  
- [x] Downstream Tasks SWD-71 / 69 / 68 / 67 receive tracker comments pointing here  
- [x] Section references use heading anchors (not opaque §N)  
