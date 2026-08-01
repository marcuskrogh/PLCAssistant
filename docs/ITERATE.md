# Iterate: Level/Flow PID Manual SP does not drive CV

## Prior work
- Task: [SWD-222](https://marcusknielsen.atlassian.net/browse/SWD-222)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/85 (App 0.1.42)
- Spec context: `docs/io/06-pid-faceplate.md`, `plcassistant/app/skid_scan.py`

## Problem
1. Setting Level Manual SP does not show a useful Level CV (stays 0 / masked).
2. Setting Flow Manual SP does not move Flow CV (`CMD_SPEED`) while RUNNING.
3. Soft-PLC canvas shows Level CV→Flow SP wire live, but published tags stay wrong.

## Clarifications
- SP-source Manual must drive the loop SP (PID still computes CV) — not classic output Manual.
- Cascade Automatic (Flow Auto) remains the default; Flow Man/Rem must engage the flow PI.

## Acceptance criteria
- [x] RUNNING + Flow Manual + `SP_FLOW_MAN>0` + `FT_INLET≈0` → `CMD_SPEED` rises (tracks Manual SP), even when level error≈0
- [x] RUNNING + Flow Automatic + Level Manual SP≠PV → `SP_FLOW_AUTO` (Level CV) > 0 and `CMD_SPEED` > 0
- [x] Level faceplate CV reads true level CV (`SP_FLOW_AUTO`), not Flow Man mux of `SP_FLOW`
- [x] Flow Manual with `SP_FLOW_MAN=0` does not hide Level CV on the faceplate
- [x] STOP/TRIPPED still forces `CMD_SPEED=0`
- [x] App/integration **0.1.43**; dual trees synced; regression tests; full pytest green

## Out of scope
- Classic output Manual (operator sets CV directly, PID bypassed)
- Retuning default PID gains

## Work packages
1. Soft-PLC: apply Flow Man/Rem SP to `flow_pi.sp` (override cascade wire for that tick) — done
2. Faceplate: Level CV → `SP_FLOW_AUTO` — done
3. Tests + docs + version bump — done (`tests/test_swd223_acceptance.py`, 584 passed)

## Tracker
- Task: [SWD-223](https://marcusknielsen.atlassian.net/browse/SWD-223)
- Relates: SWD-222
- Branch: `cursor/swd-223-pid-manual-cv-a52c`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/86 (App 0.1.43)

## Next
`/review-fix SWD-223` — Review and auto-fix until clean
