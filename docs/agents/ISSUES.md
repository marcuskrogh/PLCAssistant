# Issues

Continuity mirror for Jira (`SWD`). Upsert rows when issues are created, transitioned, or handed off.

| Key | Type | Title | Status | Parent | Artifact | Next |
|-----|------|-------|--------|--------|----------|------|
| SWD-66 | Story | PLCAssistant: virtual PLC for Home Assistant | To Do | | docs/ROADMAP.md | `/implement SWD-70` |
| SWD-70 | Task | Architecture & approach selection for virtual PLC over HA entities | To Do | SWD-66 | docs/PLAN.md | `/implement SWD-70` |
| SWD-73 | Sub-task | WP1: ADR — architecture decision record | To Do | SWD-70 | docs/PLAN.md | `/implement SWD-70` |
| SWD-74 | Sub-task | WP2: I/O HAL contract | To Do | SWD-70 | docs/PLAN.md | `/implement SWD-70` |
| SWD-75 | Sub-task | WP3: Packaging blueprint | To Do | SWD-70 | docs/PLAN.md | `/implement SWD-70` |
| SWD-72 | Sub-task | WP4: Downstream handoff to SWD-71/69/68/67 | To Do | SWD-70 | docs/PLAN.md | `/implement SWD-70` |
| SWD-71 | Task | HA entity I/O bridge for PLC tags | To Do | SWD-66 | docs/ROADMAP.md | `/define SWD-71` after SWD-70 ships |
| SWD-69 | Task | PLC program execution runtime | To Do | SWD-66 | docs/ROADMAP.md | `/define SWD-69` after SWD-71 |
| SWD-68 | Task | Operator surfaces: Lovelace HMI and Influx/Grafana historian | To Do | SWD-66 | docs/ROADMAP.md | `/define SWD-68` after runtime tags |
| SWD-67 | Task | Delivery packaging as HA integration/addon | To Do | SWD-66 | docs/ROADMAP.md | `/define SWD-67` when MVP scope stable |

## Log

- 2026-07-25 — `/explore` created Story SWD-66 + phase Tasks SWD-70/71/69/68/67; wrote `docs/ROADMAP.md`; Next `/research SWD-70` or `/define SWD-70`.
- 2026-07-25 — `/research SWD-70` wrote `docs/RESEARCH.md` (IEC 61131 arXiv brief; scan soft-PLC preferred); Next `/define SWD-70`.
- 2026-07-26 — Enriched `docs/RESEARCH.md` with HA technology landscape (entities, ST_HA, addons, Modbus, FUXA, Influx/Grafana, Lovelace); lean soft-PLC **addon** + thin Core integration; Next `/define SWD-70`.
- 2026-07-26 — Added detailed competitive evaluation of similar HA integrations/apps (OpenPLC, redPlc, ST_HA, S7/TwinCAT, FUXA, PiPLC, etc.); white-space confirmed; Next `/define SWD-70`.
- 2026-07-26 — `/define SWD-70` wrote `docs/PLAN.md`; Sub-tasks SWD-73/74/75/72; Next `/implement SWD-70`.
