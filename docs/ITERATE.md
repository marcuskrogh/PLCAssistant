# Iterate: Lovelace status indicator + Start wiring

## Status
**In Review** — PR [#49](https://github.com/marcuskrogh/PLCAssistant/pull/49); App **0.1.13**

## Prior work
- Task: SWD-134 (PR #47, App 0.1.12 — sidebar Lovelace, no status / MODE on board)

## Problem
Operator feedback after 0.1.12:

1. **No status on the Lovelace dashboard** — cannot see if the Soft-PLC process is running, stopped/idle, tripped, or offline. Status must appear at the **top** of the board.
2. **Start appears to do nothing** — pressing Start gives no visible feedback. HMI contract tags (`MODE`, `PERM_OK`) were never published on the packaging MQTT image; status topic was never mirrored into HA; setpoint request was not published until the Number was changed.

## Acceptance criteria
1. Lovelace shows Soft-PLC / process status at the top (running, stopped/idle, tripped, offline/fault as applicable).
2. Pressing Start moves status/MODE to running and process sensors respond when healthy.
3. Soft-PLC publishes MODE (+ PERM_OK) on tag OUT; integration mirrors App `status` topic + those tags as sensors.
4. Stock Lovelace YAML (missing status entities) is refreshed on App/integration update; true custom boards are preserved.
5. App + integration version **0.1.13**.

## Tracker
- Task: [SWD-135](https://marcusknielsen.atlassian.net/browse/SWD-135)
- Relates: SWD-134
- Branch: `cursor/swd-135-lovelace-status-start-7273`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/49
