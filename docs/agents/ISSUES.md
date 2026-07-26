# Issues

Continuity mirror for Jira (`SWD`). Upsert rows when issues are created, transitioned, or handed off.

| Key | Type | Title | Status | Parent | Artifact | Next |
|-----|------|-------|--------|--------|----------|------|
| SWD-81 | Story | PLCAssistant — Virtual PLC for Home Assistant | To Do | — | docs/ROADMAP.md | `/review-fix SWD-86` |
| SWD-83 | Task | Explore theme: Lab / hobby / small-process wedge | Done | SWD-81 | docs/PLAN.md (prior), docs/wedge/, plcassistant/wedge/ | Done — phase closed |
| SWD-88 | Sub-task | SWD-83: Reference process spec | Done | SWD-83 | docs/wedge/01-reference-process.md | — |
| SWD-87 | Sub-task | SWD-83: I/O & HMI contract for the skid | Done | SWD-83 | docs/wedge/02-io-hmi-contract.md | — |
| SWD-92 | Sub-task | SWD-83: Control story spec | Done | SWD-83 | docs/wedge/03-control-story.md | — |
| SWD-93 | Sub-task | SWD-83: Safety story spec | Done | SWD-83 | docs/wedge/04-safety-story.md | — |
| SWD-90 | Sub-task | SWD-83: Mock process requirements | Done | SWD-83 | docs/wedge/05-mock-process.md | — |
| SWD-89 | Sub-task | SWD-83: Mock acceptance scenarios | Done | SWD-83 | docs/wedge/06-mock-acceptance.md | — |
| SWD-91 | Sub-task | SWD-83: Follow-on note (physical + later examples) | Done | SWD-83 | docs/wedge/07-follow-on.md | — |
| SWD-94 | Sub-task | SWD-83: Preliminary packaging sketch | Done | SWD-83 | docs/wedge/08-packaging-sketch.md | — |
| SWD-86 | Task | Explore theme: HA entities as PLC I/O | In Review | SWD-81 | docs/PLAN.md, docs/io/, plcassistant/io/ | `/review-fix SWD-86` |
| SWD-95 | Sub-task | SWD-86: I/O image & quality contract | Done | SWD-86 | docs/io/01-image-quality.md, plcassistant/io/ | — |
| SWD-98 | Sub-task | SWD-86: Binding model & schema | Done | SWD-86 | docs/io/02-binding-model.md, plcassistant/io/binding.py | — |
| SWD-96 | Sub-task | SWD-86: Wedge I/O contract update | Done | SWD-86 | docs/wedge/02-io-hmi-contract.md, plcassistant/wedge/ | — |
| SWD-97 | Sub-task | SWD-86: Packaging note revision | Done | SWD-86 | docs/wedge/08-packaging-sketch.md (+ 05/07/README) | — |
| SWD-99 | Sub-task | SWD-86: Thin-integration stub | Done | SWD-86 | docs/io/03-thin-integration-stub.md, plcassistant/io/integration.py | — |
| SWD-100 | Sub-task | SWD-86: Contract/unit tests | Done | SWD-86 | docs/io/04-acceptance.md, tests/test_swd86_acceptance.py | — |
| SWD-85 | Task | Explore theme: Control semantics | To Do | SWD-81 | docs/ROADMAP.md | `/research SWD-85` (optional) |
| SWD-82 | Task | Explore theme: Programming surface | To Do | SWD-81 | docs/ROADMAP.md | later |
| SWD-84 | Task | Explore theme: Packaging shape | To Do | SWD-81 | docs/ROADMAP.md | later |

## Log

- 2026-07-26 — Cleared first PLCAssistant development session (Story SWD-66 and Tasks/Sub-tasks SWD-67..SWD-80; removed explore/implement artifacts from the repo) for a fresh exploration start.
- 2026-07-26 — Explore complete: Story SWD-81 + theme Tasks SWD-83, SWD-86, SWD-85, SWD-82, SWD-84; artifact `docs/ROADMAP.md`; Next `/define SWD-83`.
- 2026-07-26 — Define complete for SWD-83: `docs/PLAN.md`; Sub-tasks SWD-88, SWD-87, SWD-92, SWD-93, SWD-90, SWD-89, SWD-91, SWD-94; Next `/implement SWD-83`.
- 2026-07-26 — Implement SWD-83: wedge specs + mock cascade/safety core; Sub-tasks Done; Task → In Review.
- 2026-07-26 — review-fix SWD-83 CLEAN after 3 iterations (8→2→0 should-fix); Next `/ship SWD-83`.
- 2026-07-26 — Shipped SWD-83 via PR #11 (merge `3f892a4`); Task Done; Story SWD-81 remains open; Next `/define SWD-86`.
- 2026-07-26 — Define complete for SWD-86: `docs/PLAN.md`; Sub-tasks SWD-95, SWD-98, SWD-96, SWD-97, SWD-99, SWD-100; Next `/implement SWD-86`.
- 2026-07-26 — SWD-95 Done: I/O image & quality contract (`docs/io/01-image-quality.md`, `plcassistant/io/`); reason codes locked; Next continue `/implement SWD-86` (SWD-98).
- 2026-07-26 — SWD-98 Done: binding model & schema (`docs/io/02-binding-model.md`, `plcassistant/io/binding.py`); config field names locked; Next continue `/implement SWD-86` (SWD-96).
- 2026-07-26 — SWD-96 Done: wedge I/O contract retires `*_BAD`; runtime uses `TagQuality` / `is_good` from `plcassistant.io`; Next continue `/implement SWD-86` (SWD-97 / SWD-99).
- 2026-07-26 — SWD-97 Done: packaging sketch revised — mock/sim entities owned by thin integration; Add-on remains live I/O image SoT (`docs/wedge/08-packaging-sketch.md` + related); docs-only; Next continue `/implement SWD-86`.
- 2026-07-26 — SWD-99 Done: thin-integration stub (`docs/io/03-thin-integration-stub.md`, `plcassistant/io/integration.py`); in-process `scan_inputs`/`scan_outputs` on shared `IoImage` (HA IPC later / SWD-84); Next continue `/implement SWD-86` (SWD-100).
- 2026-07-26 — SWD-100 Done: PLAN acceptance contract/unit tests (`docs/io/04-acceptance.md`, `tests/test_swd86_acceptance.py`); all SWD-86 packages complete; Next `/review-fix SWD-86`.
- 2026-07-26 — Implement SWD-86 complete: Sub-tasks Done; Task → In Review; Next `/review-fix SWD-86`.
