# Implementation plan: Live cloud HA integration & system tests (SWD-232)

## Summary
- Add a **live-stack** pytest suite under `tests/live/` that exercises Soft-PLC App ↔ thin HA integration against Mosquitto + HA Core + Soft-PLC in the cloud/dev environment.
- Gate with pytest markers so default `pytest` stays fast (unit/acceptance only).
- Provide a runner script that ensures the stack is up, then runs the live markers.

## Scope
### In
- Shared HA REST + Soft-PLC HTTP clients; load token from `.cursor/ha/data/ha_token.json`
- Markers: `live`, `live_integration`, `live_system` (default suite excludes `live`)
- Integration scenarios: MQTT attached, entities present, HA start/stop drives Soft-PLC scan, status mirror
- System scenarios: stack health, Start path updates HA status + plant sensors, editor APIs, SP write round-trip
- Docs in `.cursor/ha/README.md` + `bash .cursor/ha/scripts/run_live_tests.sh`

### Out
- Rewriting existing in-process `test_integration_*` / `test_system_*` acceptance tests
- Supervisor / HA OS e2e
- Full cascade/dynamics matrix beyond smoke path

## Decisions
| Topic | Decision |
|-------|----------|
| Location | `tests/live/` (separate from in-process acceptance) |
| Markers | `live` + `live_integration` / `live_system`; default `addopts = -m "not live"` |
| Stack missing | Skip with clear reason unless runner starts stack |
| Auth | Reuse bootstrap token file; runner re-bootstraps if needed |
| Entity IDs | Prefer known defaults (`sensor.plcassistant_status`, …) with discovery fallback |
| Start path | HA service `plcassistant.start` → Soft-PLC `scanning` / status `running` |
| Runner | `.cursor/ha/scripts/run_live_tests.sh` starts Mosquitto + HA + Soft-PLC if down, then pytest |

## Constraints
- Must not slow default unit CI / local `pytest`
- Dual trees / App packaging unchanged unless version bump required (tests-only → no App version bump)
- Soft-PLC remains mock-unaware; plant dynamics stay integration-owned

## Acceptance criteria
- [x] `pytest` (default) does not collect/run live tests
- [x] `pytest -m live` (with stack up) passes integration + system live tests
- [x] Live integration: Soft-PLC MQTT attached; HA has PLCAssistant entities; start/stop via HA drives Soft-PLC
- [x] Live system: stack ports healthy; Start updates HA status sensor; plant PV sensors available; Soft-PLC `/api/runtime` + `/api/project` respond; level MAN SP write is visible on Soft-PLC tags
- [x] `.cursor/ha/README.md` documents how to run; `run_live_tests.sh` works in this cloud env

## Work packages
1. **Live stack fixtures + clients** — [SWD-233](https://marcusknielsen.atlassian.net/browse/SWD-233)
2. **Live integration tests** — [SWD-234](https://marcusknielsen.atlassian.net/browse/SWD-234)
3. **Live system tests** — [SWD-235](https://marcusknielsen.atlassian.net/browse/SWD-235)
4. **Docs + runner** — [SWD-236](https://marcusknielsen.atlassian.net/browse/SWD-236)

## Open items
- Broader scenario matrix deferred to fog on SWD-231 roadmap

## Tracker
- Provider: jira
- Story: [SWD-231](https://marcusknielsen.atlassian.net/browse/SWD-231)
- Task: [SWD-232](https://marcusknielsen.atlassian.net/browse/SWD-232)
- Sub-tasks: SWD-233, SWD-234, SWD-235, SWD-236
- Branch: `cursor/swd-232-cloud-ha-live-tests-04fc`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/95

## Next
`/review-fix SWD-232` — multi-axis review then ship closeout.
