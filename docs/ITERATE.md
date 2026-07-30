# Iterate: Tank level settles away from setpoint (Soft-PLC plant IN silent)

## Prior work
- Task: [SWD-170](https://marcusknielsen.atlassian.net/browse/SWD-170)
- PR: [#72](https://github.com/marcuskrogh/PLCAssistant/pull/72) (merged, App **0.1.29**)
- Spec context: prior `docs/ITERATE.md` (SWD-170), packaging file bridge (SWD-139…141), Soft-PLC mock ownership (SWD-145)

## Problem
After App **0.1.29**, Operate **Process** shows live plant PVs, but the tank **settling level does not match Active level SP** (e.g. SP = 0.3 m while LT_TANK ≈ 0.4 m / `H_TANK_MAX`). Soft-PLC keeps **SP_FLOW** at max and **CMD_SPEED** at 100 % — open-loop fill while HMI sensors already show the high tank.

## Clarifications
- Soft-PLC stays **mock-unaware** (`HeldProcess`); plant physics remain in the integration simulator.
- Process ↔ Soft-PLC **primary** transport remains MQTT IN/OUT (mock ≡ field).
- The HA-config **file bridge** is the established MQTT-silent fallback (cmds, Soft-PLC OUT, `SP_LEVEL_REQ`). Plant IN must use the same fallback so cascade sees real PVs when MQTT plant→App is silent.
- HMI plant sensors (SWD-170) hydrate from the same-process bus and can look healthy while Soft-PLC still runs on HeldProcess holds — that asymmetry is the bug.

## Acceptance criteria
- [ ] Integration plant simulator writes plant IN tags (`LT_TANK`, `LT_RES`, `FT_INLET`) into shared `inputs.json` on flush (alongside MQTT publish)
- [ ] Soft-PLC `_apply_file_inputs` applies those plant tags (file first; live MQTT still wins on the same scan)
- [ ] MQTT-silent closed loop: after Start with a level SP, `LT_TANK` settles near `SP_LEVEL` (not stuck at `H_TANK_MAX` with CMD at 100 %)
- [ ] Soft-PLC remains on `HeldProcess` for the live App path
- [ ] Regression tests cover file plant IN + settle; inverted SWD-145 “ignore plant in inputs.json” expectation
- [ ] GitHub Actions CI runs the **full** `pytest` suite on push/PR
- [ ] App + integration **0.1.30**; dual trees synced

## Out of scope
- Retuning cascade gains / new PID forms
- Field (non-mock) I/O commissioning
- Changing Operate Lovelace layout beyond docs notes if needed

## Work packages
1. File-bridge plant IN (Soft-PLC + HassPlantSimulator + ha_config_bridge helpers)
2. Settle + MQTT-silent closed-loop regression tests
3. GitHub Actions CI workflow for full suite
4. Version bump 0.1.30 + packaging docs notes + sync

## Tracker
- Task: [SWD-171](https://marcusknielsen.atlassian.net/browse/SWD-171)
- Relates: [SWD-170](https://marcusknielsen.atlassian.net/browse/SWD-170)
- Branch: `cursor/swd-171-level-settle-ci-b0f4`
- PR: _(pending)_

## Next
`/review-fix SWD-171` — Review and auto-fix until clean
