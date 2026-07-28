# Issues

Continuity mirror for Jira (`SWD`). Upsert rows when issues are created, transitioned, or handed off.

| Key | Type | Title | Status | Parent | Artifact | Next |
|-----|------|-------|--------|--------|----------|------|
| SWD-81 | Story | PLCAssistant — Virtual PLC for Home Assistant | Done | — | docs/ROADMAP.md | Done — initiative complete |
| SWD-83 | Task | Explore theme: Lab / hobby / small-process wedge | Done | SWD-81 | docs/PLAN.md (prior), docs/wedge/, plcassistant/wedge/ | Done — phase closed |
| SWD-88 | Sub-task | SWD-83: Reference process spec | Done | SWD-83 | docs/wedge/01-reference-process.md | — |
| SWD-87 | Sub-task | SWD-83: I/O & HMI contract for the skid | Done | SWD-83 | docs/wedge/02-io-hmi-contract.md | — |
| SWD-92 | Sub-task | SWD-83: Control story spec | Done | SWD-83 | docs/wedge/03-control-story.md | — |
| SWD-93 | Sub-task | SWD-83: Safety story spec | Done | SWD-83 | docs/wedge/04-safety-story.md | — |
| SWD-90 | Sub-task | SWD-83: Mock process requirements | Done | SWD-83 | docs/wedge/05-mock-process.md | — |
| SWD-89 | Sub-task | SWD-83: Mock acceptance scenarios | Done | SWD-83 | docs/wedge/06-mock-acceptance.md | — |
| SWD-91 | Sub-task | SWD-83: Follow-on note (physical + later examples) | Done | SWD-83 | docs/wedge/07-follow-on.md | — |
| SWD-94 | Sub-task | SWD-83: Preliminary packaging sketch | Done | SWD-83 | docs/wedge/08-packaging-sketch.md | — |
| SWD-86 | Task | Explore theme: HA entities as PLC I/O | Done | SWD-81 | docs/PLAN.md (prior), docs/io/, plcassistant/io/ | Done — phase closed |
| SWD-95 | Sub-task | SWD-86: I/O image & quality contract | Done | SWD-86 | docs/io/01-image-quality.md, plcassistant/io/ | — |
| SWD-98 | Sub-task | SWD-86: Binding model & schema | Done | SWD-86 | docs/io/02-binding-model.md, plcassistant/io/binding.py | — |
| SWD-96 | Sub-task | SWD-86: Wedge I/O contract update | Done | SWD-86 | docs/wedge/02-io-hmi-contract.md, plcassistant/wedge/ | — |
| SWD-97 | Sub-task | SWD-86: Packaging note revision | Done | SWD-86 | docs/wedge/08-packaging-sketch.md (+ 05/07/README) | — |
| SWD-99 | Sub-task | SWD-86: Thin-integration stub | Done | SWD-86 | docs/io/03-thin-integration-stub.md, plcassistant/io/integration.py | — |
| SWD-100 | Sub-task | SWD-86: Contract/unit tests | Done | SWD-86 | docs/io/04-acceptance.md, tests/test_swd86_acceptance.py | — |
| SWD-85 | Task | Explore theme: Control semantics | Done | SWD-81 | docs/PLAN.md, docs/control/, plcassistant/control/ | Done — phase closed |
| SWD-103 | Sub-task | SWD-85: Scan scheduler contract | Done | SWD-85 | docs/control/01-scan-scheduler.md, plcassistant/control/ | — |
| SWD-105 | Sub-task | SWD-85: Continuous FB / PID semantics | Done | SWD-85 | docs/control/02-fb-pid.md, plcassistant/wedge/control.py | — |
| SWD-104 | Sub-task | SWD-85: Safety precedence in the scan | Done | SWD-85 | docs/control/03-safety-precedence.md, plcassistant/wedge/skid.py | — |
| SWD-101 | Sub-task | SWD-85: HA↔cyclic boundary note | Done | SWD-85 | docs/control/04-ha-cyclic-boundary.md | — |
| SWD-102 | Sub-task | SWD-85: Wedge control-story update | Done | SWD-85 | docs/wedge/03-control-story.md (+ 02/07) | — |
| SWD-106 | Sub-task | SWD-85: Contract/unit tests | Done | SWD-85 | docs/control/05-acceptance.md, tests/test_swd85_acceptance.py | — |
| SWD-82 | Task | Explore theme: Programming surface | Done | SWD-81 | docs/PLAN.md, docs/surface/, plcassistant/surface/, plcassistant/app/ | Done — phase closed |
| SWD-119 | Sub-task | SWD-82: Block model + YAML schema | Done | SWD-82 | docs/surface/01-block-model.md, plcassistant/surface/ | — |
| SWD-116 | Sub-task | SWD-82: Python block runtime + scan integration | Done | SWD-82 | docs/surface/02-runtime.md, plcassistant/surface/runtime.py | — |
| SWD-115 | Sub-task | SWD-82: Built-in wedge block library | Done | SWD-82 | docs/surface/03-builtin-library.md, plcassistant/surface/builtin.py | — |
| SWD-114 | Sub-task | SWD-82: User library + in-App Python editor | Done | SWD-82 | plcassistant/surface/user_library.py, plcassistant/app/ | — |
| SWD-120 | Sub-task | SWD-82: App visual canvas bound to YAML | Done | SWD-82 | docs/surface/05-app-editor.md, plcassistant/app/ | — |
| SWD-117 | Sub-task | SWD-82: Apply policy (restart + hot-apply) | Done | SWD-82 | docs/surface/04-apply-policy.md, plcassistant/surface/apply.py | — |
| SWD-121 | Sub-task | SWD-82: Wedge skid migration onto blocks | Done | SWD-82 | docs/surface/06-wedge-migration.md, plcassistant/wedge/skid.py | — |
| SWD-118 | Sub-task | SWD-82: Contract/unit tests + acceptance | Done | SWD-82 | docs/surface/07-acceptance.md, tests/test_swd82_acceptance.py | — |
| SWD-84 | Task | Explore theme: Packaging shape | Done | SWD-81 | docs/PLAN.md, docs/packaging/, plc_assistant/, custom_components/plcassistant/ | Done — phase closed |
| SWD-122 | Sub-task | SWD-84: Packaging contract docs | Done | SWD-84 | docs/packaging/ | — |
| SWD-123 | Sub-task | SWD-84: HA App scaffold | Done | SWD-84 | ha_app/plcassistant/ | — |
| SWD-125 | Sub-task | SWD-84: MQTT I/O bridge (App) | Done | SWD-84 | plcassistant/io/mqtt_*.py | — |
| SWD-126 | Sub-task | SWD-84: Bundled thin integration | Done | SWD-84 | custom_components/plcassistant/ | — |
| SWD-127 | Sub-task | SWD-84: GitHub App repository + install docs | Done | SWD-84 | ha_app/repository.yaml, ha_app/INSTALL.md | — |
| SWD-124 | Sub-task | SWD-84: Acceptance tests + checklist | Done | SWD-84 | docs/packaging/03-acceptance.md, tests/test_swd84_acceptance.py | — |
| SWD-128 | Bug | [Iterate] App configure after reinstall: Supervisor job-group stop/stats errors | In Review | Relates SWD-84 | docs/ITERATE.md | `/ship SWD-128` |

## Log

- 2026-07-28 — review-fix SWD-128 CLEAN after 2 iterations (iter1: 1B+6SF watchdog/install/MQTT lifecycle; iter2: 0); Next `/ship SWD-128`.
- 2026-07-28 — Iterate SWD-128: after 0.1.5 reinstall, configuring App logs Supervisor `Another job is running` / `App is not running`. Hardening App start (integration install must not crash-loop; MQTT off HTTP thread); docs troubleshooting; bump App to 0.1.6.
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
- 2026-07-26 — review-fix SWD-86 CLEAN after 3 iterations (10→5→0 blocking); Next `/ship SWD-86`.
- 2026-07-26 — Fix-forward SWD-86 review iteration 1: apply_in non-GOOD/missing, apply_out written-only flush, docs alignment, compose helpers; Task stays In Review; Next `/review-fix SWD-86`.
- 2026-07-26 — Fix-forward SWD-86 review iteration 2: apply_in GOOD None/non-numeric/non-finite demote, set_output non-finite demote, SP_LEVEL naming docs; Task stays In Review; Next `/review-fix SWD-86`.
- 2026-07-26 — Research complete for SWD-85: `docs/RESEARCH.md` (scan-cycle semantics, safety ambition, HA vs cyclic); tool `scripts/arxiv_research.py`; Next `/define SWD-85`.
- 2026-07-27 — Define complete for SWD-85: `docs/PLAN.md`; Sub-tasks SWD-103, SWD-105, SWD-104, SWD-101, SWD-102, SWD-106; Next `/implement SWD-85`.
- 2026-07-27 — Implement SWD-85 complete: Sub-tasks Done; Task → In Review; Next `/ship SWD-85`.
- 2026-07-27 — review-fix SWD-85 CLEAN after 2 iterations (2→0 should-fix); Next `/ship SWD-85`.
- 2026-07-27 — Shipped SWD-85 via PR #18 (merge `a51cdbe`); Task Done; Story SWD-81 remains open; Next `/define SWD-82`.
- 2026-07-27 — Reverted incorrect SWD-82 `/research` + `/define` (PRs #20/#21 closed unmerged; Sub-tasks SWD-107..112 cancelled). Continuity remains post–SWD-85 ship; Next `/define SWD-82`.
- 2026-07-27 — Fresh research complete for SWD-82: `docs/RESEARCH.md` (multi-axis; does not reuse discarded brief; surfaces overload of “easy high-level” + Soft-PLC≠HA; leaves layer/language choices open). Task remains To Do; Next `/define SWD-82`.
- 2026-07-27 — Define complete for SWD-82: `docs/PLAN.md`; Sub-tasks SWD-119, SWD-116, SWD-115, SWD-114, SWD-120, SWD-117, SWD-121, SWD-118; Next `/implement SWD-82`.
- 2026-07-27 — Implement SWD-82 complete: surface + App editor + wedge CONTROL on blocks; Sub-tasks Done; Task → In Review; Next `/review-fix SWD-82`.
- 2026-07-27 — review-fix SWD-82 CLEAN after 2 iterations (iter1: stale context/sandbox/hot-apply/etc.; iter2: shell-owned `running` wires + CMD clamp, builtin overwrite guard, localhost default, docs JSON/YAML align); Next `/ship SWD-82`.
- 2026-07-27 — Shipped SWD-82 via PR #26 (merge `6bc330f`); Task Done; Story SWD-81 remains open (SWD-84 packaging remains); Next `/research SWD-84`.
- 2026-07-27 — Research complete for SWD-84: `docs/RESEARCH.md` (HA Apps vs integration vs Container sidecar; soft-PLC container peers; bridge options). Task remains To Do; Next `/define SWD-84`.
- 2026-07-27 — Define complete for SWD-84: `docs/PLAN.md`; Sub-tasks SWD-122, SWD-123, SWD-125, SWD-126, SWD-127, SWD-124; Next `/implement SWD-84`.
- 2026-07-27 — Implement SWD-84 complete: packaging docs, HA App scaffold, MQTT bridge, bundled thin integration, GitHub App install docs, acceptance tests; Sub-tasks Done; Task → In Review; Next `/review-fix SWD-84`.
- 2026-07-27 — review-fix SWD-84 CLEAN after 3 iterations (iter1: 3B+8SF MQTT wiring/persist; iter2: 1B+4SF writable mock IN + scan cmds/retry/locks; iter3: 0 blockers/should-fix); Next `/ship SWD-84`.
- 2026-07-28 — Shipped SWD-84 via PR #30 (merge `3b64b33`); Task Done; all theme Tasks Done; Story SWD-81 → Done (initiative complete).
