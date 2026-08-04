# Iterate: Simplify pump flow limits

## Prior work
- Task: [SWD-250](https://marcusknielsen.atlassian.net/browse/SWD-250)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/98 (App 0.1.53)
- Spec context: docs/BUG.md (SWD-250), cascade `cv_max` repair, structured `q_pump_max` fields

## Problem
After SWD-250, changing pump flow capacity is still hard and misleading:

1. **PID “max pump cmd”** (`flow_pi.cv_max`) is CMD_SPEED % (0–100). Raising it does not increase plant flow — inlet flow still caps at plant `q_pump_max` (~8 L/min).
2. **Sim pump block `q_max`** can be set to a literal number, unlinking from global Max pump flow. That desyncs plant capacity from cascade `level_pi.cv_max` (flow SP clamp) and control jumps/hunts.

Operators need **one** capacity knob that keeps plant and Soft-PLC cascade limits coherent.

## Clarifications
- Invoke was rich; no further clarifying questions.
- Plant capacity unit remains **L/min** (`q_pump_max`). Flow PID CV stays **% speed** (0–100).
- Soft-PLC sync uses the existing HA-config file bridge (App mounts `homeassistant_config`).

## Acceptance criteria
- [x] Model Settings **Max pump flow** is the single plant-capacity control
- [x] Pump unit-op block does not create a second capacity: numeric edits write through to `q_pump_max` and keep `q_max: "q_pump_max"`; save/apply normalizes aliases
- [x] Soft-PLC cascade `level_pi.cv_max` tracks plant `q_pump_max` via capacity bridge file; `flow_pi.cv_max` remains 100 (% CMD_SPEED)
- [x] Soft-PLC PID overlay labels make units obvious (L/min vs %); helper points capacity changes at Max pump flow
- [x] Changing Max pump flow + Apply updates the capacity bridge; cascade repair/load picks it up without hunting from desynced limits
- [x] Regression tests + App/integration version bump (dual trees) — App **0.1.54**

## Out of scope
- Auto-retuning PID gains when capacity changes (large gain changes may still need manual tune)
- Lovelace faceplate redesign
- Non-cascade custom PID programs (only `level_pi` / `flow_pi` roles sync)

## Work packages
1. Dynamics: pump-block write-through + document normalize; capacity bridge write on save/apply — done
2. Soft-PLC: read capacity bridge in cascade limit repair; overlay labels/helpers — done
3. Align default `CASCADE_SP_FLOW_MAX` with default `q_pump_max` (8.0) — done
4. Tests + version 0.1.54 + dual-tree sync — done

## Tracker
- Task: [SWD-251](https://marcusknielsen.atlassian.net/browse/SWD-251)
- Relates: SWD-250
- Branch: `cursor/swd-251-simplify-pump-flow-limits-3043`
- App: **0.1.54**

## Next
`/review-fix SWD-251` — Review and auto-fix (single pass)
