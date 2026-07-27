# 05 — Control semantics acceptance

**Tracker:** [SWD-106](https://marcusknielsen.atlassian.net/browse/SWD-106)  
**Parent:** [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85) · [`docs/PLAN.md`](../PLAN.md)

## Checklist

Automated in `tests/test_swd85_acceptance.py` (and related unit tests). No real HA.

| # | Criterion | Proof |
|---|-----------|-------|
| 1 | Phase order IN → SAFETY → CONTROL → OUT | `ScanShell` + `Skid.scan_phases` |
| 2 | Injectable `dt` (no hidden wall-clock in FB) | cascade / skid accept caller `dt` |
| 3 | Trip same scan → `CMD_SPEED = 0` | skid trip inject while RUNNING |
| 4 | Anti-windup: I does not grow unboundedly at clamp | cascade saturation test |
| 5 | Bumpless Start: no unbounded CV jump on Start | prepare_bumpless / skid Start |
| 6 | `scan_period_s` default 0.1; overrun counter when duration > period | `ScanDiagnostics` |
| 7 | Existing wedge mock acceptance still green | `tests/test_mock_acceptance.py` |

## Commands

```bash
python3 -m pytest -q
```
