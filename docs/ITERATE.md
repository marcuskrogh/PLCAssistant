# Iterate: HMI zeros on SP_LEVEL/SP_FLOW/LT_RES + clarify PERM_OK while RUNNING

## Status
**In Progress** — App **0.1.18**; PR pending review

## Prior work
- Task: SWD-139 (PR #55, App 0.1.17 — HA-config file bridge)
- Spec context: prior ITERATE.md (SWD-139)

## Problem
After SWD-139 / App **0.1.17**, Soft-PLC runs and tank/flow/speed move, but:

1. **Start permissive** stays **Off** while Soft-PLC is `running` (operator unsure if correct; Start still worked).
2. **Active level SP**, **Active flow SP**, and **Reservoir level** stay **0.0** while tank/flow/speed show live values.

## Root cause
1. `PERM_OK` is intentionally false whenever MODE is RUNNING (safety story) — only meaningful as Start-ready when STOP. HMI label/help does not explain this.
2. SWD-139 file bridge only mirrors `MODE`/`PERM_OK`/`TRIP_ACTIVE`/`LT_TANK`/`FT_INLET`/`CMD_SPEED`. When MQTT is silent, `SP_LEVEL`/`SP_FLOW`/`LT_RES` never hydrate and stay at entity default 0.0.

## Acceptance criteria
1. File bridge (App write + integration poll) includes `SP_LEVEL`, `SP_FLOW`, `LT_RES` (and other Soft-PLC OUT HMI tags).
2. Lovelace clarifies Start permissive = Start-ready when idle; Off while RUNNING is expected.
3. After Update **0.1.18** + Core reload: while running near SP 0.2 m, Active level SP ≈ request, Active flow SP and Reservoir are non-zero (healthy mock).
4. App + integration version **0.1.18**.

## Out of scope
- Changing PERM_OK semantics (stays Off while RUNNING by design).
- Replacing MQTT; file bridge remains secondary fallback.

## Tracker
- Task: [SWD-140](https://marcusknielsen.atlassian.net/browse/SWD-140)
- Relates: SWD-139
- Branch: `cursor/swd-140-hmi-sp-tags-perm-33f4`
- PR: (see GitHub)

## Next
`/review-fix SWD-140`
