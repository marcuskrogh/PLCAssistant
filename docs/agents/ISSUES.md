# Issues

Continuity mirror for Jira (`SWD`). Upsert rows when issues are created, transitioned, or handed off.

| Key | Type | Title | Status | Parent | Artifact | Next |
|-----|------|-------|--------|--------|----------|------|
| SWD-66 | Story | PLCAssistant: virtual PLC for Home Assistant | To Do | | docs/ROADMAP.md | `/implement SWD-71` |
| SWD-70 | Task | Architecture & approach selection for virtual PLC over HA entities | Done | SWD-66 | docs/ARCHITECTURE.md | Done — phase closed |
| SWD-73 | Sub-task | WP1: ADR — architecture decision record | Done | SWD-70 | docs/ARCHITECTURE.md | — |
| SWD-74 | Sub-task | WP2: I/O HAL contract | Done | SWD-70 | docs/IO_HAL.md | — |
| SWD-75 | Sub-task | WP3: Packaging blueprint | Done | SWD-70 | docs/PACKAGING.md | — |
| SWD-72 | Sub-task | WP4: Downstream handoff to SWD-71/69/68/67 | Done | SWD-70 | docs/HANDOFF.md | — |
| SWD-71 | Task | HA entity I/O bridge for PLC tags | To Do | SWD-66 | docs/PLAN.md | `/implement SWD-71` |
| SWD-78 | Sub-task | WP1: plcassistant_contract library | To Do | SWD-71 | docs/PLAN.md | `/implement SWD-71` |
| SWD-80 | Sub-task | WP2: HACS integration skeleton + config entry | To Do | SWD-71 | docs/PLAN.md | `/implement SWD-71` |
| SWD-77 | Sub-task | WP3: Binding registry and config UI | To Do | SWD-71 | docs/PLAN.md | `/implement SWD-71` |
| SWD-76 | Sub-task | WP4: Control-plane sync client | To Do | SWD-71 | docs/PLAN.md | `/implement SWD-71` |
| SWD-79 | Sub-task | WP5: Diagnostic entities from GetStatus | To Do | SWD-71 | docs/PLAN.md | `/implement SWD-71` |
| SWD-69 | Task | PLC program execution runtime | To Do | SWD-66 | docs/ARCHITECTURE.md | `/define SWD-69` after SWD-71 |
| SWD-68 | Task | Operator surfaces: Lovelace HMI and Influx/Grafana historian | To Do | SWD-66 | docs/HANDOFF.md | `/define SWD-68` after runtime tags |
| SWD-67 | Task | Delivery packaging as HA integration and addon | To Do | SWD-66 | docs/PACKAGING.md | `/define SWD-67` when MVP scope stable |

## Log

- 2026-07-25 — `/explore` created Story SWD-66 + phase Tasks SWD-70/71/69/68/67; wrote `docs/ROADMAP.md`; Next `/research SWD-70` or `/define SWD-70`.
- 2026-07-25 — `/research SWD-70` wrote `docs/RESEARCH.md` (IEC 61131 arXiv brief; scan soft-PLC preferred); Next `/define SWD-70`.
- 2026-07-26 — Enriched `docs/RESEARCH.md` with HA technology landscape (entities, ST_HA, addons, Modbus, FUXA, Influx/Grafana, Lovelace); lean soft-PLC **addon** + thin Core integration; Next `/define SWD-70`.
- 2026-07-26 — Added detailed competitive evaluation of similar HA integrations/apps (OpenPLC, redPlc, ST_HA, S7/TwinCAT, FUXA, PiPLC, etc.); white-space confirmed; Next `/define SWD-70`.
- 2026-07-26 — `/define SWD-70` wrote `docs/PLAN.md`; Sub-tasks SWD-73/74/75/72; Next `/implement SWD-70`.
- 2026-07-26 — `/implement SWD-70` wrote `docs/ARCHITECTURE.md`, `IO_HAL.md`, `PACKAGING.md`, `HANDOFF.md`; Sub-tasks Done; Task → In Review; Next `/review-fix SWD-70`.
- 2026-07-26 — `/review-fix` iter 1: REQUEST_CHANGES (0 blocker / 10 should-fix); fix-forward addressing HANDOFF anchors, IO_HAL fields/phases, control plane, HAL ownership, ROADMAP hybrid wording.
- 2026-07-26 — `/review-fix` iter 2: CLEAN (0 blocker / 0 should-fix / notes only); Next `/ship SWD-70`.
- 2026-07-26 — `/ship SWD-70`: merged PR #3 (`b16a84d`); Task Done; Story SWD-66 remains open; Next `/define SWD-71`.
- 2026-07-26 — `/define SWD-71` wrote `docs/PLAN.md` (archived prior plan as `PLAN_SWD-70.md`); Sub-tasks SWD-78/80/77/76/79; Next `/implement SWD-71`.
