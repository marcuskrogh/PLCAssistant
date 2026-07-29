# Iterate: Soft-PLC still offline after 0.1.14 — MQTT never attaches

## Status
**In Progress** — App **0.1.15**

## Prior work
- Task: SWD-136 (PR #51, App 0.1.14 — status cache/hydrate + heartbeat/LWT)
- Spec context: prior ITERATE.md (SWD-136)

## Problem
Operator feedback after 0.1.14:

1. Soft-PLC still **offline**, Mode STOP, Start permissive Off, Trip Off (entity defaults).
2. Pressing Start still does nothing.

Root cause: HA App runtime can boot with missing/empty `/data/options.json`. Empty options are falsy in Python, so Soft-PLC never defaults to `core-mosquitto` and `_mqtt_supervisor` returns without starting the MQTT retry thread. No scan loop → no status/OUT MQTT → HMI stays at defaults. The 0.1.14 status-race fixes cannot help when Soft-PLC never publishes.

## Acceptance criteria
1. With HA runtime (`PLCASSISTANT_HA_RUNTIME=1`), Soft-PLC always attempts MQTT to `core-mosquitto` even when options.json is missing/empty.
2. App Start seeds default options.json when missing.
3. After App Start + Core restart (Mosquitto up), Lovelace Soft-PLC shows `stopped` and Start permissive On; Start → running.
4. MODE / PERM_OK / TRIP_ACTIVE OUT published retained (hydrate-friendly).
5. App + integration version **0.1.15**.

## Out of scope
- Mosquitto not installed / HA MQTT credentials mismatch (ops) — Soft-PLC still retries and logs connect failures.
- Changing boot MODE (remains STOP until Start).

## Tracker
- Task: [SWD-137](https://marcusknielsen.atlassian.net/browse/SWD-137)
- Relates: SWD-136
- Branch: `cursor/swd-137-soft-plc-mqtt-attach-33f4`

## Next
`/review-fix SWD-137` — Review and auto-fix until clean
