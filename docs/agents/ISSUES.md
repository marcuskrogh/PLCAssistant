# Issues

Continuity mirror for Jira (`SWD`). Upsert rows when issues are created, transitioned, or handed off.

| Key | Type | Title | Status | Parent | Artifact | Next |
|-----|------|-------|--------|--------|----------|------|
| SWD-81 | Story | PLCAssistant — Virtual PLC for Home Assistant | To Do | — | docs/ROADMAP.md | `/ship SWD-83` |
| SWD-83 | Task | Explore theme: Lab / hobby / small-process wedge | In Review | SWD-81 | docs/PLAN.md, docs/wedge/, plcassistant/wedge/ | `/ship SWD-83` |
| SWD-88 | Sub-task | SWD-83: Reference process spec | Done | SWD-83 | docs/wedge/01-reference-process.md | — |
| SWD-87 | Sub-task | SWD-83: I/O & HMI contract for the skid | Done | SWD-83 | docs/wedge/02-io-hmi-contract.md | — |
| SWD-92 | Sub-task | SWD-83: Control story spec | Done | SWD-83 | docs/wedge/03-control-story.md | — |
| SWD-93 | Sub-task | SWD-83: Safety story spec | Done | SWD-83 | docs/wedge/04-safety-story.md | — |
| SWD-90 | Sub-task | SWD-83: Mock process requirements | Done | SWD-83 | docs/wedge/05-mock-process.md | — |
| SWD-89 | Sub-task | SWD-83: Mock acceptance scenarios | Done | SWD-83 | docs/wedge/06-mock-acceptance.md | — |
| SWD-91 | Sub-task | SWD-83: Follow-on note (physical + later examples) | Done | SWD-83 | docs/wedge/07-follow-on.md | — |
| SWD-94 | Sub-task | SWD-83: Preliminary packaging sketch | Done | SWD-83 | docs/wedge/08-packaging-sketch.md | — |
| SWD-86 | Task | Explore theme: HA entities as PLC I/O | To Do | SWD-81 | docs/ROADMAP.md | sibling later |
| SWD-85 | Task | Explore theme: Control semantics | To Do | SWD-81 | docs/ROADMAP.md | sibling later |
| SWD-82 | Task | Explore theme: Programming surface | To Do | SWD-81 | docs/ROADMAP.md | sibling later |
| SWD-84 | Task | Explore theme: Packaging shape | To Do | SWD-81 | docs/ROADMAP.md | sibling later |

## Log

- 2026-07-26 — Cleared first PLCAssistant development session (Story SWD-66 and Tasks/Sub-tasks SWD-67..SWD-80; removed explore/implement artifacts from the repo) for a fresh exploration start.
- 2026-07-26 — Explore complete: Story SWD-81 + theme Tasks SWD-83, SWD-86, SWD-85, SWD-82, SWD-84; artifact `docs/ROADMAP.md`; Next `/define SWD-83`.
- 2026-07-26 — Define complete for SWD-83: `docs/PLAN.md`; Sub-tasks SWD-88, SWD-87, SWD-92, SWD-93, SWD-90, SWD-89, SWD-91, SWD-94; Next `/implement SWD-83`.
- 2026-07-26 — Implement SWD-83: wedge specs + mock cascade/safety core (37 pytest); Sub-tasks Done; Task → In Review; Next `/ship SWD-83`.
- 2026-07-26 — review-fix SWD-83 CLEAN after 3 iterations (8→2→0 should-fix); Next `/ship SWD-83`.
