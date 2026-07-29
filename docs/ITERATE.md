# Iterate: Auto-register Lovelace dashboard in HA sidebar

## Status
**In Progress** — App **0.1.12** (branch `cursor/swd-134-sidebar-lovelace-dashboard-1bbe`)

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

## Next
PR → `/review-fix SWD-134`
