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
| Binding schema | IO_HAL §1 | Persist `entity_id` ↔ PLC address ↔ direction ↔ type ↔ fail-safe |
| Scan I/O order | IO_HAL §2 | Snapshot inputs → expose to runtime → apply outputs after scan |
| Fail-safe | IO_HAL §3 | On disconnect/timeout: hold / safe / last-good per binding |
| Diagnostics | IO_HAL §5 | Latency, stale, fail-safe events for HACS sensors later |
| Ownership | PACKAGING | Bridge code lives primarily in **addon** (or shared lib); HACS configures bindings |

**Do not:** Treat Modbus as the primary path; invent a second binding model.

---

### SWD-69 — Phase 3: Soft-PLC runtime

| Implication | Source | Required behaviour |
|-------------|--------|-------------------|
| Wrap OpenPLC Runtime | ADR decision summary | Addon hosts OpenPLC (or documented fork); build program externally |
| Scan cycle | ADR decision summary | Fixed period; measure jitter; soft RT only |
| I/O via HAL | IO_HAL | Runtime must not talk to entities directly — use HAL |
| Fallback | ADR fallback trigger | If OpenPLC blocked, minimal custom scan loop + same HAL — explicit pivot |
| Authoring | ADR decision summary | OpenPLC Editor external; no in-HA ST IDE in MVP |

**Do not:** Transpile ST → HA automations as the runtime; claim hard RT or SIL.

---

### SWD-68 — Phase 4: HMI & historian

| Implication | Source | Required behaviour |
|-------------|--------|-------------------|
| HMI = Lovelace (+ optional kiosk) | ADR decision summary | Dashboards bind to HA entities / PLC status entities |
| Historian = Influx + Grafana | ADR decision summary | Document patterns; optional export of scan metrics |
| FUXA | RESEARCH | Optional later — not MVP dependency |
| Diagnostics surfaces | IO_HAL §5 | Expose status entities the HMI can show |

**Do not:** Build a custom SCADA shell in MVP; require FUXA for first demo.

---

### SWD-67 — Phase 5: Packaging & distribution

| Implication | Source | Required behaviour |
|-------------|--------|-------------------|
| Dual packaging | ADR + PACKAGING | Addon (runtime) + HACS (config/UI) |
| Ingress / auth | PACKAGING §3–4 | Prefer Supervisor proxy; document token handling |
| Lifecycle | PACKAGING §5 | Start order, config reload, program deploy |
| Docs for install | PACKAGING §6 | README paths for HAOS users |

**Do not:** Ship runtime-only without a config surface, or HACS-only without a process host.

---

## Acceptance for WP4

- [x] This handoff exists and links all architecture docs  
- [x] ROADMAP phase 1 points at ARCHITECTURE (and related)  
- [x] Downstream Tasks SWD-71 / 69 / 68 / 67 receive tracker comments pointing here  
