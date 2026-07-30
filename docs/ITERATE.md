# Iterate: Soft-PLC stuck TRIPPED after settle — stale plant file LOS

## Prior work
- Task: [SWD-171](https://marcusknielsen.atlassian.net/browse/SWD-171)
- PR: [#73](https://github.com/marcuskrogh/PLCAssistant/pull/73) (merged, App **0.1.30**)
- Spec context: prior `docs/ITERATE.md` (SWD-171 plant IN file-bridge + stale demotion)

## Problem
After App **0.1.30**, Soft-PLC shows **MODE=TRIPPED**, **Trip active=On**, **Start ready=Off**. Operator cannot Reset or Start — process stuck.

## Clarifications
- Soft-PLC stays mock-unaware (`HeldProcess`).
- Root cause: SWD-171 demotes plant file tags to BAD/UNAVAILABLE after 5 s without a fresh `ts`. Plant **coalesces unchanged GOOD publishes**, so once levels settle the file timestamps stop refreshing → Soft-PLC latches `LOS_LT_*` / `LOS_FT_INLET`. Reset fails while those conditions remain “bad”.
- Real LOS (explicit BAD/FAULT from the plant) must still trip.

## Acceptance criteria
- [ ] Settled plant (unchanged PVs for >5 s) must **not** latch LOS from file age alone
- [ ] Stale/missing plant file `ts`: hold last good (skip apply); do **not** force BAD/UNAVAILABLE
- [ ] Plant publishes a file/MQTT heartbeat for plant tags even when value coalesce would skip
- [ ] After a real LOS clears, Reset → STOP → Start works
- [ ] Regression tests: settle-without-LOS + Reset recovery; update prior stale-demote expectation
- [ ] App + integration **0.1.31**; dual trees synced

## Out of scope
- Changing trip thresholds / cascade tuning
- Lovelace trip-code display redesign

## Work packages
1. Soft-PLC: stop demoting stale plant file tags to LOS
2. PlantSimulator: heartbeat publish for settled PVs
3. Tests + version bump

## Tracker
- Task: [SWD-173](https://marcusknielsen.atlassian.net/browse/SWD-173)
- Relates: [SWD-171](https://marcusknielsen.atlassian.net/browse/SWD-171)
- Branch: `cursor/swd-173-trip-stale-los-b0f4`

## Next
`/review-fix SWD-173` — Review and auto-fix until clean
