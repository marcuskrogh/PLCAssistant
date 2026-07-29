# Implementation plan: Configurable dynamics core + skid preset (SWD-146)

## Summary
- Build the **integration-owned stand-alone process simulator** that restores live plant motion after SWD-145 made Soft-PLC mock-unaware.
- Deliver a **dynamics core** (states + parameters + inputs + outputs + RHS + post-step projection) with a **deterministic fixed-step** stepper driven by observed Soft-PLC `scan_period_s`.
- Ship the existing tank/reservoir skid as the **first selectable preset** (`skid`), reproducing today’s `MockProcess` physics qualitatively and via oracle comparison.
- Soft-PLC stays **mock-unaware**; process ↔ Soft-PLC remains **MQTT** (mock ≡ field).

## Scope
**In**
- HA-independent dynamics engine under the thin integration (`custom_components/plcassistant/dynamics/`)
- Preset registry with programmatic `skid` default when `mock_mode=true`
- Skid preset: migrate live physics from wedge `MockProcess` (levels, pump, drain, lags, inventory projection)
- HA simulator lifecycle: observe MQTT status (`scan_period_s`, state), consume Soft-PLC `CMD_SPEED` OUT, publish plant PVs IN
- Plant Number ownership: simulator is authoritative publisher; Numbers display/nudge state (no competing MQTT writers)
- Programmatic nudge / quality hooks for automated acceptance
- Docs + tests: end-to-end plant motion; Soft-PLC still uses `HeldProcess`
- App + integration version bump

**Out**
- Unit-op library / custom equation authoring / expression sandbox → [SWD-144](https://marcusknielsen.atlassian.net/browse/SWD-144)
- Integration mock UI (preset chooser, parameter editor, fault-injection services) → [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143)
- Soft-PLC programming / control / safety changes
- Scan-edge lockstep protocol (new tick topic)
- Physical field commissioning
- Persisted plant state across Core restart (v1 resets to preset initials)

## Decisions
1. **Integration-local core:** pure stdlib dynamics under `custom_components/plcassistant/dynamics/` (no Home Assistant imports in the engine). HA wrapper (`simulator.py`) owns lifecycle/MQTT/entities.
2. **Model contract:** `ModelSpec = states + parameters + inputs + tag outputs + rhs(dt, state, inputs, params) + projection(state, params, dt)`.
3. **Solver:** deterministic fixed-step integration at the **observed nominal** Soft-PLC period; substeps ≤ 100 ms; monotonic accumulator with capped catch-up. Not scan-edge lockstep.
4. **Coupling:** async / nominal — Soft-PLC OUT `CMD_SPEED` → simulator input; simulator → plant MQTT IN. Expect ≤ ~1 scan of latency.
5. **Default preset:** when `mock_mode=true`, run `skid` programmatically. No user-facing selector yet (SWD-143).
6. **Plant publisher ownership:** simulator owns `LT_TANK` / `LT_RES` / `FT_INLET` MQTT IN. Writable Numbers update simulator state (nudge) and reflect simulator values; they must not independently republish while the preset runs.
7. **Status behaviour:** start stepping after a valid status with finite positive `scan_period_s`; continue gravity drain while Soft-PLC is `stopped`; freeze timing on `offline`/`fault` (and zero `CMD_SPEED` after a watchdog timeout).
8. **Transport:** MQTT only for plant ↔ Soft-PLC (file bridge unchanged — `SP_LEVEL_REQ` only).
9. **`MockProcess` remains** the offline / unit-test oracle in `plcassistant.wedge`; live Soft-PLC path stays `HeldProcess`. Do not import App package from the HA component.
10. **Skid fidelity:** reproduce inventory conservation, clamps, pump derate, flow lag, and qualitative Start/Stop / cascade / HH / LL / LOS acceptance from wedge docs; exact byte-identical step matching is not required if oracle comparison stays within agreed tolerances.

## Constraints
- Soft-PLC remains mock-unaware (no plant synthesis OUT; no mock-mode API)
- Preserve MQTT topic/payload contracts (`docs/packaging/02-mqtt-topics.md`)
- App + integration version lock; dual trees under `plc_assistant/` stay synced
- One simulator task per config entry; cancel on unload/reload
- Cap MQTT plant publish cadence (coalesce to latest state) so 100 ms Soft-PLC period does not flood QoS-1

## Inputs (supportive)
- Ownership: [`docs/PLAN.md` history / SWD-145](https://marcusknielsen.atlassian.net/browse/SWD-145), [`docs/packaging/01-shape.md`](packaging/01-shape.md)
- Physics + acceptance: [`docs/wedge/05-mock-process.md`](wedge/05-mock-process.md), [`docs/wedge/06-mock-acceptance.md`](wedge/06-mock-acceptance.md)
- Library oracle: `plcassistant/wedge/process.py` (`MockProcess`)
- Live seams: `custom_components/plcassistant/{__init__,number,sensor}.py`

## Acceptance criteria
1. With `mock_mode=true`, skid preset starts at defaults (tank 0.15 m, res 0.20 m, flow 0 L/min) and publishes plant PVs as Soft-PLC MQTT IN.
2. Soft-PLC Start with healthy plant raises `CMD_SPEED` / flow response; zero command drains tank (qualitative).
3. Inventory conserved within stated tolerance; levels remain within vessel bounds.
4. Observed valid `scan_period_s` sets nominal step period; malformed/missing values fall back safely (default 0.1 s) without crashing the task.
5. Soft-PLC App still constructs `HeldProcess` and does **not** publish plant PVs as OUT.
6. No competing plant Number MQTT publisher while simulator owns the skid.
7. Automated tests cover: dynamics unit oracle vs `MockProcess` (tolerance), HA/in-memory MQTT closed-loop plant motion, unload/reload single-task lifecycle, file-bridge plant tags still ignored.
8. Docs state: integration simulator + skid preset; Soft-PLC mock-unaware; UI/unit-ops deferred to SWD-143/144.
9. App + integration versions bumped and dual trees synced.

## Work packages
1. **Dynamics engine** — `ModelSpec`, fixed-step stepper, validation, projection seam, timing accumulator
2. **Skid preset** — migrate live physics from `MockProcess`; registry + `skid` default; oracle-comparison tests
3. **HA simulator lifecycle** — parse/store `scan_period_s` + status; subscribe Soft-PLC `CMD_SPEED`; step + publish plant IN; watchdog / offline freeze
4. **Plant Number ownership** — stop competing publishes; hydrate/nudge from simulator; Lovelace copy for live motion
5. **Acceptance + packaging** — closed-loop tests, docs, version bump, dual-tree sync

## Open items
- Exact oracle tolerance bands (implement choice; document in tests)
- Whether Number entities become read-only while simulator runs vs stay writable nudges (prefer writable nudges)
- `SC_PUMP` / quality HMI surfaces — not required for SWD-146 dashboard
- Full unit-op composition / custom DE DSL → SWD-144
- Preset chooser + parameter editor UI → SWD-143

## Tracker
- Provider: jira
- Story: [SWD-142](https://marcusknielsen.atlassian.net/browse/SWD-142)
- Task: [SWD-146](https://marcusknielsen.atlassian.net/browse/SWD-146)
- Sub-tasks: [SWD-156](https://marcusknielsen.atlassian.net/browse/SWD-156) engine, [SWD-154](https://marcusknielsen.atlassian.net/browse/SWD-154) skid preset, [SWD-152](https://marcusknielsen.atlassian.net/browse/SWD-152) HA lifecycle, [SWD-155](https://marcusknielsen.atlassian.net/browse/SWD-155) Number/HMI, [SWD-153](https://marcusknielsen.atlassian.net/browse/SWD-153) acceptance
- Prior: [SWD-145](https://marcusknielsen.atlassian.net/browse/SWD-145) Done
- Branch: `cursor/swd-146-dynamics-core-define-33f4`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/62

## Next
`/implement SWD-146` — Build per this plan (same branch/PR after define approval)
