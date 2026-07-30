# Iterate: Operate plant PVs still unavailable after 0.1.28

## Prior work
- Task: [SWD-169](https://marcusknielsen.atlassian.net/browse/SWD-169) — BOX mode + plant Number hydrate/bus
- PR: [#71](https://github.com/marcuskrogh/PLCAssistant/pull/71) (merged, App **0.1.28**)
- Spec context: prior `docs/ITERATE.md` (SWD-169), `docs/PLAN.md` (SWD-146), Lovelace Operate board

## Problem
After App **0.1.28**, the Lovelace **Operate** board still shows blank / unavailable values for **Tank level**, **Inlet flow**, and related plant rows (Reservoir blank in the same card; operator report also flags **flow set point**). Soft-PLC OUT sensors (**Pump speed command**, **Active level SP**, **Active flow SP**) continue to render numeric values.

SWD-169 assumed blank grey tracks were Number AUTO/slider rendering and fixed BOX mode + simulator hydrate. Post-ship evidence shows plant rows remain unavailable while the sensor-based Soft-PLC rows work — pointing at:
1. Lovelace Process still bound to plant **Number** entity IDs that can be orphaned / unavailable after registry churn
2. Numbers remaining a fragile HMI display surface vs the proven OUT **Sensor** pattern

## Clarifications
- Soft-PLC stays mock-unaware; MQTT IN remains process↔PLC transport.
- Process card should **display** plant PVs as Sensors (same hydrate/cache pattern as OUT).
- Plant Numbers remain for operator nudges; they are not the primary Operate Process display.
- Active flow SP (`sensor.plcassistant_sp_flow`) stays on the Soft-PLC OUT path (already readable when Soft-PLC is attached).

## Acceptance criteria
- [x] Operate **Process (IN — live simulator)** shows numeric Tank level, Reservoir level, and Inlet flow via plant IN **sensors**
- [x] History graph uses the same plant IN sensor entity IDs
- [x] Integration caches plant IN payloads (`in_values`) and hydrates sensors on add + `plcassistant_plant_in` bus updates
- [x] Simulator flush writes `in_values` before MQTT publish so late entity add still hydrates
- [x] Stock Lovelace board refreshes (dashboard version bump) to the sensor entity IDs
- [x] Orphan cleanup: contracted plant Number entity_ids that are registry-unavailable are removed so nudge Numbers can reclaim them
- [x] Stable unique_ids for plant sensors/numbers keyed by `instance_id` + tag (not only config-entry id)
- [x] Tests cover sensor entity_ids, `in_values` cache wiring, and dashboard YAML; App + integration **0.1.29**; dual trees synced

## Out of scope
- Soft-PLC HeldProcess / control / safety changes
- Writable flow setpoint request (cascade still owns `SP_FLOW`)
- Field (non-mock) I/O commissioning

## Work packages
1. Plant IN sensors + `in_values` cache / bus hydrate
2. Lovelace Process + history → sensors; dashboard version bump
3. Registry orphan cleanup + stable unique_ids
4. Version **0.1.29**, dual-tree sync, regression tests

## Tracker
- Task: [SWD-170](https://marcusknielsen.atlassian.net/browse/SWD-170)
- Relates: [SWD-169](https://marcusknielsen.atlassian.net/browse/SWD-169)
- Branch: `cursor/swd-170-plant-in-sensors-b6e1`
- PR: *(opening)*

## Next
`/review-fix SWD-170` — Review and auto-fix until clean
