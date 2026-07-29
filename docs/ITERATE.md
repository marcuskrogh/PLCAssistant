# Iterate: Auto-register Lovelace dashboard in HA sidebar

## Status
**In Review (review-fix CLEAN)** — App **0.1.12** (PR [#47](https://github.com/marcuskrogh/PLCAssistant/pull/47))

## Prior work
- Task: SWD-133 (PR #46, App 0.1.11 — Lovelace template still required copy/paste)

## Problem
Default Lovelace board required manual paste from `/config/dashboards/plcassistant.yaml`. Operator wants the dashboard **built and shown on the sidebar** automatically.

## Acceptance criteria
1. After App Update + Core restart + PLCAssistant integration loaded, **PLCAssistant** appears in the HA **sidebar** (no Settings → Dashboards paste).
2. Dashboard shows Start/Stop/Reset, Level setpoint, and live process sensors.
3. Docs no longer treat copy/paste as the primary install path.
4. App + integration version **0.1.12**.

## Tracker
- Task: [SWD-134](https://marcusknielsen.atlassian.net/browse/SWD-134)
- Relates: SWD-133
- Branch: `cursor/swd-134-sidebar-lovelace-dashboard-1bbe`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/47

## review-test
- Iter 1: HA import fragility (`async_panel_exists` / `LOVELACE_DATA` hard-fail skipped sidebar); module logger; `run.sh` no-clobber regression test
- Iter 2: 0 blockers / 0 should-fix

## Next
`/ship SWD-134`
