# Implementation plan: Isolate PID faceplate elements (SWD-373)

## Summary
- Split the Lovelace PID faceplate into **named visual elements** (ISA-5.1 glyph, KPI row, PV/SP bars, CO bar, MAN/AUTO/REM) in a shared ES module.
- Add a **developer sandbox** that mounts those elements in isolation (and as assembled Level/Flow mocks) in a browser — no Home Assistant, no App, no MQTT.
- Lovelace `plcassistant-pid-card` consumes the same module so sandbox chrome is shipping chrome.

## Scope
### In
- `custom_components/plcassistant/www/pid-faceplate-elements.js` — CSS, markup, `applyPidFaceplateState`, and existing faceplate helpers
- Lovelace card becomes HA glue (hass, services, dialog drafts) importing that module
- `tools/pid-faceplate/` sandbox gallery + local static server script
- Tests, faceplate-doc note, dual-tree sync, App **0.1.59** (new www module the card imports)

### Out
- Operator Lovelace behaviour changes (geometry, modes, writes, ISA-101 colour)
- New Lovelace resource registration for the elements file (the card module imports it)
- Alarm-limit colour bands, CAS relabel, series form / autotune
- Replacing Lovelace with a dedicated SCADA HMI

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
| App version | **0.1.59** — operators need the new sibling file next to the card. |

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
- Do not change MAN/AUTO/REM write targets, bar click mapping, or ISA-101 colour rules
- Keep SWD-227 click routing: mode only from `button[data-mode]`
- Dialog stays a sibling of `.pid-card` (overflow:hidden on the card only)
- Issue keys stay off product surfaces (card copy, Lovelace yaml, sandbox visible labels)
- Default `pytest` stays fast (no live marker)

## Acceptance criteria
- [ ] Named elements `isa-glyph`, `kpi-row`, `analog-bars`, `mode-row` can be mounted one-at-a-time from the shared module
- [ ] Sandbox shows those isolates plus assembled Level and Flow mocks; openable without HA/App
- [ ] Lovelace card imports the shared module; operator geometry, modes, and writes match SWD-369
- [ ] Existing JS faceplate contract tests still pass (re-exports from the card)
- [ ] Dual-tree includes `pid-faceplate-elements.js`; App **0.1.59**
- [ ] Docs note the sandbox path and that chrome iteration does not require an App deploy until ship

## Work packages
1. **Shared faceplate elements module + Lovelace wiring** ([SWD-374](https://marcusknielsen.atlassian.net/browse/SWD-374))
2. **Isolated element sandbox (no HA/App)** ([SWD-375](https://marcusknielsen.atlassian.net/browse/SWD-375))
3. **Tests, docs, dual-tree, App 0.1.59** ([SWD-376](https://marcusknielsen.atlassian.net/browse/SWD-376))

## Open items
- Whether a later slice adds alarm-limit colour bands on the PV bar — still later (SWD-368)

## Tracker
- Provider: jira
- Story: [SWD-368](https://marcusknielsen.atlassian.net/browse/SWD-368) (Relates)
- Task: [SWD-373](https://marcusknielsen.atlassian.net/browse/SWD-373)
- Sub-tasks: [SWD-374](https://marcusknielsen.atlassian.net/browse/SWD-374), [SWD-375](https://marcusknielsen.atlassian.net/browse/SWD-375), [SWD-376](https://marcusknielsen.atlassian.net/browse/SWD-376)
- Branch: `cursor/swd-373-pid-faceplate-sandbox-a582`
- PR: [#105](https://github.com/marcuskrogh/PLCAssistant/pull/105)
- Classification: feature
- Workflow: feature-standard

## Next
`/implement SWD-373` — Build per PLAN.md workflow binding (same branch/PR)
