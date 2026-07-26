# PLCAssistant

Virtual PLC for Home Assistant: control logic with PLC-like semantics, using HA entities as field I/O, Lovelace/kiosk as HMI, and InfluxDB/Grafana as historian.

See [docs/ROADMAP.md](docs/ROADMAP.md) for goals, scope, phases, and tracker links (Story [SWD-66](https://marcusknielsen.atlassian.net/browse/SWD-66)).

## Architecture (phase 1)

| Doc | Role |
|-----|------|
| [docs/PLAN.md](docs/PLAN.md) | Definition / locked decisions (SWD-70) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Accepted ADR (scan soft-PLC, OpenPLC wrap, HA I/O) |
| [docs/IO_HAL.md](docs/IO_HAL.md) | Entity ↔ PLC binding and scan I/O contract |
| [docs/PACKAGING.md](docs/PACKAGING.md) | Addon + HACS packaging boundary |
| [docs/HANDOFF.md](docs/HANDOFF.md) | Implications for phases 2–5 |
| [docs/RESEARCH.md](docs/RESEARCH.md) | Research brief backing the ADR |
