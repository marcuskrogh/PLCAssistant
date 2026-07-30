# Implementation plan: Unit-op library + custom equation authoring (SWD-144)

## Summary
- Extend the SWD-146 integration dynamics core so plant models are built from a **small unit-op catalog** plus optional **custom ODE expressions**, compiled into one collected `ModelSpec` and stepped by the existing fixed-step runner.
- Prove the path by **rebuilding the skid** from unit ops (oracle-parity with today’s code `skid` / `MockProcess`) while keeping Soft-PLC **mock-unaware**.
- Authoring is **HA-free + file/YAML first**; Home Assistant preset/parameter UI stays deferred to [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143).

## Scope
**In**
- Unit-op contract (states / params / inputs / algebraic or ODE contributions / projection hooks)
- v1 catalog derived from the skid: `tank`, `pump`, `orifice`, `lag`, plus `custom_ode`
- Compiler: unit-op instances + connections → one `ModelSpec` (collected RHS + `project`)
- Safe math-expression sandbox (AST whitelist) for `custom_ode` and any expression fields
- YAML/JSON **model document** schema + HA-free loader under `custom_components/plcassistant/dynamics/`
- Rebuild skid as a composed model document; register alongside code `skid`
- Widen `PlantSimulator` to `DynamicsModel` (not `SkidModel`-only); programmatic preset selection for tests
- Docs + tests (oracle parity, sandbox rejects unsafe code, loader validation)
- App + integration version bump (**0.1.23**)

**Out**
- Integration mock UI / preset chooser / live parameter editor → [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143)
- Soft-PLC block editor / surface programs for plant math (**mock ≠ PLC program**)
- Full chem-eng unit-op library beyond the skid-derived set
- Scan-edge lockstep; Soft-PLC programming/control/safety changes
- Persisted live plant state across Core restart (still reset to model initials)
- Unrestricted Python `exec` for plant equations

## Decisions
1. **Runtime SoT unchanged:** `ModelSpec` + `FixedStepRunner` remain the only stepper. Unit ops **compile** into one collected RHS/projection; they do not introduce a second solver.
2. **Composition model:** graph/list of unit-op instances + named connections → compiler → `ModelSpec`. Prefer compile-once at load; step path stays allocation-light.
3. **v1 catalog (skid decomposition):**
   - `tank` — level/inventory from net volumetric flow + clamps
   - `pump` — `CMD`/speed → flow with lag + optional low-level derate
   - `orifice` — `q = k * sqrt(max(h, 0))` (gravity drain)
   - `lag` — first-order lag (generic)
   - `custom_ode` — map of `state_key → d(state)/dt` expressions (and optional algebraic outs)
4. **Expression language:** math-only AST whitelist in the HA-free engine (names for state/input/param, `+ - * / **`, parentheses, unary minus; functions `sqrt`, `exp`, `min`, `max`, `abs`, `clamp`). No attribute access, imports, comprehensions, or arbitrary calls. **Not** Soft-PLC `BlockRuntime` / user-template `exec`.
5. **Persistence:** JSON (always) or YAML (when PyYAML present) model documents loaded by HA-free code. Live HA config-entry / UI ownership → SWD-143. Shipped composed-skid document: `dynamics/models/skid_composed.json`.
6. **Default live preset:** keep code `skid` as the `mock_mode=true` default for zero operator regression. Composed skid is registered as `skid_composed` for oracle/acceptance; UI selection → SWD-143.
7. **Typing:** `PlantSimulator.model` / `for_preset` speak `DynamicsModel`, not concrete `SkidModel`.
8. **Soft-PLC boundary locked:** plant math stays under `custom_components/plcassistant/dynamics/`. Do not import or invoke `plcassistant.surface` for plant. Soft-PLC stays `HeldProcess` + MQTT plant IN.
9. **Sandbox failure mode:** invalid/unsafe expressions fail at **load/compile** (clear error); never crash the HA plant task mid-scan. Already-running models are immutable until reload.
10. **Versioning:** model document includes a schema `version` string (`"1.0"`); loader accepts the v1 schema only until a later migration story.

## Constraints
- Soft-PLC remains mock-unaware (no plant synthesis OUT; no mock-mode API)
- HA-free dynamics modules (`core`, catalog, compiler, expressions, plant) — no `homeassistant` imports; CI must import them without HA
- Preserve MQTT topic/payload contracts; plant Numbers remain nudge-only while simulator owns tags
- App + integration version lock; dual trees synced via `./scripts/sync-ha-app-package.sh`
- One simulator task per config entry (unchanged lifecycle)

## Acceptance criteria
1. Unit-op catalog includes `tank`, `pump`, `orifice`, `lag`, `custom_ode` with documented contracts.
2. A composed-skid model document compiles to a `ModelSpec` whose steps match code `SkidModel` / `MockProcess` within **1e-9**.
3. `custom_ode` accepts safe expressions and **rejects** unsafe AST at load time with a clear error.
4. Loader validates schema `version`, required fields, unknown op types, and dangling connection names.
5. `PlantSimulator` runs any `DynamicsModel` from the preset registry; live default remains code `skid`.
6. Soft-PLC App still constructs `HeldProcess` and does not gain plant math APIs.
7. Docs state: unit-ops + expression sandbox live in the integration dynamics package; Soft-PLC surface is not the plant authoring path; UI → SWD-143.
8. Automated tests cover: catalog ops, compiler/oracle parity, expression sandbox allow/deny, loader validation, registry/`DynamicsModel` typing.
9. App + integration versions bumped and dual trees synced on implement.

## Work packages
1. **Unit-op contract + catalog** — op interface; implement `tank` / `pump` / `orifice` / `lag` / `custom_ode`
2. **Expression sandbox** — AST parse/whitelist/eval; allow/deny tests
3. **Compiler + model documents** — connections → collected `ModelSpec`; composed-skid JSON; schema version
4. **Runtime wiring** — `DynamicsModel` typing; registry (`skid`, `skid_composed`); keep live default `skid`
5. **Acceptance + packaging** — oracle/sandbox/loader tests, docs, version bump, dual-tree sync

## Tracker
- Provider: jira
- Story: [SWD-142](https://marcusknielsen.atlassian.net/browse/SWD-142)
- Task: [SWD-144](https://marcusknielsen.atlassian.net/browse/SWD-144)
- Sub-tasks: [SWD-157](https://marcusknielsen.atlassian.net/browse/SWD-157) catalog, [SWD-159](https://marcusknielsen.atlassian.net/browse/SWD-159) sandbox, [SWD-158](https://marcusknielsen.atlassian.net/browse/SWD-158) compiler/YAML, [SWD-160](https://marcusknielsen.atlassian.net/browse/SWD-160) registry wiring, [SWD-161](https://marcusknielsen.atlassian.net/browse/SWD-161) acceptance
- Prior: [SWD-146](https://marcusknielsen.atlassian.net/browse/SWD-146) Done (App 0.1.22)
- Follow-on UI: [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143)
- Branch: `cursor/swd-144-unit-ops-implement-33f4`
- Implement: App **0.1.23** — PR https://github.com/marcuskrogh/PLCAssistant/pull/65

## Next
`/define SWD-143` — after SWD-144 Done
