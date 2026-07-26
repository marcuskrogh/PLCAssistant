# Issues

Continuity mirror for Jira (`SWD`). Upsert rows when issues are created, transitioned, or handed off.

| Key | Type | Title | Status | Parent | Artifact | Next |
|-----|------|-------|--------|--------|----------|------|
| SWD-66 | Story | PLCAssistant: virtual PLC for Home Assistant | To Do | | docs/ROADMAP.md | `/ship SWD-71` |
| SWD-70 | Task | Architecture & approach selection for virtual PLC over HA entities | Done | SWD-66 | docs/ARCHITECTURE.md | Done — phase closed |
| SWD-73 | Sub-task | WP1: ADR — architecture decision record | Done | SWD-70 | docs/ARCHITECTURE.md | — |
| SWD-74 | Sub-task | WP2: I/O HAL contract | Done | SWD-70 | docs/IO_HAL.md | — |
| SWD-75 | Sub-task | WP3: Packaging blueprint | Done | SWD-70 | docs/PACKAGING.md | — |
| SWD-72 | Sub-task | WP4: Downstream handoff to SWD-71/69/68/67 | Done | SWD-70 | docs/HANDOFF.md | — |
| SWD-71 | Task | HA entity I/O bridge for PLC tags | In Review | SWD-66 | docs/PLAN.md | `/ship SWD-71` |
| SWD-78 | Sub-task | WP1: plcassistant_contract library | Done | SWD-71 | packages/plcassistant_contract/ | — |
| SWD-80 | Sub-task | WP2: HACS integration skeleton + config entry | Done | SWD-71 | custom_components/plcassistant/ | — |
| SWD-77 | Sub-task | WP3: Binding registry and config UI | Done | SWD-71 | custom_components/plcassistant/ | — |
| SWD-76 | Sub-task | WP4: Control-plane sync client | Done | SWD-71 | custom_components/plcassistant/control_plane.py | — |
| SWD-79 | Sub-task | WP5: Diagnostic entities from GetStatus | Done | SWD-71 | custom_components/plcassistant/ | — |
| SWD-69 | Task | PLC program execution runtime | To Do | SWD-66 | docs/ARCHITECTURE.md | `/define SWD-69` after SWD-71 |
| SWD-68 | Task | Operator surfaces: Lovelace HMI and Influx/Grafana historian | To Do | SWD-66 | docs/HANDOFF.md | `/define SWD-68` after runtime tags |
| SWD-67 | Task | Delivery packaging as HA integration and addon | To Do | SWD-66 | docs/PACKAGING.md | `/define SWD-67` when MVP scope stable |

## Log

- 2026-07-25 — `/explore` created Story SWD-66 + phase Tasks SWD-70/71/69/68/67; wrote `docs/ROADMAP.md`; Next `/research SWD-70` or `/define SWD-70`.
- 2026-07-25 — `/research SWD-70` wrote `docs/RESEARCH.md` (IEC 61131 arXiv brief; scan soft-PLC preferred); Next `/define SWD-70`.
- 2026-07-26 — Enriched `docs/RESEARCH.md` with HA technology landscape; lean soft-PLC **addon** + thin Core integration; Next `/define SWD-70`.
- 2026-07-26 — Competitive evaluation; white-space confirmed; Next `/define SWD-70`.
- 2026-07-26 — `/define SWD-70` wrote architecture PLAN; Sub-tasks SWD-73/74/75/72; Next `/implement SWD-70`.
- 2026-07-26 — `/implement` → `/review-fix` → `/ship SWD-70` (PR #3); Next `/define SWD-71`.
- 2026-07-26 — `/define SWD-71` wrote `docs/PLAN.md`; Sub-tasks SWD-78/80/77/76/79; Next `/implement SWD-71`.
- 2026-07-26 — `/implement SWD-71`: contract lib + HACS integration + tests (30 passed); Sub-tasks Done; Task → In Review; Next `/review-fix SWD-71`.
- 2026-07-26 — `/review-fix SWD-71` iter1 REQUEST_CHANGES (2 blockers); fix-forward: PutBindings on setup, HACS vendor contract, control_plane client, fail-safe options (34 tests).
- 2026-07-26 — `/review-fix SWD-71` iter2 **CLEAN**; Task stays In Review; Next `/ship SWD-71`.
