# Iterate: Start does not drive PID CVs — unify tag↔pin wirings

## Prior work
- Task: [SWD-223](https://marcusknielsen.atlassian.net/browse/SWD-223)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/86 (App 0.1.43)
- Spec context: prior `docs/ITERATE.md`, `docs/surface/06-wedge-migration.md`, `docs/io/06-pid-faceplate.md`

## Problem
1. Starting the process did not actually start the PID loops — underlying CVs (`SP_FLOW_AUTO`, `CMD_SPEED`) made no useful change after Start when faceplate gains were not on the live instances.
2. Process tag ↔ PID pin bridging was hardcoded in Skid; individual wirings were hard to regression-test.
3. Flow Man/Rem mutated `program.wires` in place each tick.

## Clarifications
- Soft-PLC Start → `MODE=RUNNING` → `pump_permit` drives both PID `running` pins via declarative tag↔pin wirings.
- Faceplate tunings must affect the executing PID copies (instance params), not only CascadeConfig.
- Test the **format** (apply IN/OUT once for any wire list) — not per-tag wiring tests.

## Acceptance criteria
- [x] RUNNING + Level Manual SP ≠ PV + Flow Automatic → `SP_FLOW_AUTO` and `CMD_SPEED` rise within ≤30 scans
- [x] Tag↔pin wirings use one common `{tag, instance, pin, dir}` format applied by shared helpers
- [x] Generic unit tests cover format apply (IN and OUT) without per-wire tests
- [x] Writing `LEVEL_KP` / `FLOW_KP` (etc.) updates live `level_pi` / `flow_pi` instance params before the next tick
- [x] Flow Man/Rem overrides cascade into `flow_pi.sp` via `prefer_context` (no `program.wires` mutation)
- [x] App/integration **0.1.44**; dual trees synced; 590 pytest passed

## Out of scope
- Classic output Manual (operator sets CV directly)
- Renaming demo instance ids away from `level_pi` / `flow_pi` in the App UI

## Work packages
1. Add `TagPinWire` format + apply helpers + default cascade map — done
2. Skid: drive CONTROL I/O + gains through the format; Start→CV — done
3. Tests + docs + version bump (0.1.44) — done (`tests/test_swd224_acceptance.py`)

## Tracker
- Task: [SWD-224](https://marcusknielsen.atlassian.net/browse/SWD-224)
- Relates: SWD-223
- Branch: `cursor/swd-224-start-pid-io-wires-5ef6`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/87 (App 0.1.44) — draft

## Next
`/review-fix SWD-224` — Review and auto-fix until clean
