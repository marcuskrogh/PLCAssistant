# Iterate: Soft-PLC attached but HMI still offline — Core never restarts

## Status
**In Review** — App **0.1.16**; PR [#53](https://github.com/marcuskrogh/PLCAssistant/pull/53)

## Prior work
- Task: SWD-137 (PR #52, App 0.1.15 — empty options MQTT attach)
- Spec context: prior ITERATE.md (SWD-137)

## Problem
Operator App log after 0.1.15 shows Soft-PLC MQTT **attached** (`status=stopped`, `instance_id=default`) and thin integration installed/updated, but Lovelace HMI still shows Soft-PLC **offline**, Mode STOP, Start permissive Off; Start does nothing.

Root cause: Soft-PLC publish path is healthy. App Start copies `custom_components/plcassistant` into HA config and stamps `integration_needs_core_restart`, but **never restarts Home Assistant Core**. Core keeps stale/unloaded integration code and never hydrates retained status/OUT over MQTT. The log line “Restart Home Assistant Core” is easy to miss on mobile.

## Acceptance criteria
1. After App Start that syncs the thin integration, Core restart is requested via Supervisor API (`SUPERVISOR_TOKEN`). If restart cannot be requested, create a HA persistent notification telling the operator to restart Core.
2. Soft-PLC MQTT uses a unique `client_id` (not fixed `plcassistant-app`) to avoid LWT thrash on App restart.
3. Lovelace offline help states: if App log shows `Soft-PLC MQTT scan attached` but HMI is offline → Restart Home Assistant Core.
4. App + integration version **0.1.16**.
5. Opt-out: `PLCASSISTANT_AUTO_CORE_RESTART=0` skips the Supervisor restart request (still logs + notification when possible).

## Out of scope
- Forcing host reboot.
- Changing Soft-PLC MODE boot behaviour.
- Fixing Mosquitto/HA MQTT credential mismatches (ops).

## Tracker
- Task: [SWD-138](https://marcusknielsen.atlassian.net/browse/SWD-138)
- Relates: SWD-137
- Branch: `cursor/swd-138-core-restart-after-sync-33f4`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/53

## Next
`/review-fix SWD-138` — Review and auto-fix until clean
