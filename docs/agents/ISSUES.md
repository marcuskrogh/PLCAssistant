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
| SWD-128 | Bug | [Iterate] App configure after reinstall: Supervisor job-group stop/stats errors | Done | Relates SWD-84 | docs/ITERATE.md | Done — shipped PR #40 |
| SWD-129 | Bug | [Iterate] App Update stale image + hass.components integration after reinstall | Done | Relates SWD-128 | docs/ITERATE.md | Done — shipped PR #41 |
| SWD-130 | Bug | [Iterate] Store Latest stuck at 0.1.6 while GitHub has newer App version | Done | Relates SWD-129 | docs/ITERATE.md | Done — shipped PR #42 |
| SWD-131 | Bug | [Iterate] App Block Editor 404 under Ingress + thin integration too thin / version lock | Done | Relates SWD-130 | docs/ITERATE.md | Done — shipped PR #43 |
| SWD-132 | Bug | [Iterate] Operator dashboard default + major App UI refresh (mobile) | Done | Relates SWD-131 | docs/ITERATE.md | Done — shipped PR #44 |
| SWD-133 | Bug | [Iterate] Lovelace HMI default + writable SP + Soft-PLC plant on Start (not App SCADA) | Done | Relates SWD-132 | docs/ITERATE.md | Done — shipped PR #46 |
| SWD-134 | Bug | [Iterate] Auto-register default Lovelace dashboard in HA sidebar (no copy/paste) | Done | Relates SWD-133 | docs/ITERATE.md | Done — shipped PR #47 |
| SWD-135 | Bug | [Iterate] Lovelace status indicator + Start wiring (no visible process state) | Done | Relates SWD-134 | docs/ITERATE.md | Done — shipped PR #49 |
| SWD-136 | Bug | [Iterate] Soft-PLC HMI stuck offline — Start does nothing (status race) | Done | Relates SWD-135 | docs/ITERATE.md | Done — shipped PR #51 |
| SWD-137 | Bug | [Iterate] Soft-PLC still offline after 0.1.14 — MQTT never attaches without options | Done | Relates SWD-136 | docs/ITERATE.md | Done — shipped PR #52 |
| SWD-138 | Bug | [Iterate] Soft-PLC attached but HMI still offline — Core never restarts after integration sync | Done | Relates SWD-137 | docs/ITERATE.md | Done — shipped PR #53 |
| SWD-139 | Bug | [Iterate] Soft-PLC attached (stopped) but HMI still offline — MQTT never reaches HA entities | Done | Relates SWD-138 | docs/ITERATE.md | Done — shipped PR #55 |
| SWD-140 | Bug | [Iterate] HMI zeros on SP_LEVEL/SP_FLOW/LT_RES + clarify PERM_OK while RUNNING | Done | Relates SWD-139 | docs/ITERATE.md | Done — shipped PR #56 |
| SWD-141 | Bug | [Iterate] Level setpoint request does not update Active level SP (stuck 0.2 m) | Done | Relates SWD-140 | docs/ITERATE.md | Done — shipped PR #57 |
| SWD-142 | Story | Configurable mock dynamics — tags, unit ops, ODEs, selectable presets | Done | — | docs/ROADMAP.md | Done — initiative complete |
| SWD-145 | Task | Soft-PLC ↔ integration mock ownership boundary | Done | Relates SWD-142 | docs/PLAN.md | Done — shipped PR #59+#60 |
| SWD-149 | Subtask | SWD-145: Ownership docs (packaging / wedge / I/O) | Done | SWD-145 | docs/PLAN.md | — |
| SWD-150 | Subtask | SWD-145: Expose scan_period_s on Soft-PLC MQTT status | Done | SWD-145 | docs/PLAN.md | — |
| SWD-147 | Subtask | SWD-145: Remove App plant from live scan; plant tags as IN | Done | SWD-145 | docs/PLAN.md | — |
| SWD-148 | Subtask | SWD-145: Bindings / HMI / file-bridge cleanup for plant OUT removal | Done | SWD-145 | docs/PLAN.md | — |
| SWD-151 | Subtask | SWD-145: Tests + acceptance for ownership gap | Done | SWD-145 | docs/PLAN.md | — |
| SWD-146 | Task | Configurable dynamics core + skid preset | Done | Relates SWD-142 | docs/PLAN.md | Done — shipped PR #63 |
| SWD-156 | Subtask | SWD-146: Dynamics engine (ModelSpec + fixed-step stepper) | Done | SWD-146 | docs/PLAN.md | — |
| SWD-154 | Subtask | SWD-146: Skid preset + MockProcess oracle tests | Done | SWD-146 | docs/PLAN.md | — |
| SWD-152 | Subtask | SWD-146: HA simulator lifecycle + status/CMD_SPEED coupling | Done | SWD-146 | docs/PLAN.md | — |
| SWD-155 | Subtask | SWD-146: Plant Number ownership + HMI live-motion copy | Done | SWD-146 | docs/PLAN.md | — |
| SWD-153 | Subtask | SWD-146: Acceptance tests + packaging/docs/version | Done | SWD-146 | docs/PLAN.md | — |
| SWD-144 | Task | Unit-op library + custom equation authoring | Done | Relates SWD-142 | docs/PLAN.md | Done — shipped PR #65 |
| SWD-157 | Subtask | SWD-144: Unit-op contract + skid-derived catalog | Done | SWD-144 | docs/PLAN.md | — |
| SWD-159 | Subtask | SWD-144: Math expression AST sandbox | Done | SWD-144 | docs/PLAN.md | — |
| SWD-158 | Subtask | SWD-144: Compiler + YAML model documents | Done | SWD-144 | docs/PLAN.md | — |
| SWD-160 | Subtask | SWD-144: DynamicsModel typing + preset registry wiring | Done | SWD-144 | docs/PLAN.md | — |
| SWD-161 | Subtask | SWD-144: Acceptance tests + packaging/docs/version | Done | SWD-144 | docs/PLAN.md | — |
| SWD-143 | Task | Integration mock UI + preset selection | Done | Relates SWD-142 | docs/PLAN.md | Done — shipped PR #66 (App 0.1.24) |
| SWD-162 | Subtask | SWD-143: Options flow + preset persistence | Done | SWD-143 | docs/PLAN.md | — |
| SWD-163 | Subtask | SWD-143: Wire HassPlantSimulator to selected preset | Done | SWD-143 | docs/PLAN.md | — |
| SWD-164 | Subtask | SWD-143: Service + Lovelace operator surface | Done | SWD-143 | docs/PLAN.md | — |
| SWD-165 | Subtask | SWD-143: Acceptance tests + packaging/docs/version | Done | SWD-143 | docs/PLAN.md | — |
| SWD-166 | Task | [Iterate] Sidebar dynamics block editor + toy setup guide | Done | Relates SWD-143 | docs/ITERATE.md | Done — shipped PR #68 (App 0.1.25) |
| SWD-167 | Task | [Iterate] Per-equation state/measurement authoring + exposed block dynamics | Done | Relates SWD-166 | docs/ITERATE.md | Done — shipped PR #69 (App 0.1.26) |
| SWD-168 | Task | [Iterate] Show Restart required on Settings updates page after PLCAssistant integration sync | Done | Relates SWD-138 | docs/ITERATE.md | Done — shipped PR #70 (App 0.1.27) |
| SWD-169 | Bug | [Iterate] Integration dashboard plant level/flow values unavailable | Done | Relates SWD-146 | docs/ITERATE.md | Done — shipped PR #71 (App 0.1.28) |
| SWD-170 | Bug | [Iterate] Operate plant PVs still unavailable after 0.1.28 BOX hydrate | Done | Relates SWD-169 | docs/ITERATE.md | Done — shipped PR #72 (App 0.1.29) |
| SWD-171 | Bug | [Iterate] Tank level settles away from setpoint (Soft-PLC plant IN silent) | Done | Relates SWD-170 | docs/ITERATE.md | Done — shipped PR #73 (App 0.1.30) |
| SWD-173 | Bug | [Iterate] Soft-PLC stuck TRIPPED after settle — stale plant file LOS | Done | Relates SWD-171 | docs/ITERATE.md | Done — shipped PR #74 (App 0.1.31) |
| SWD-178 | Story | Industrial-parity Soft-PLC programming surface (multi-program) | To Do | — | docs/ROADMAP.md, docs/RESEARCH.md, docs/PLAN.md | `/define SWD-191` |
| SWD-179 | Task | Research: industrial PLC program organization & engineering UI capabilities | Done | Relates SWD-178, SWD-173 | docs/RESEARCH.md | Done — PR [#75](https://github.com/marcuskrogh/PLCAssistant/pull/75) |
| SWD-182 | Task | Soft-PLC program organization model (tasks → programs → instances) | Done | Relates SWD-178; blocked by SWD-179 | docs/PLAN.md | Done — shipped PR [#76](https://github.com/marcuskrogh/PLCAssistant/pull/76) (App 0.1.32) |
| SWD-187 | Sub-task | SWD-182: Schema + legacy Program migration | Done | SWD-182 | docs/PLAN.md | — |
| SWD-185 | Sub-task | SWD-182: Runtime Task passes + apply policy | Done | SWD-182 | docs/PLAN.md | — |
| SWD-188 | Sub-task | SWD-182: Wedge tank Program under Main Task | Done | SWD-182 | docs/PLAN.md | — |
| SWD-189 | Sub-task | SWD-182: Minimal App/API project tree JSON | Done | SWD-182 | docs/PLAN.md | — |
| SWD-186 | Sub-task | SWD-182: Unit + integration + system tests (HA/App/MQTT) | Done | SWD-182 | docs/PLAN.md | — |
| SWD-181 | Task | App engineering surface (Program cards + Diagram/Log/Settings) | Done | Relates SWD-178; blocked by SWD-182 | docs/PLAN.md | Done — shipped PR [#77](https://github.com/marcuskrogh/PLCAssistant/pull/77) (App 0.1.33) |
| SWD-190 | Subtask | SWD-181: Main Program cards overview | Done | SWD-181 | docs/PLAN.md | — |
| SWD-192 | Subtask | SWD-181: Program shell Diagram\|Log\|Settings + Back | Done | SWD-181 | docs/PLAN.md | — |
| SWD-194 | Subtask | SWD-181: Create + Settings pages | Done | SWD-181 | docs/PLAN.md | — |
| SWD-195 | Subtask | SWD-181: Diagram binding + Hot Apply | Done | SWD-181 | docs/PLAN.md | — |
| SWD-193 | Subtask | SWD-181: unit + integration + system tests | Done | SWD-181 | docs/PLAN.md | — |
| SWD-191 | Task | Define Task/Program scheduling editor | To Do | Relates SWD-178; blocked by SWD-181 | docs/ROADMAP.md | `/define SWD-191` |
| SWD-180 | Task | Define library inspectability + generic PID | To Do | Relates SWD-178; blocked by SWD-182 | docs/ROADMAP.md | `/define SWD-180` (parallel after SWD-182) |
| SWD-184 | Task | Define integration multi-datablock tag mapping UI | To Do | Relates SWD-178; blocked by SWD-182 | docs/ROADMAP.md | `/define SWD-184` (parallel after SWD-182) |
| SWD-183 | Task | Define online / runtime visibility (loaded vs running) | To Do | Relates SWD-178; blocked by SWD-181 | docs/ROADMAP.md | `/define SWD-183` (after SWD-181) |

## Log

- 2026-08-01 — Shipped SWD-181 via PR #77 (App 0.1.33); review-fix CLEAN after 3 iters; Task Done; Next `/define SWD-191`.
- 2026-08-01 — Define SWD-181 approved + ship: PLAN.md; Sub-tasks SWD-190/192/194/195/193; scheduling follow-on SWD-191; branch `cursor/swd-181-app-engineering-surface-a52c`. Remaining: implement → review-fix → closeout.
- 2026-08-01 — Shipped SWD-182 via PR #76 (App 0.1.32); review-fix CLEAN after 2 iters; Task Done; Next `/define SWD-181`.
- 2026-08-01 — review-fix SWD-182 CLEAN after 2 iterations (iter1: 4SF scan_period/MQTT/system/403; iter2: 0); closeout.
- 2026-08-01 — Define SWD-182 approved: PLAN.md + Sub-tasks SWD-187/185/188/189/186; branch `cursor/swd-182-softplc-program-model-a52c`. Next `/implement SWD-182`.
- 2026-08-01 — Explore SWD-178 charted: route SWD-179→182→{181,180,184}; 181→183; frontier `/define SWD-182`.
- 2026-08-01 — Research SWD-179: industrial PLC program/UI capabilities → `docs/RESEARCH.md`; Story SWD-178; draft PR [#75](https://github.com/marcuskrogh/PLCAssistant/pull/75). Next `/explore SWD-178`.
- 2026-07-30 — Shipped SWD-173 via PR #74 (App 0.1.31); review-fix CLEAN after 3 iters; Task Done.
- 2026-07-30 — review-fix SWD-173 CLEAN after 3 iterations (iter1: 2SF heartbeat/PyYAML; iter2: 1B+2SF aged-BAD/status-flip/tests; iter3: 0); closeout.
- 2026-07-30 — Implement SWD-173: App 0.1.31; hold last-good on stale plant file + plant heartbeat; PR [#74](https://github.com/marcuskrogh/PLCAssistant/pull/74) → In Review. Next `/review-fix SWD-173`.
- 2026-07-30 — Iterate SWD-173: Soft-PLC stuck TRIPPED after settle (stale plant file LOS from SWD-171); Relates SWD-171.
- 2026-07-30 — Shipped SWD-171 via PR #73 (App 0.1.30); review-fix CLEAN after 2 iters; Task Done.
- 2026-07-30 — review-fix SWD-171 CLEAN after 2 iterations (iter1: 4SF lock/stale/coerce/file-before-mqtt; iter2: 0); closeout.
- 2026-07-30 — Implement SWD-171: App 0.1.30; plant IN file-bridge + settle regression + GitHub Actions CI; PR [#73](https://github.com/marcuskrogh/PLCAssistant/pull/73) → In Review. Next `/review-fix SWD-171`.
- 2026-07-30 — Iterate SWD-171: tank settles away from Active level SP when MQTT plant→Soft-PLC silent; Relates SWD-170.
- 2026-07-30 — Shipped SWD-170 via PR #72 (App 0.1.29); review-fix CLEAN after 2 iters; Task Done.
- 2026-07-30 — review-fix SWD-170 CLEAN after 2 iterations (iter1: SP_LEVEL_REQ unique_id/purge/run.sh/tests; iter2: 0); closeout.
- 2026-07-30 — Implement SWD-170: App 0.1.29; plant IN Sensors + in_values + Lovelace Process sensors; PR [#72](https://github.com/marcuskrogh/PLCAssistant/pull/72) → In Review. Next `/review-fix SWD-170`.
- 2026-07-30 — Iterate SWD-170: App 0.1.29; plant IN Sensors + in_values cache + Lovelace Process sensors; Relates SWD-169.
- 2026-07-30 — Shipped SWD-169 via PR #71 (App 0.1.28); review-fix CLEAN after 2 iters; Task Done.
- 2026-07-30 — review-fix SWD-169 CLEAN after 2 iterations (iter1: isfinite+hydrate except; iter2: 0); closeout.
- 2026-07-30 — Implement SWD-169: App 0.1.28; plant IN BOX + hydrate/bus; PR [#71](https://github.com/marcuskrogh/PLCAssistant/pull/71) → In Review. Next `/review-fix SWD-169`.
- 2026-07-30 — Iterate SWD-169: App 0.1.28; plant IN Number BOX mode + hydrate/bus; Relates SWD-146.
- 2026-07-30 — Shipped SWD-168 via PR #70 (App 0.1.27); review-fix CLEAN after 2 iters; Task Done.
- 2026-07-30 — review-fix SWD-168 CLEAN after 2 iterations (iter1: docs/manifest/repair; iter2: 0); closeout.
- 2026-07-30 — Implement SWD-168: App 0.1.27; Update entity + repair; PR [#70](https://github.com/marcuskrogh/PLCAssistant/pull/70) → In Review. Next `/review-fix SWD-168`.
- 2026-07-30 — Iterate SWD-168: App 0.1.27; Update entity + repair for Restart required on Settings → Updates; Relates SWD-138.
- 2026-07-30 — Shipped SWD-167 via PR #69 (App 0.1.26); review-fix CLEAN after 1 iter; Task Done.
- 2026-07-30 — Implement SWD-167: App 0.1.26; per-row state/measurement equations + catalog dynamics exposure; Next `/review-fix SWD-167`.
- 2026-07-30 — Iterate SWD-167: per-equation state/measurement UX + expose catalog dynamics; App 0.1.26; Relates SWD-166.
- 2026-07-30 — Shipped SWD-166 via PR #68 (App 0.1.25); review-fix CLEAN after 1 iter; Task Done.
- 2026-07-30 — Iterate SWD-166: sidebar Dynamics block editor + toy README guide; App 0.1.25; Relates SWD-143.
- 2026-07-30 — Shipped SWD-143 via PR #66 (App 0.1.24); review-fix CLEAN after 1 iter; Task Done; Story SWD-142 → Done (initiative complete).
- 2026-07-30 — Implement SWD-143: App 0.1.24; Options flow + set_dynamics_preset + preset sensor; Next `/review-fix SWD-143`.
- 2026-07-30 — Define SWD-143: PLAN.md + Sub-tasks SWD-162/163/164/165; Options flow + options SoT + service; Next `/implement SWD-143` (ship requested).
- 2026-07-30 — Shipped SWD-144 via PR #65 (App 0.1.23); review-fix CLEAN after 1 iter (README); Task Done; Next `/define SWD-143`.
- 2026-07-30 — Implement SWD-144: App 0.1.23; unit-ops + AST sandbox + skid_composed oracle; PR #65 → In Review. Next `/review-fix SWD-144`.
- 2026-07-30 — Define SWD-144: PLAN.md + Sub-tasks SWD-157/159/158/160/161; unit-ops compile → ModelSpec + AST sandbox; Next `/implement SWD-144`.
- 2026-07-29 — Shipped SWD-146 via PR #63 (App 0.1.22); review-fix CLEAN after 1 iter (retained-status hydrate + docs); Task Done; Next `/define SWD-144`.
- 2026-07-29 — Define SWD-146: PLAN.md + Sub-tasks SWD-156/154/152/155/153; integration dynamics core + skid preset; Next `/implement SWD-146`.
- 2026-07-29 — Shipped SWD-145 via PR #59 (0.1.20) + PR #60 (0.1.21 review-fix CLEAN 2 iter); Task Done; Next `/define SWD-146`.
- 2026-07-29 — review-fix SWD-145 CLEAN after 2 iterations (iter1: 1B+4SF LOS/LWT/file/docs/tests; iter2: 0); Next `/ship SWD-145`.
- 2026-07-29 — review-fix SWD-145 NEEDS FIXES (1B LOS forced GOOD + 4SF); App 0.1.21 follow-up; premature ship of #59 noted.
- 2026-07-29 — Premature ship attempt of SWD-145 via PR #59 (0.1.20); user requested review-fix first — reopened.
- 2026-07-29 — Implement SWD-145: App 0.1.20; HeldProcess + plant IN; scan_period_s; PR #59 → In Review. Next `/review-fix SWD-145`.
- 2026-07-29 — Define SWD-145 approved: PLAN.md + Sub-tasks SWD-149/150/147/148/151; PR #59; Next `/implement SWD-145`.
- 2026-07-29 — Define SWD-145 started: Soft-PLC ↔ integration mock ownership; awaiting first divergence (where ODE runs).
- 2026-07-29 — Explore SWD-142: configurable mock dynamics (unit ops, custom ODEs, presets, integration UI); themes SWD-145/146/144/143; Next `/define SWD-145`.
- 2026-07-29 — Shipped SWD-141 via PR #57; App 0.1.19 file-bridge SP_LEVEL_REQ → Active level SP. Bug Done.
- 2026-07-29 — review-fix SWD-141 CLEAN after 2 iterations (iter1: 3B write_input_tag kwonly; iter2: 0); Next `/ship SWD-141`.
- 2026-07-29 — Iterate SWD-141: PR #57 opened (App 0.1.19); file-bridge SP_LEVEL_REQ inputs.json; Task → In Review.
- 2026-07-29 — Iterate SWD-141: Level setpoint (SP_LEVEL_REQ) stuck vs Active SP; file-bridge inputs.json; App 0.1.19.
- 2026-07-29 — Shipped SWD-140 via PR #56; App 0.1.18 file-bridge SP/LT_RES + Start-ready HMI. Bug Done.
- 2026-07-29 — review-fix SWD-140 CLEAN after 2 iterations (iter1: 0B+3SF run.sh/README; iter2: 0); Next `/ship SWD-140`.
- 2026-07-29 — Iterate SWD-140: PR #56 opened (App 0.1.18); file-bridge SP/LT_RES + Start-ready help; Task → In Review.
- 2026-07-29 — Iterate SWD-140: HMI zeros on SP/LT_RES + PERM_OK Off while RUNNING expected; file-bridge tags + Start-ready help; App 0.1.18.
- 2026-07-29 — Shipped SWD-139 via PR #55; App 0.1.17 HA-config file bridge for MQTT-silent HMI. Bug Done.
- 2026-07-29 — review-fix SWD-139 CLEAN after 2 iterations (iter1: 0B+1SF MQTT primary gate; iter2: 0); Next `/ship SWD-139`.
- 2026-07-29 — Iterate SWD-139: Soft-PLC attached but HMI offline; shared HA-config file bridge; App 0.1.17.
- 2026-07-29 — Shipped SWD-138 via PR #53; App 0.1.16 auto Core restart after thin-integration sync. Bug Done.
- 2026-07-29 — review-fix SWD-138 CLEAN after 1 iteration (0B+0SF+1N packaging wording fixed); Next `/ship SWD-138`.
- 2026-07-29 — Iterate SWD-138: PR #53 opened (App 0.1.16); auto Core restart after thin-integration sync; Task → In Review.
- 2026-07-29 — Iterate SWD-138: Soft-PLC attached (0.1.15 log) but HMI offline; auto Core restart after thin-integration sync; App 0.1.16.
- 2026-07-29 — Shipped SWD-137 via PR #52; App 0.1.15 empty-options MQTT attach + retain HMI OUT. Bug Done.
- 2026-07-29 — review-fix SWD-137 CLEAN after 3 iterations (iter1: 0B+3SF race/Lovelace/docs; iter2: 0B+3SF HA attach/_alive; iter3: 0); Next `/ship SWD-137`.
- 2026-07-29 — Iterate SWD-137: PR #52 opened (App 0.1.15); empty options MQTT attach; Task → In Review.
- 2026-07-29 — Iterate SWD-137: Soft-PLC still offline after 0.1.14; empty options skipped MQTT; App 0.1.15.
- 2026-07-29 — Shipped SWD-136 via PR #51; App 0.1.14 status cache/hydrate + heartbeat/LWT. Bug Done.
- 2026-07-29 — review-fix SWD-136 CLEAN after 2 iterations (iter1: 0B+3SF status churn/heartbeat test/LWT coverage; iter2: 0); Next `/ship SWD-136`.
- 2026-07-29 — Iterate SWD-136: PR #51 opened (App 0.1.14); status cache+hydrate, heartbeat, LWT; Task → In Review.
- 2026-07-29 — Iterate SWD-136: Soft-PLC HMI stuck offline / Start noop after 0.1.13; status cache+hydrate, heartbeat, LWT; App 0.1.14.
- 2026-07-29 — Shipped SWD-135 via PR #49; App 0.1.13 Lovelace status + Start/MODE wiring. Bug Done.
- 2026-07-29 — Iterate SWD-135: PR #49 opened (App 0.1.13); Lovelace status + Start/MODE wiring; Task → In Review.
- 2026-07-29 — Iterate SWD-135: Lovelace status at top + Start/MODE MQTT wiring; App 0.1.13.
- 2026-07-29 — Shipped SWD-134 via PR #47; App 0.1.12 auto-registers Lovelace sidebar dashboard (no copy/paste). Bug Done.
- 2026-07-29 — review-fix SWD-134 CLEAN after 2 iterations (iter1: HA import fragility + run.sh no-clobber test; iter2: 0); Next `/ship SWD-134`.
- 2026-07-29 — Iterate SWD-134: auto-register PLCAssistant Lovelace dashboard in HA sidebar; App 0.1.12.
- 2026-07-29 — Shipped SWD-133 via PR #46; App 0.1.11 Lovelace HMI + Skid plant + writable SP_LEVEL_REQ. Bug Done.
- 2026-07-29 — review-fix SWD-133 CLEAN after 2 iterations (iter1: reset semantics + entity_ids/migration; iter2: 0); Next `/ship SWD-133`.
- 2026-07-29 — Iterate SWD-133: PR #46 opened (App 0.1.11); Lovelace HMI + Skid plant + writable SP_LEVEL_REQ; Task → In Review.
- 2026-07-29 — Iterate SWD-133: Lovelace HMI (not App SCADA), writable SP_LEVEL_REQ, Skid plant on Start; App 0.1.11.
- 2026-07-29 — Shipped SWD-132 via PR #44; App 0.1.10 operator dashboard + UI refresh; cmd enqueue + offline intent. Bug Done.
- 2026-07-29 — review-fix SWD-132 CLEAN after 3 iterations (iter1: cmd race/offline/tests/arch/spec; iter2: stop-vs-late-connect + OperatorRuntime; iter3: 0); Next `/ship SWD-132`.
- 2026-07-28 — Iterate SWD-132: PR #44 opened (App 0.1.10); operator dashboard + UI refresh; Task → In Review.
- 2026-07-28 — Iterate SWD-132: operator dashboard default + major App UI refresh; App 0.1.10; `/api/runtime` + `/api/cmd`.
- 2026-07-28 — Shipped SWD-131 via PR #43; App 0.1.9 Ingress relative API + version lock + FT_INLET/buttons. Bug Done.
- 2026-07-28 — review-fix SWD-131 CLEAN after 2 iterations (iter1: 0B+3SF apiUrl/tests/bindings; iter2: 0); Next `/ship SWD-131`.
- 2026-07-28 — Iterate SWD-131: PR #43 opened (App 0.1.9); Ingress relative API, version lock, FT_INLET + buttons; Task → In Review.
- 2026-07-28 — Iterate SWD-131: Ingress Block Editor 404 (absolute `/api`), App↔integration version lock 0.1.9, expand mock tags (incl. FT_INLET) + Start/Stop/Reset buttons.
- 2026-07-28 — Shipped SWD-130 via PR #42; App 0.1.8 pins `#main` + stuck-Latest recovery docs. Bug Done.
- 2026-07-28 — Iterate SWD-130: HA Latest stuck at 0.1.6 while GitHub has newer; pin `#main`, document store/update-entity recovery, bump App 0.1.8.
- 2026-07-28 — Shipped SWD-129 via PR #41; App 0.1.7 cache-busts Docker layers + migrates leftover hass.components thin integration. Bug Done.
- 2026-07-28 — Iterate SWD-129: Update leaves installed version stuck; reinstall still loads pre-0.1.5 `hass.components` integration (stale Docker layers). Dockerfile BUILD_VERSION cache-bust + runtime migration + force-sync; bump 0.1.7.
- 2026-07-28 — Shipped SWD-128 via PR #40; App 0.1.6 hardens start against Supervisor job-group configure races. Bug Done; SWD-84/SWD-81 remain Done.
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
