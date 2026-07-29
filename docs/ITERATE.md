# Iterate: Level setpoint request does not update Active level SP

## Status
**In Review** — App **0.1.19**; PR [#57](https://github.com/marcuskrogh/PLCAssistant/pull/57)

## Prior work
- Task: SWD-140 (PR #56, App 0.1.18 — OUT file-bridge tags + Start ready)
- Spec context: prior ITERATE.md (SWD-140)

## Problem
Operator sets **Level setpoint** to **0.3 m**, Stop+Start, but **Active level SP** stays **0.2 m**. Process PVs and Active flow SP otherwise move (file bridge OUT path works).

## Root cause
MQTT-silent file bridge carries Start/Stop/Reset and OUT tags, but not operator IN `SP_LEVEL_REQ`. The number entity only MQTT-publishes; Soft-PLC keeps image default **0.20 m**.

## Acceptance criteria
1. HA writes `SP_LEVEL_REQ` into shared HA-config inputs file when Level setpoint changes (in addition to MQTT).
2. Soft-PLC applies file IN tags each scan; MQTT still overrides when present.
3. After Update **0.1.19** + Core reload: set Level setpoint to 0.3 m, Stop+Start → Active level SP ≈ 0.3 m.
4. App + integration version **0.1.19**.

## Out of scope
- Fixing Mosquitto so MQTT alone delivers IN tags.
- Changing cascade/control math.

## Tracker
- Task: [SWD-141](https://marcusknielsen.atlassian.net/browse/SWD-141)
- Relates: SWD-140
- Branch: `cursor/swd-141-sp-level-req-file-33f4`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/57

## Next
`/ship SWD-141`
