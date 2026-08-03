# Roadmap: Cloud HA live integration & system tests

## Destination
Integration and system tests run against the cloud development stack (Mosquitto + Home Assistant Core + Soft-PLC App) and prove end-to-end functionality between the thin HA integration and the Soft-PLC application.

## Notes
- Trigger: `.cursor/environment.json` HA Core stack; existing `test_integration_*` / `test_system_*` suites are mostly in-process acceptance, not live-stack.
- Prefer pytest markers so default unit runs stay fast; live tests opt-in when the stack is up.
- Reuse `.cursor/ha/scripts/bootstrap_ha.py` token + HA REST / Soft-PLC `/api/*`.
- Do not replace in-process acceptance suites — add a parallel `tests/live/` suite.

## Route
| Order | Task | Type | Blocked by | Status | Issue |
|-------|------|------|------------|--------|-------|
| 1 | Define & ship live cloud HA integration/system test suite | define→ship | — | Done | [SWD-232](https://marcusknielsen.atlassian.net/browse/SWD-232) · PR [#95](https://github.com/marcuskrogh/PLCAssistant/pull/95) |

## Cleared so far
- [Define & ship live cloud HA suite](https://marcusknielsen.atlassian.net/browse/SWD-232) — `tests/live/` + `run_live_tests.sh`; 9/9 live tests; review-fix CLEAN; PR #95

## Not yet specified
- Whether live tests should auto-start HA/Soft-PLC in CI (vs skip) when terminals are absent
- Broader scenario matrix (cascade PID, dynamics presets, schedule apply) beyond smoke Start/Stop/SP path

## Out of scope
- Replacing in-process unit/acceptance suites
- Supervisor / HA OS production install testing
- Physical plant / field I/O commissioning

## Tracker
- Provider: jira
- Story (map): [SWD-231](https://marcusknielsen.atlassian.net/browse/SWD-231)
- Tasks: [SWD-232](https://marcusknielsen.atlassian.net/browse/SWD-232)

## Next
Done — initiative complete (SWD-231). Optional: broader live scenario matrix.
