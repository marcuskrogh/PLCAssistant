# Issues

Continuity mirror for Jira (`SWD`). Upsert rows when issues are created, transitioned, or handed off.

| Key | Type | Title | Status | Parent | Artifact | Next |
|-----|------|-------|--------|--------|----------|------|
| SWD-373 | Task | Isolate PID faceplate elements for sandbox iteration | In Review | Relates SWD-368, SWD-369 | docs/PLAN.md | `/review-fix SWD-373` |
| SWD-374 | Subtask | SWD-373: Shared faceplate elements module + Lovelace wiring | Done | SWD-373 | docs/PLAN.md, custom_components/plcassistant/www/pid-faceplate-elements.js | — |
| SWD-375 | Subtask | SWD-373: Isolated element sandbox (no HA/App) | Done | SWD-373 | docs/PLAN.md, tools/pid-faceplate/ | — |
| SWD-376 | Subtask | SWD-373: Tests, docs, dual-tree, App 0.1.59 | Done | SWD-373 | docs/PLAN.md, tests/test_swd373_acceptance.py | — |
| SWD-368 | Story | ISA-101 / DCS-standard PID faceplates | Done | Relates SWD-366 | docs/ROADMAP.md, docs/RESEARCH.md | Done — shipped PR [#104](https://github.com/marcuskrogh/PLCAssistant/pull/104) |
| SWD-369 | Task | Define & ship ISA-101 DCS PID faceplate | Done | Relates SWD-368 | docs/PLAN.md | Done — shipped PR [#104](https://github.com/marcuskrogh/PLCAssistant/pull/104) |
| SWD-370 | Subtask | SWD-369: Controller-mode contract + CO_MAN + auto/uman wiring | Done | SWD-369 | docs/PLAN.md, plcassistant/io/pid_loop.py | — |
| SWD-371 | Subtask | SWD-369: Lovelace analog-controller PID card | Done | SWD-369 | docs/PLAN.md, custom_components/plcassistant/www/pid-loop-card.js | — |
| SWD-372 | Subtask | SWD-369: Tests, docs, dual-tree, App 0.1.58 | Done | SWD-369 | docs/PLAN.md, tests/test_swd369_acceptance.py | — |
| SWD-367 | Task | Iterate: Align builtin PID with IFAC 2024 reference implementation | Done | Relates SWD-360, SWD-366 | docs/ITERATE.md | Done — shipped PR [#103](https://github.com/marcuskrogh/PLCAssistant/pull/103) |
| SWD-366 | Task | Iterate: Lovelace PID cards ISA-5.1 look and ISA-101 highlighting | Done | Relates SWD-360 | docs/ITERATE.md | Done — shipped PR [#102](https://github.com/marcuskrogh/PLCAssistant/pull/102) |
| SWD-359 | Story | Standardised PID blocks — ISA visualisation and structure | Done | — | docs/ROADMAP.md, docs/RESEARCH.md | Done — shipped PR [#101](https://github.com/marcuskrogh/PLCAssistant/pull/101) |
| SWD-360 | Task | Define & ship standardised PID visualisation and structure | Done | Relates SWD-359 | docs/PLAN.md | Done — shipped PR [#101](https://github.com/marcuskrogh/PLCAssistant/pull/101) |
| SWD-361 | Subtask | SWD-360: ISA-5.1 three-mode PID glyph on App Diagram | Done | SWD-360 | docs/PLAN.md, plcassistant/app/_canvas.py | — |
| SWD-362 | Subtask | SWD-360: ISA-TR5.9 / Bauer PID pin and parameter contract | Done | SWD-360 | docs/PLAN.md, docs/surface/03-builtin-library.md | — |
| SWD-363 | Subtask | SWD-360: Hybrid incremental/positional PID algorithm | Done | SWD-360 | docs/PLAN.md, plcassistant/surface/builtin.py | — |
| SWD-364 | Subtask | SWD-360: Faceplate and Datablock PV/SP/CO alignment | Done | SWD-360 | docs/PLAN.md, docs/io/06-pid-faceplate.md | — |
| SWD-365 | Subtask | SWD-360: Tests, docs, and App version | Done | SWD-360 | docs/PLAN.md, tests/ | — |
| SWD-252 | Task | Cloud agents refresh marcuskrogh/skills on every boot | Done | — | AGENTS.md, .cursor/environment.json | Done — shipped PR [#100](https://github.com/marcuskrogh/PLCAssistant/pull/100) |
| SWD-251 | Bug | [Iterate] Simplify pump flow limits — one capacity knob that stays in sync | Done | Relates SWD-250 | docs/ITERATE.md | Done — shipped PR [#99](https://github.com/marcuskrogh/PLCAssistant/pull/99) (App 0.1.54) |
| SWD-250 | Bug | PID diagram clipping + wrong CV max; model settings hard to edit | Done | Relates SWD-249 | docs/BUG.md | Done — shipped PR [#98](https://github.com/marcuskrogh/PLCAssistant/pull/98) (App 0.1.53) |
| SWD-249 | Bug | One-tank Diagram empty; mobile cannot place blocks | Done | Relates SWD-237 | docs/BUG.md | Done — shipped PR [#97](https://github.com/marcuskrogh/PLCAssistant/pull/97) (App 0.1.52) |
| SWD-237 | Bug | App UI: card click, empty diagram, place blocks, built-in labels, code formatting | Done | — | docs/BUG.md | Done — shipped PR [#96](https://github.com/marcuskrogh/PLCAssistant/pull/96) (App 0.1.51) |
| SWD-231 | Story | Cloud HA live integration & system tests (App ↔ thin integration) | Done | — | docs/ROADMAP.md | Done — initiative complete (PR [#95](https://github.com/marcuskrogh/PLCAssistant/pull/95)) |
| SWD-232 | Task | Define & ship live cloud HA integration/system test suite | Done | Relates SWD-231 | docs/PLAN.md | Done — shipped PR [#95](https://github.com/marcuskrogh/PLCAssistant/pull/95) |
| SWD-233 | Subtask | SWD-232: Live stack fixtures + clients | Done | SWD-232 | docs/PLAN.md, tests/live/ | — |
| SWD-234 | Subtask | SWD-232: Live integration tests (App ↔ integration) | Done | SWD-232 | docs/PLAN.md, tests/live/ | — |
| SWD-235 | Subtask | SWD-232: Live system tests (e2e stack) | Done | SWD-232 | docs/PLAN.md, tests/live/ | — |
| SWD-236 | Subtask | SWD-232: Docs + run_live_tests script | Done | SWD-232 | docs/PLAN.md, .cursor/ha/ | — |
| SWD-230 | Bug | [Iterate] PID cards: match Lovelace fonts/sizes + force 2dp on all values | Done | Relates SWD-229 | docs/ITERATE.md | Done — shipped PR [#93](https://github.com/marcuskrogh/PLCAssistant/pull/93) (App 0.1.50) |
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
| SWD-178 | Story | Industrial-parity Soft-PLC programming surface (multi-program) | Done | — | docs/ROADMAP.md, docs/RESEARCH.md, docs/PLAN.md | Done — initiative complete |
| SWD-183 | Task | Online / runtime visibility + PID HMI faceplates | Done | Relates SWD-178; blocked by SWD-181 | docs/PLAN.md | Done — shipped PR [#81](https://github.com/marcuskrogh/PLCAssistant/pull/81) (App 0.1.38) |
| SWD-219 | Bug | [Iterate] Integration setup fails: No module named plcassistant.io | Done | Relates SWD-183 | docs/ITERATE.md | Done — shipped PR [#82](https://github.com/marcuskrogh/PLCAssistant/pull/82) (App 0.1.39) |
| SWD-221 | Bug | [Iterate] Cascade reliability: HA freeze, Start path, Level Man / Flow Auto defaults | Done | Relates SWD-220 | docs/ITERATE.md | Done — shipped PR [#84](https://github.com/marcuskrogh/PLCAssistant/pull/84) (App 0.1.41) |
| SWD-222 | Bug | [Iterate] Start/cascade dead, Start–Stop unresponsive, PID setpoints, HA lockup | Done | Relates SWD-221 | docs/ITERATE.md | Done — shipped PR [#85](https://github.com/marcuskrogh/PLCAssistant/pull/85) (App 0.1.42) |
| SWD-223 | Bug | [Iterate] Level/Flow PID Manual SP does not drive CV (post 0.1.42) | Done | Relates SWD-222 | docs/ITERATE.md | Done — shipped PR [#86](https://github.com/marcuskrogh/PLCAssistant/pull/86) (App 0.1.43) |
| SWD-224 | Bug | [Iterate] Start does not drive PID CVs — unify tag↔pin wirings | Done | Relates SWD-223 | docs/ITERATE.md | Done — shipped PR [#87](https://github.com/marcuskrogh/PLCAssistant/pull/87) (App 0.1.44) |
| SWD-225 | Bug | [Iterate] Start still leaves PID CVs at 0 (post 0.1.44) | Done | Relates SWD-224 | docs/ITERATE.md | Done — shipped PR #88 |
| SWD-226 | Bug | [Iterate] PID card SP edit bugs + climate-inspired visual refresh | Done | Relates SWD-225 | docs/ITERATE.md | Done — shipped PR #89 |
| SWD-227 | Bug | [Iterate] PID card Set SP fails — expected float (data-mode click hijack) | Done | Relates SWD-226 | docs/ITERATE.md | Done — shipped PR [#90](https://github.com/marcuskrogh/PLCAssistant/pull/90) (App 0.1.47) |
| SWD-228 | Bug | [Iterate] PID card compact redesign: 2dp KPIs, single-row mobile, more-info popup | Done | Relates SWD-227 | docs/ITERATE.md | Done — shipped PR [#91](https://github.com/marcuskrogh/PLCAssistant/pull/91) (App 0.1.48) |
| SWD-229 | Bug | [Iterate] Lovelace Operate: SCADA-style declutter (not every entity) | Done | Relates SWD-228 | docs/ITERATE.md | Done — shipped PR [#92](https://github.com/marcuskrogh/PLCAssistant/pull/92) (App 0.1.49) |
| SWD-220 | Bug | [Iterate] PID cards Configuration error + default mode Remote (should be Manual) | Done | Relates SWD-219 | docs/ITERATE.md | Done — shipped PR [#83](https://github.com/marcuskrogh/PLCAssistant/pull/83) (App 0.1.40) |
| SWD-217 | Subtask | SWD-183: PID SP-source mode logic + Datablock tag contract | Done | SWD-183 | docs/PLAN.md | — |
| SWD-214 | Subtask | SWD-183: HA compound PID loop entity platform | Done | SWD-183 | docs/PLAN.md | — |
| SWD-215 | Subtask | SWD-183: Lovelace PID card + generic list card | Done | SWD-183 | docs/PLAN.md | — |
| SWD-213 | Subtask | SWD-183: Soft-PLC App online visibility | Done | SWD-183 | docs/PLAN.md | — |
| SWD-218 | Subtask | SWD-183: Demo rebuild + docs | Done | SWD-183 | docs/PLAN.md | — |
| SWD-216 | Subtask | SWD-183: unit + integration + system tests | Done | SWD-183 | docs/PLAN.md | — |

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
| SWD-191 | Task | Task/Program scheduling editor | Done | Relates SWD-178; blocked by SWD-181 | docs/PLAN.md | Done — shipped PR [#78](https://github.com/marcuskrogh/PLCAssistant/pull/78) (App 0.1.34) |
| SWD-196 | Subtask | SWD-191: Schema + persist/apply split | Done | SWD-191 | docs/PLAN.md | — |
| SWD-199 | Subtask | SWD-191: Task editor API | Done | SWD-191 | docs/PLAN.md | — |
| SWD-200 | Subtask | SWD-191: App UI top nav + Task editor | Done | SWD-191 | docs/PLAN.md | — |
| SWD-197 | Subtask | SWD-191: Wire Program cards status after Apply | Done | SWD-191 | docs/PLAN.md | — |
| SWD-198 | Subtask | SWD-191: unit + integration + system tests | Done | SWD-191 | docs/PLAN.md | — |
| SWD-180 | Task | Library inspectability + generic PID | Done | Relates SWD-178; blocked by SWD-182 | docs/PLAN.md | Done — shipped PR [#79](https://github.com/marcuskrogh/PLCAssistant/pull/79) (App 0.1.35) |
| SWD-203 | Subtask | SWD-180: Equation runtime + PID template | Done | SWD-180 | docs/PLAN.md | — |
| SWD-202 | Subtask | SWD-180: Copy-on-place + instance equation storage | Done | SWD-180 | docs/PLAN.md | — |
| SWD-205 | Subtask | SWD-180: Migrate level_pi/flow_pi to PID copies | Done | SWD-180 | docs/PLAN.md | — |
| SWD-206 | Subtask | SWD-180: Library editor UI + API | Done | SWD-180 | docs/PLAN.md | — |
| SWD-201 | Subtask | SWD-180: Diagram instance equation editor | Done | SWD-180 | docs/PLAN.md | — |
| SWD-204 | Subtask | SWD-180: unit + integration + system tests | Done | SWD-180 | docs/PLAN.md | — |
| SWD-184 | Task | Integration Datablock tag mapping UI | Done | Relates SWD-178; blocked by SWD-182 | docs/PLAN.md | Done — shipped PR [#80](https://github.com/marcuskrogh/PLCAssistant/pull/80) (App 0.1.36) |
| SWD-209 | Subtask | SWD-184: Datablock model + schema | Done | SWD-184 | docs/PLAN.md | — |
| SWD-208 | Subtask | SWD-184: Program ↔ Datablock access + tag visibility | Done | SWD-184 | docs/PLAN.md | — |
| SWD-210 | Subtask | SWD-184: HA configuration panel (Datablock CRUD) | Done | SWD-184 | docs/PLAN.md | — |
| SWD-207 | Subtask | SWD-184: Rebuild example Datablock + demo Program | Done | SWD-184 | docs/PLAN.md | — |
| SWD-212 | Subtask | SWD-184: Persistence + apply/reload into MQTT/image path | Done | SWD-184 | docs/PLAN.md | — |
| SWD-211 | Subtask | SWD-184: unit + integration + system tests | Done | SWD-184 | docs/PLAN.md | — |

## Log

- 2026-08-18 — Implement SWD-373: shared elements module + sandbox; App 0.1.59; PR [#105](https://github.com/marcuskrogh/PLCAssistant/pull/105) → In Review. Next `/review-fix SWD-373`.
- 2026-08-18 — Define SWD-373: isolate PID faceplate elements + sandbox; Relates SWD-368/369; Sub-tasks SWD-374..376; branch `cursor/swd-373-pid-faceplate-sandbox-a582`. Next `/implement SWD-373`.
- 2026-08-18 — Ship SWD-369: review-fix CLEAN + closeout; PR [#104](https://github.com/marcuskrogh/PLCAssistant/pull/104) (App 0.1.58) → Done.
- 2026-08-18 — review-fix SWD-369 CLEAN after 1 iter (pid_loop parse / seed-before-MODE=0 / persist CO_MAN). Next `/ship SWD-369` closeout.
- 2026-08-17 — Implement SWD-369: ISA-101 DCS PID faceplate (PV/SP bars, CO bar, MAN writes CO); App 0.1.58; PR [#104](https://github.com/marcuskrogh/PLCAssistant/pull/104) → In Review. Next `/review-fix SWD-369`.
- 2026-08-17 — Explore+research+define SWD-368/SWD-369: ISA-112 vs ISA-101; analog-controller geometry; PLAN on `cursor/swd-369-isa101-pid-faceplate-5304`.
- 2026-08-17 — Ship SWD-367: review-fix CLEAN + closeout; PR [#103](https://github.com/marcuskrogh/PLCAssistant/pull/103) (App 0.1.57) → Done.
- 2026-08-17 — Iterate SWD-367: IFAC 2024 incremental PID (filter, Tx, auto/uman, windup); Relates SWD-360/366; PR [#103](https://github.com/marcuskrogh/PLCAssistant/pull/103) (App 0.1.57) → In Review. Next `/review-fix SWD-367`.
- 2026-08-17 — Ship SWD-366: review-fix CLEAN + closeout; PR [#102](https://github.com/marcuskrogh/PLCAssistant/pull/102) (App 0.1.56) → Done.
- 2026-08-17 — Iterate SWD-366: Lovelace PID cards ISA-5.1 look + ISA-101 highlighting; Relates SWD-360; PR [#102](https://github.com/marcuskrogh/PLCAssistant/pull/102) (App 0.1.56) → In Review. Next `/review-fix SWD-366`.
- 2026-08-17 — Ship SWD-360: review-fix CLEAN + closeout; PR [#101](https://github.com/marcuskrogh/PLCAssistant/pull/101) (App 0.1.55) → Done.
- 2026-08-17 — review-fix SWD-360 CLEAN after 1 iter (uff/last_ep/shipped pins/docs/tests). Next `/ship SWD-360` closeout.
- 2026-08-17 — Implement SWD-360: ISA-5.1 PID glyph, TR5.9 Parallel + Bauer hybrid, faceplate CO, App 0.1.55; PR [#101](https://github.com/marcuskrogh/PLCAssistant/pull/101) → In Review. Next `/review-fix SWD-360`.
- 2026-08-17 — Explore+research+define SWD-359/SWD-360: ISA-5.1 / ISA-TR5.9 / Bauer PID blocks; ROADMAP + RESEARCH + PLAN; Sub-tasks SWD-361..365; Next `/implement SWD-360`.
- 2026-08-06 — Shipped SWD-252 via PR #100; review-fix CLEAN after 1 iter; Task Done.
- 2026-08-06 — review-fix SWD-252 CLEAN after 1 iter (start soft-fail sync so Mosquitto still boots; ISSUES In Review). Next `/ship SWD-252` closeout.
- 2026-08-06 — Implement SWD-252: cloud start sync for skills + prefer-workflow wiring; branch `swd-252-cloud-skills-boot-sync`. Next `/review-fix SWD-252`.
- 2026-08-04 — Shipped SWD-250 via PR #98 (App 0.1.53); review-fix CLEAN after 2 iters; Task Done.
- 2026-08-04 — review-fix SWD-250 CLEAN after 2 iters (iter1: version pins/repair-on-save/CTM/NaN/tests; iter2: 0). Next `/ship SWD-250` closeout.
- 2026-08-04 — Implement SWD-250: cascade cv_max repair + diagram viewBox + structured dynamics fields (App 0.1.53); PR [#98](https://github.com/marcuskrogh/PLCAssistant/pull/98) → In Review. Next `/review-fix SWD-250`.
- 2026-08-04 — Bug SWD-250: PID diagram clipping + CV max both 6 (flow should be 100); model settings JSON-only for `q_pump_max`; Relates SWD-249; branch `cursor/swd-250-pid-cvmax-model-9910`; docs/BUG.md. Next `/implement SWD-250`.
- 2026-08-04 — Shipped SWD-249 via PR #97 (App 0.1.52); review-fix CLEAN after 2 iters; Task Done.
- 2026-08-04 — review-fix SWD-249 CLEAN after 2 iters (iter1: dblclick/asymmetry/heuristics/tests; iter2: 0). Next `/ship SWD-249` closeout.
- 2026-08-04 — Implement SWD-249: heal empty demo programs + mobile tap-to-place (App 0.1.52); PR [#97](https://github.com/marcuskrogh/PLCAssistant/pull/97) → In Review. Next `/review-fix SWD-249`.
- 2026-08-04 — Bug SWD-249: one-tank Diagram empty + mobile place; Relates SWD-237; branch `cursor/swd-249-empty-diagram-1e05`; draft PR [#97](https://github.com/marcuskrogh/PLCAssistant/pull/97); docs/BUG.md. Next `/implement SWD-249`.
- 2026-08-03 — Shipped SWD-237 via PR #96 (App 0.1.51); review-fix CLEAN after 2 iters; Task Done.
- 2026-08-03 — review-fix SWD-237 CLEAN after 2 iters (iter1: library-card/layout/tests; iter2: 0). Next `/ship SWD-237` closeout.
- 2026-08-03 — Implement SWD-237: App UI cards/diagram/place/built-in/editors (App 0.1.51); PR [#96](https://github.com/marcuskrogh/PLCAssistant/pull/96) → In Review. Next `/review-fix SWD-237`.
- 2026-08-03 — Bug SWD-237: App UI cards/diagram/place/built-in/code formatting; branch `cursor/swd-237-app-ui-bugs-2b92`; docs/BUG.md. Next `/implement SWD-237`.
- 2026-08-02 — Shipped SWD-230 via PR #93 (App 0.1.50); review-fix CLEAN after 2 iters; Task Done.
- 2026-08-02 — review-fix SWD-230 CLEAN after 2 iters (iter1: 11SF null-err/Set-round/shared-precision/standards; iter2: 0). Next `/ship SWD-230`.
- 2026-08-02 — Implement SWD-230: PID Lovelace fonts + 2dp (App 0.1.50); PR [#93](https://github.com/marcuskrogh/PLCAssistant/pull/93) → In Review. Next `/review-fix SWD-230`.
- 2026-08-02 — Iterate SWD-230: PID Lovelace typography + 2dp everywhere (App 0.1.50); Relates SWD-229. Next `/review-fix SWD-230`.
- 2026-08-02 — Shipped SWD-229 via PR #92 (App 0.1.49); review-fix CLEAN after 2 iters; Task Done.
- 2026-08-02 — review-fix SWD-229 CLEAN after 2 iters (iter1: run.sh/docs/tests; iter2: 0). Next `/ship SWD-229`.
- 2026-08-02 — Implement SWD-229: Operate SCADA declutter (App 0.1.49 / dash 28); Relates SWD-228. Next `/review-fix SWD-229`.
- 2026-08-02 — Iterate SWD-229: Lovelace Operate should mimic SCADA (not every entity); Relates SWD-228.
- 2026-08-02 — Shipped SWD-228 via PR #91 (App 0.1.48); review-fix CLEAN after 2 iters; Task Done.
- 2026-08-02 — Implement SWD-228: compact PID faceplate (2dp, single-row KPIs, tap popup); App 0.1.48 / dash 27; PR [#91](https://github.com/marcuskrogh/PLCAssistant/pull/91) → In Review. Next `/review-fix SWD-228`.
- 2026-08-02 — Iterate SWD-228: Relates SWD-227; docs/ITERATE.md — compact redesign after 0.1.47.
- 2026-08-02 — Shipped SWD-227 via PR #90 (App 0.1.47); review-fix CLEAN after 2 iters; Task Done.
- 2026-08-02 — Fix-forward SWD-227: Node + pytest regression for HMI↔`number.set_value` float contract (PR #90). Next `/review-fix SWD-227`.
- 2026-08-02 — Implement SWD-227: PID Set SP data-mode hijack fix (App 0.1.47); PR [#90](https://github.com/marcuskrogh/PLCAssistant/pull/90) → In Review. Next `/review-fix SWD-227`.
- 2026-08-02 — Iterate SWD-227: PID card Set SP fails (data-mode click hijack → NaN); App 0.1.47; Relates SWD-226.
- 2026-08-02 — Shipped SWD-226 via PR #89 (App 0.1.46); review-fix CLEAN after 2 iters; Task Done.
- 2026-08-02 — Implement SWD-226: PID card SP edit + climate faceplate (App 0.1.46); PR [#89](https://github.com/marcuskrogh/PLCAssistant/pull/89) → In Review. Next `/review-fix SWD-226`.
- 2026-08-02 — Iterate SWD-226: PID card SP edit bugs + climate-inspired visual refresh (App 0.1.46); Relates SWD-225.
- 2026-08-02 — Shipped SWD-225 via PR #88 (App 0.1.45); review-fix CLEAN after 2 iters; Task Done.
- 2026-08-02 — Implement SWD-225: file mirror + Apply→Skid + cascade fallback (App 0.1.45); PR [#88](https://github.com/marcuskrogh/PLCAssistant/pull/88) → In Review. Next `/review-fix SWD-225`.
- 2026-08-02 — Iterate SWD-225: Start still leaves PID CVs at 0 after 0.1.44; file mirror + Apply→Skid (App 0.1.45); Relates SWD-224.
- 2026-08-02 — Shipped SWD-224 via PR #87 (App 0.1.44); review-fix CLEAN after 2 iters; CI green; Task Done.
- 2026-08-02 — Implement SWD-224: Start/PID io_wires + gain sync (App 0.1.44); PR [#87](https://github.com/marcuskrogh/PLCAssistant/pull/87) → In Review. Next `/review-fix SWD-224`.
- 2026-08-02 — Iterate SWD-224: Start does not drive PID CVs; unify tag↔pin io_wires + gain sync (App 0.1.44); Relates SWD-223.
- 2026-08-02 — Shipped SWD-223 via PR #86 (App 0.1.43); review-fix CLEAN; CI green; Task Done.
- 2026-08-01 — Implement SWD-223: Flow Manual drives CMD; Level CV=`SP_FLOW_AUTO` (App 0.1.43); PR [#86](https://github.com/marcuskrogh/PLCAssistant/pull/86) → In Review. Next `/review-fix SWD-223`.
- 2026-08-01 — Iterate SWD-223: Level/Flow Manual SP does not drive CV; Relates SWD-222.
- 2026-08-01 — Shipped SWD-222 via PR #85 (App 0.1.42); review-fix CLEAN; CI watchdog flake fixed; Task Done.
- 2026-08-01 — review-fix SWD-222 CLEAN after 2 iters (PR #85). Next `/ship SWD-222`.
- 2026-08-01 — Implement SWD-222: Start/cascade + plant load + PID mux/card (App 0.1.42); PR [#85](https://github.com/marcuskrogh/PLCAssistant/pull/85) → In Review. Next `/review-fix SWD-222`.
- 2026-08-01 — Iterate SWD-222: Start fails cascade, Start–Stop unresponsive, PID setpoints, HA lockup; Relates SWD-221.
- 2026-08-01 — Shipped SWD-221 via PR #84 (App 0.1.41); review-fix CLEAN after 2 iters; Task Done.
- 2026-08-01 — Implement SWD-221: cascade reliability Level Man / Flow Auto + no freeze (App 0.1.41); PR [#84](https://github.com/marcuskrogh/PLCAssistant/pull/84) → In Review. Next `/review-fix SWD-221`.
- 2026-08-01 — Iterate SWD-221: HA freeze + Level Man / Flow Auto cascade defaults (App 0.1.41); Relates SWD-220.
- 2026-08-01 — Shipped SWD-220 via PR #83 (App 0.1.40); review-fix CLEAN after 2 iters; Task Done.
- 2026-08-01 — Implement SWD-220: Lovelace resource registration + Manual SP-source default (App 0.1.40); PR [#83](https://github.com/marcuskrogh/PLCAssistant/pull/83) → In Review. Next `/review-fix SWD-220`.
- 2026-08-01 — Iterate SWD-220: PID cards Configuration error + mode Remote by default; Relates SWD-219; App 0.1.40.
- 2026-08-01 — Shipped SWD-219 via PR #82 (App 0.1.39); review-fix CLEAN after 1 iter; Task Done.
- 2026-08-01 — Implement SWD-219: HA-local Datablock catalog (App 0.1.39); PR [#82](https://github.com/marcuskrogh/PLCAssistant/pull/82) → In Review. Next `/review-fix SWD-219`.
- 2026-08-01 — Iterate SWD-219: HA Core setup fails ModuleNotFoundError plcassistant.io after 0.1.38; Relates SWD-183; App 0.1.39 HA-local Datablock catalog.
- 2026-08-01 — Shipped SWD-183 via PR #81 (App 0.1.38); review-fix CLEAN after 2 iters; Task Done; Story SWD-178 Done — initiative complete.
- 2026-08-01 — Implement SWD-183 complete (App 0.1.37): PID modes + compound entities + Lovelace cards + App online; Sub-tasks Done; Task → In Review; PR #81; Next `/review-fix SWD-183`.
- 2026-08-01 — Define SWD-183 approved: PLAN.md; Sub-tasks SWD-217/214/215/213/218/216; branch `cursor/swd-183-online-visibility-a52c`. Next `/implement SWD-183`.
- 2026-08-01 — Shipped SWD-184 via PR #80 (App 0.1.36); review-fix CLEAN after 2 iters; Task Done; Next `/define SWD-183`.
- 2026-08-01 — Implement SWD-184: Datablock model/catalog, Program access, HA Datablocks panel + store, DB_Tank example, App 0.1.36; pytest 530 passed. Next `/review-fix SWD-184`.
- 2026-08-01 — Define SWD-184 approved: PLAN.md; Sub-tasks SWD-209/208/210/207/212/211; branch `cursor/swd-184-datablock-mapping-a52c`. Next `/implement SWD-184`.
- 2026-08-01 — Shipped SWD-180 via PR #79 (App 0.1.35); review-fix CLEAN after 2 iters; Task Done; Next `/define SWD-184`.
- 2026-08-01 — Implement SWD-180: generic equation-driven PID, copy-on-place instances, library editor/API/persistence, migration, App 0.1.35; full pytest 521 passed. Next `/review-fix SWD-180`.
- 2026-08-01 — Define SWD-180 approved + ship: PLAN.md; Sub-tasks SWD-203/202/205/206/201/204; branch `cursor/swd-180-library-pid-a52c`. Remaining: implement → review-fix → closeout.
- 2026-08-01 — Shipped SWD-191 via PR #78 (App 0.1.34); review-fix CLEAN after 2 iters; Task Done; Next `/define SWD-180`.
- 2026-08-01 — Define SWD-191 approved + ship: PLAN.md; Sub-tasks SWD-196/199/200/197/198; branch `cursor/swd-191-task-scheduling-editor-a52c`. Remaining: implement → review-fix → closeout.
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
- 2026-08-04 — Iterate SWD-251: simplify pump flow limits (one Max pump flow knob + Soft-PLC sync); Relates SWD-250; branch `cursor/swd-251-simplify-pump-flow-limits-3043`; docs/ITERATE.md. PR [#99](https://github.com/marcuskrogh/PLCAssistant/pull/99) (App 0.1.54) → In Review. Next `/review-fix SWD-251`.
- 2026-08-04 — Implement SWD-251: one Max pump flow knob + Soft-PLC cascade sync (App 0.1.54); PR [#99](https://github.com/marcuskrogh/PLCAssistant/pull/99) → In Review. Next `/review-fix SWD-251`.
- 2026-08-04 — Ship SWD-251: review-fix CLEAN + closeout; PR [#99](https://github.com/marcuskrogh/PLCAssistant/pull/99) (App 0.1.54) → Done.
- 2026-08-04 — Merged SWD-251 PR #99 (`135ff27`) — App 0.1.54 Done.
