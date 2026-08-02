# Iterate: Start still leaves PID CVs at 0 (post 0.1.44)

## Prior work
- Task: [SWD-224](https://marcusknielsen.atlassian.net/browse/SWD-224)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/87 (App 0.1.44)
- Spec context: screenshot — Level Man SP=0.3 / PV=0 / CV=0 while running

## Problem
1. Pressing Start did not engage PID loops — Level/Flow CVs stayed **0.00** while status showed running.
2. Soft-PLC file runtime omitted `SP_FLOW_AUTO` (HA file-bridge expected it).
3. File snapshot wrote bumpless-zero on Start then throttled updates while RUNNING.
4. `/api/apply` did not sync into the live Skid; missing `level_pi`/`flow_pi` silently published CV=0.

## Acceptance criteria
- [x] Soft-PLC file runtime mirror includes `SP_FLOW_AUTO`
- [x] While RUNNING, file runtime refreshes every scan (not stuck at Start bumpless zero)
- [x] Program Apply (hot/restart) syncs into the live Skid loader
- [x] Missing `level_pi`/`flow_pi` falls back to CascadeController so Start still drives CVs
- [x] Screenshot repro (Level Man SP=0.3, PV=0, Flow Auto) → CVs rise
- [x] App/integration **0.1.45**; dual trees synced; pytest green

## Out of scope
- Classic output Manual
- Full multi-program prefer_context redesign

## Work packages
1. File mirror SP_FLOW_AUTO + per-scan refresh while RUNNING — done
2. Apply → Skid sync + cascade fallback — done
3. Tests + version bump — done (`tests/test_swd225_acceptance.py`)

## Tracker
- Task: [SWD-225](https://marcusknielsen.atlassian.net/browse/SWD-225)
- Relates: SWD-224
- Branch: `cursor/swd-225-start-pid-cvs-still-zero-5ef6`
- PR: *(opening)*

## Next
`/review-fix SWD-225` — Review and auto-fix until clean
