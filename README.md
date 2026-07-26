# PLCAssistant

Virtual PLC for Home Assistant: control logic with PLC-like semantics, using HA entities as field I/O, Lovelace/kiosk as HMI, and InfluxDB/Grafana as historian.

See [docs/ROADMAP.md](docs/ROADMAP.md) for goals, scope, phases, and tracker links (Story [SWD-66](https://marcusknielsen.atlassian.net/browse/SWD-66)).

## Architecture (phase 1)

| Doc | Role |
|-----|------|
| [docs/PLAN.md](docs/PLAN.md) | Current implementation plan (SWD-71 I/O bridge) |
| [docs/PLAN_SWD-70.md](docs/PLAN_SWD-70.md) | Shipped phase-1 architecture plan |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Accepted ADR (scan soft-PLC, OpenPLC wrap, HA I/O) |
| [docs/IO_HAL.md](docs/IO_HAL.md) | Entity ↔ PLC binding and scan I/O contract |
| [docs/PACKAGING.md](docs/PACKAGING.md) | Addon + HACS packaging boundary |
| [docs/HANDOFF.md](docs/HANDOFF.md) | Implications for phases 2–5 |
| [docs/BRIDGE.md](docs/BRIDGE.md) | SWD-71 binding JSON + control-plane sync notes |
| [docs/RESEARCH.md](docs/RESEARCH.md) | Research brief backing the ADR |

## Code (phase 2 — SWD-71)

| Path | Role |
|------|------|
| `packages/plcassistant_contract/` | Shared binding schema, coercion, fail-safe, HTTP control-plane client |
| `custom_components/plcassistant/` | HACS integration: config entry, binding store/UI, diagnostics, services |

```bash
python3 -m pip install -r requirements-dev.txt -e packages/plcassistant_contract
python3 -m pytest -q
```

