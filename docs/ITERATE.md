# Iterate: Soft-PLC attached but HMI still offline — MQTT never reaches HA

## Status
**Done** — App **0.1.17**; shipped PR [#55](https://github.com/marcuskrogh/PLCAssistant/pull/55)

## Prior work
- Task: SWD-138 (PR #53, App 0.1.16 — auto Core restart after sync)
- Spec context: prior ITERATE.md (SWD-138)

## Problem
Operator confirms App log `Soft-PLC MQTT scan attached (status=stopped)` and thin integration up to date, but Lovelace still shows Soft-PLC **offline**, Mode STOP, Start permissive Off.

Soft-PLC→Mosquitto publish works. HA entities never leave defaults — the MQTT path into the thin integration is not delivering (HA MQTT disconnected / different broker / subscribe never hydrates).

## Acceptance criteria
1. Soft-PLC writes shared runtime snapshot under HA config (`plcassistant/runtime.json`) on status/scan heartbeat.
2. Soft-PLC drains operator cmds from `plcassistant/cmd.json` (start/stop/reset).
3. Thin integration polls the runtime file and hydrates status + MODE / PERM_OK / TRIP_ACTIVE when MQTT is silent; Start/Stop/Reset also write the cmd file.
4. MQTT remains primary when it works (file is secondary fallback).
5. App + integration version **0.1.17**.

## Out of scope
- Replacing MQTT entirely.
- Fixing Mosquitto credential/ACL ops issues beyond this fallback.

## Tracker
- Task: [SWD-139](https://marcusknielsen.atlassian.net/browse/SWD-139)
- Relates: SWD-138
- Branch: `cursor/swd-139-ha-config-bridge-33f4`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/55

## Next
Done — phase closed.
