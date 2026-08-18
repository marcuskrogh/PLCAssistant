# Implementation plan: Isolate PID faceplate elements (SWD-373)

## Summary
- Split the Lovelace PID faceplate into **named visual elements** (ISA-5.1 glyph, KPI row, PV/SP bars, MV bar, MAN/AUTO/REM) in a shared ES module.
- Add a **developer sandbox** that mounts those elements in isolation (and as assembled Level/Flow mocks) in a browser — no Home Assistant, no App, no MQTT.
- Lovelace `plcassistant-pid-card` consumes the same module so sandbox chrome is shipping chrome.

## Scope
### In
- `custom_components/plcassistant/www/pid-faceplate-elements.js` — CSS, markup, `applyPidFaceplateState`, and existing faceplate helpers
- Lovelace card becomes HA glue (hass, services, dialog drafts) importing that module
- `tools/pid-faceplate/` sandbox gallery + local static server script
- Tests, faceplate-doc note, dual-tree sync, App **0.1.64**
- Faceplate UX (SWD-377): thinner/taller PV/SP bars; thicker MV; colour fill on the writable analog; values on the bars; bar click opens a numeric popup; `<< < > >>` nudges; settings gear for Kp/Ki/Kd
- Faceplate UX (SWD-378): focused popup for the clicked analog (value + min/max); CO labelled **MV**; ε between PV and SP
- Faceplate UX (SWD-379): writable analog fill is a muted activity green
- Faceplate UX (SWD-380): settings gear exposes all standardised PID params in panes (Gains / Structure / Output / Filter)
- Faceplate UX (SWD-381): SP ramping (`sp_ramp_max`) in backend + Ramp settings pane; orange SP-bar segment from current SP to target while ramping

### Out
- New Lovelace resource registration for the elements file (the card module imports it)
- Alarm-limit colour bands, series form / autotune
- Replacing Lovelace with a dedicated SCADA HMI
- Colour-coding MAN / AUTO / REM **buttons** (mode identity stays grayscale invert; only the writable **bar fill** uses colour)

## Decisions
| Topic | Decision |
|-------|----------|
| Why isolate | Iterate faceplate chrome in a browser without deploying the HA App or the rest of the Soft-PLC. |
| Source of truth | One module: `pid-faceplate-elements.js`. Card and sandbox both import it. |
| Elements | `isa-glyph`, `kpi-row`, `analog-bars`, `mode-row`, plus assembled face (+ dialog markup for the card). |
| Sandbox location | `tools/pid-faceplate/` — developer-only; not an operator Lovelace surface; not a Supervisor App file. |
| How to open | Serve the repo root over HTTP (ES modules). `tools/pid-faceplate/serve.sh`. |
| Lovelace load | Card stays the registered module resource. Relative `import` of `./pid-faceplate-elements.js` from `/plcassistant_static/` (already `res_type: module`). |
| Helpers | Move exported contract helpers into the elements module; card re-exports so existing JS tests keep working. |
| App version | **0.1.64** — operators can rate-limit SP moves; the SP bar shows orange to the target while ramping. |
| SP ramp | Faceplate / SP-path (`sp_ramp_max` EU/s). Not a PID equation param. `0` = instant (non-regression). |
| Writable highlight | Colour the **bar fill** with muted activity green (`--pid-active`). Not a bounding box. ε colour stays on ε; MV clamp caution tints MV only. |
| Bar click | Focused popup for **that** analog: current value, min, max, unit. Set only when writable. No pointer-set. |
| Faceplate CO | Labelled **MV**. Internal `data-bar="co"` / `cv` / write_target `co` unchanged. |
| ε | Between the PV and SP bars (not in the header). Caution/abnormal colour. |
| Nudges | `<<` / `>>` ±1.0, `<` / `>` ±0.1 on the writable analog; between CO and MAN/AUTO/REM. |
| Settings | Gear top-right; paned popup for standardised PID params plus SP ramp. Skip unused `td` / `gamma`. Form is read-only Parallel. |
| SP ramp chrome | Orange `--pid-ramp` segment on the SP bar between current SP and target, only while `|ΔSP|` exceeds one scan at `sp_ramp_max`. |

## Classification
- Class: feature
- Confidence: high
- Why: new developer sandbox plus a shared element module is a buildable slice; operator HMI behaviour is preserved, not a defect

## Workflow
- Template: feature-standard
- Parameters:
  - implement.mode: single
  - implement.verify: tests
  - implement.iteration: one-shot
  - review.mode: single
  - review.depth: focused
  - side_paths: none
- Chain: implement → review-fix → ship
- Rationale: localised to www JS + a tools sandbox; Lovelace already loads the card as a module; no new HA API/schema

## Inputs
- Research: —
- Model: —

## Constraints
- Dual trees (`custom_components/plcassistant/` and `plc_assistant/custom_components/plcassistant/`) stay in sync; run `scripts/sync-ha-app-package.sh`
- MAN/AUTO/REM write targets stay: MAN→CO, AUTO→SP when Number, REM none
- Keep SWD-227 click routing: mode only from `button[data-mode]`
- Dialog stays a sibling of `.pid-card` (overflow:hidden on the card only)
- Issue keys stay off product surfaces (card copy, Lovelace yaml, sandbox visible labels)
- Default `pytest` stays fast (no live marker)

## Acceptance criteria
- [x] Named elements `isa-glyph`, `kpi-row`, `analog-bars`, `mode-row` can be mounted one-at-a-time from the shared module
- [x] Sandbox shows those isolates plus assembled Level and Flow mocks; openable without HA/App
- [x] Lovelace card imports the shared module; operator geometry, modes, and writes match SWD-369
- [x] Existing JS faceplate contract tests still pass (re-exports from the card)
- [x] Dual-tree includes `pid-faceplate-elements.js`; App **0.1.59**
- [x] Docs note the sandbox path and that chrome iteration does not require an App deploy until ship
- [x] Vertical PV/SP bars are thinner and taller; MV bar is thicker
- [x] Writable analog uses colour fill (not a bounding box); mode buttons stay grayscale
- [x] PV / SP / MV numerics sit on their bars; ε sits between PV and SP
- [x] Clicking a writable bar opens the numeric popup (no pointer-position set)
- [x] `<< < > >>` between CO and modes nudge the writable analog by 1.0 / 0.1
- [x] Settings gear (top right) edits Kp / Ki / Kd
- [x] Dual-tree + App **0.1.60**
- [x] Clicking a writable bar opens a focused popup for that analog (value, min, max)
- [x] Faceplate labels the controller output **MV**
- [x] ε sits between the PV and SP bars
- [x] Dual-tree + App **0.1.61**
- [x] Writable analog fill is a muted activity green
- [x] Dual-tree + App **0.1.62**
- [x] Settings gear panes: Gains, Structure, Output, Filter
- [x] Operators can see and set kp, ki, kd, u0, beta, direct_acting, cv_min, cv_max, hold_when_stopped, ts, tf_ts
- [x] Form is read-only Parallel; unused td/gamma are omitted
- [x] Extra params are wired like Kp (Datablock IN, Number entities, compound sensor, file-bridge, scan sync)
- [x] Dual-tree + App **0.1.63**
- [x] Ramp settings pane edits `sp_ramp_max` (0 = instant)
- [x] Soft-PLC ramps the SP fed to each PID when `|ΔSP|` exceeds the rate
- [x] Compound sensor publishes `sp` (ramped OUT when rate > 0) and `sp_target` (mux)
- [x] SP bar shows an orange segment between current SP and target while ramping
- [x] Dual-tree + App **0.1.64**

## Work packages
1. **Shared faceplate elements module + Lovelace wiring** ([SWD-374](https://marcusknielsen.atlassian.net/browse/SWD-374))
2. **Isolated element sandbox (no HA/App)** ([SWD-375](https://marcusknielsen.atlassian.net/browse/SWD-375))
3. **Tests, docs, dual-tree, App 0.1.59** ([SWD-376](https://marcusknielsen.atlassian.net/browse/SWD-376)) — Done
4. **Faceplate UX** ([SWD-377](https://marcusknielsen.atlassian.net/browse/SWD-377)) — Done
5. **Focused MV popup and ε between PV/SP** ([SWD-378](https://marcusknielsen.atlassian.net/browse/SWD-378)) — Done
6. **Calm activity green on writable analog bars** ([SWD-379](https://marcusknielsen.atlassian.net/browse/SWD-379)) — Done
7. **Paned settings for all standardised PID parameters** ([SWD-380](https://marcusknielsen.atlassian.net/browse/SWD-380)) — Done
8. **SP ramping in backend, settings, and orange SP bar** ([SWD-381](https://marcusknielsen.atlassian.net/browse/SWD-381)) — Done

## Open items
- Whether a later slice adds alarm-limit colour bands on the PV bar — still later (SWD-368)

## Tracker
- Provider: jira
- Story: [SWD-368](https://marcusknielsen.atlassian.net/browse/SWD-368) (Relates)
- Task: [SWD-373](https://marcusknielsen.atlassian.net/browse/SWD-373)
- Sub-tasks: [SWD-374](https://marcusknielsen.atlassian.net/browse/SWD-374), [SWD-375](https://marcusknielsen.atlassian.net/browse/SWD-375), [SWD-376](https://marcusknielsen.atlassian.net/browse/SWD-376), [SWD-377](https://marcusknielsen.atlassian.net/browse/SWD-377), [SWD-378](https://marcusknielsen.atlassian.net/browse/SWD-378), [SWD-379](https://marcusknielsen.atlassian.net/browse/SWD-379), [SWD-380](https://marcusknielsen.atlassian.net/browse/SWD-380), [SWD-381](https://marcusknielsen.atlassian.net/browse/SWD-381)
- Branch: `cursor/swd-373-pid-faceplate-sandbox-a582`
- PR: [#105](https://github.com/marcuskrogh/PLCAssistant/pull/105)
- Classification: feature
- Workflow: feature-standard

## Next
Done — shipped PR [#105](https://github.com/marcuskrogh/PLCAssistant/pull/105)
