# Iterate: Cascade reliability — HA freeze, Start path, Level Man / Flow Auto

## Prior work
- Task: [SWD-220](https://marcusknielsen.atlassian.net/browse/SWD-220)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/83 (App 0.1.40)
- Spec context: `docs/io/06-pid-faceplate.md`, Operate Lovelace YAML

## Problem
1. After 0.1.40, HA Core tends to freeze / become unresponsive (cold-start Number hydrate publishes MQTT + locked file writes serially; plant sim ticks during setup).
2. Hard to Start / cascade appears broken: Flow mode defaulted Manual so published `SP_FLOW=0` while Level Manual is correct.
3. Operate primary control is Level REQ while default Level mode is Manual — writes do not move active SP. Level PID Auto row writes `SP_LEVEL_AUTO` but Soft-PLC mux prefers `SP_LEVEL_REQ`.

## Clarifications
- Cascade defaults must follow system semantics: **Level = Manual**, **Flow = Automatic**.
- Start with defaults must run cascade (Level Man SP → flow Auto → CMD_SPEED).
- Reliability/efficiency is in-scope; classic CV Manual remains out of scope.

## Acceptance criteria
- [x] `LEVEL_MODE` default Manual (`0`); `FLOW_MODE` default Automatic (`1`) in Soft-PLC Datablock, HA catalog, Number meta
- [x] Cold start: operator IN defaults seeded **once** (batched `in_values` + single file write); Numbers **do not** per-entity MQTT/file publish in `async_added_to_hass`
- [x] Plant simulator starts **after** platform entity setup; tick period not tighter than scan period (≤10 Hz)
- [x] Lovelace card resource registration is idempotent (once per Core process)
- [x] Level PID `sp_auto_entity` writes `SP_LEVEL_REQ` (mux Automatic writer); Operate board primary SP is Level Man
- [x] With defaults only: Start → RUNNING and Soft-PLC publishes non-zero cascade `SP_FLOW` / `CMD_SPEED` when level error exists (regression test)
- [x] App/integration **0.1.41**; dashboard version bump; dual trees synced; tests green

## Out of scope
- Full output-manual / bumpless flow CV override
- Redesigning the entire Operate UX beyond Start/wiring reliability

## Work packages
1. Cascade mode defaults (Level Man / Flow Auto)
2. Cold-start seed batch + defer plant sim + Lovelace register once
3. Faceplate / Operate wiring (REQ ↔ Auto, Man primary)
4. Tests + version + docs

## Tracker
- Task: [SWD-221](https://marcusknielsen.atlassian.net/browse/SWD-221)
- Relates: SWD-220
- Branch: `cursor/swd-221-cascade-reliability-a52c`

## Next
`/review-fix SWD-221` — Review and auto-fix until clean
