# Iterate: Start/cascade dead, PID setpoints broken, HA lockup

## Prior work
- Task: [SWD-221](https://marcusknielsen.atlassian.net/browse/SWD-221)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/84 (App 0.1.41)
- Spec context: `docs/io/06-pid-faceplate.md`, Operate Lovelace, Soft-PLC runtime

## Problem
1. HA Core still locks up occasionally under load.
2. Start often fails to engage cascade — no inlet flow / pump motion.
3. Start/Stop feel unresponsive.
4. Defaults do not yield a working cascade on Start.
5. PID card mode / setpoint Set appear broken.

## Clarifications
- Cascade defaults remain Level Manual / Flow Automatic.
- Operator expectation: Man/Rem/Auto SP Set engages that source (flip mode on Auto SP write too).

## Acceptance criteria
- [x] Soft-PLC operator IN: file seed wins over stale MQTT retain when file is newer (or MQTT re-applied after file for operator tags)
- [x] HA seed MQTT awaited (qos≥1, retain) before platforms; FLOW_MODE=1 / LEVEL_MODE=0 land on broker
- [x] No optimistic Soft-PLC `running` status before skid PERM_OK accepts Start
- [x] Plant CMD watchdog does not zero cmd across frozen→unfrozen; plant file writes ≤1 Hz; plant sleep = `_POLL_S` (≤10 Hz)
- [x] PID compound `sp` attribute = mux(mode, man, auto, rem), never stale OUT
- [x] PID card preserves typed drafts / focused inputs across hass updates
- [x] Writing Level Auto/REQ SP flips `LEVEL_MODE` to Automatic (parity with Man/Rem flips)
- [x] System test: defaults → Start → RUNNING + SP_FLOW>0 + CMD_SPEED>0; plant FT_INLET rises when CMD applied
- [x] App/integration **0.1.42**; dual trees synced; full pytest green

## Out of scope
- Full output-manual CV override
- Redesigning Operate layout beyond Start/wiring reliability

## Work packages
1. Soft-PLC IN precedence + seed MQTT await — done
2. Start status honesty + plant load/watchdog — done
3. PID faceplate mux + card draft UX + Auto flip — done
4. Tests + version + docs — done (`tests/test_swd222_acceptance.py`, 578 passed)

## Tracker
- Task: [SWD-222](https://marcusknielsen.atlassian.net/browse/SWD-222)
- Relates: SWD-221
- Branch: `cursor/swd-222-start-cascade-pid-a52c`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/85 (App 0.1.42)

## Next
`/ship SWD-222` — Merge PR and close the Task
