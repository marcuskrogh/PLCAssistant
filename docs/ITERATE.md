# Iterate: Tank level settles away from setpoint (Soft-PLC plant IN silent)

**Done** — App **0.1.30**; shipped PR [#73](https://github.com/marcuskrogh/PLCAssistant/pull/73)

## Prior work
- Task: [SWD-170](https://marcusknielsen.atlassian.net/browse/SWD-170)
- PR: [#72](https://github.com/marcuskrogh/PLCAssistant/pull/72) (merged, App **0.1.29**)
- Spec context: prior `docs/ITERATE.md` (SWD-170), packaging file bridge (SWD-139…141), Soft-PLC mock ownership (SWD-145)

## Problem
After App **0.1.29**, Operate **Process** showed live plant PVs, but the tank **settling level did not match Active level SP** (e.g. SP = 0.3 m while LT_TANK ≈ 0.4 m / `H_TANK_MAX`). Soft-PLC kept **SP_FLOW** at max and **CMD_SPEED** at 100 % — open-loop fill while HMI sensors already showed the high tank.

## Clarifications
- Soft-PLC stays **mock-unaware** (`HeldProcess`); plant physics remain in the integration simulator.
- Process ↔ Soft-PLC **primary** transport remains MQTT IN/OUT (mock ≡ field).
- The HA-config **file bridge** is the MQTT-silent fallback (cmds, Soft-PLC OUT, `SP_LEVEL_REQ`, and plant IN).
- HMI plant sensors (SWD-170) hydrate from the same-process bus and can look healthy while Soft-PLC still runs on HeldProcess holds — that asymmetry was the bug.

## Acceptance criteria
- [x] Integration plant simulator writes plant IN tags (`LT_TANK`, `LT_RES`, `FT_INLET`) into shared `inputs.json` on flush (alongside MQTT publish)
- [x] Soft-PLC `_apply_file_inputs` applies those plant tags (file first; live MQTT still wins on the same scan)
- [x] MQTT-silent closed loop: after Start with a level SP, `LT_TANK` settles near `SP_LEVEL` (not stuck at `H_TANK_MAX` with CMD at 100 %)
- [x] Soft-PLC remains on `HeldProcess` for the live App path
- [x] Regression tests cover file plant IN + settle; inverted SWD-145 “ignore plant in inputs.json” expectation
- [x] GitHub Actions CI runs the **full** `pytest` suite on push/PR
- [x] App + integration **0.1.30**; dual trees synced

## Out of scope
- Retuning cascade gains / new PID forms
- Field (non-mock) I/O commissioning
- Changing Operate Lovelace layout beyond docs notes if needed

## Shipped
1. Plant IN file-bridge (`inputs.json`) + Soft-PLC apply path
2. Hardenings from review-fix: flock merge, finite coerce, stale plant expiry, file-before-MQTT
3. Settle + MQTT-silent closed-loop regression tests
4. GitHub Actions full pytest CI
5. review-fix CLEAN after 2 iters (iter1: 4SF; iter2: 0)
6. App **0.1.30**

## Tracker
- Task: [SWD-171](https://marcusknielsen.atlassian.net/browse/SWD-171)
- Relates: [SWD-170](https://marcusknielsen.atlassian.net/browse/SWD-170)
- Branch: `cursor/swd-171-level-settle-ci-b0f4`
- PR: [#73](https://github.com/marcuskrogh/PLCAssistant/pull/73)

## Next
Done — phase closed.
