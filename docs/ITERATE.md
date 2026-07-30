# Iterate: Operate plant PVs still unavailable after 0.1.28

**Done** — App **0.1.29**; shipped PR [#72](https://github.com/marcuskrogh/PLCAssistant/pull/72)

## Prior work
- Task: [SWD-169](https://marcusknielsen.atlassian.net/browse/SWD-169) — BOX mode + plant Number hydrate/bus
- PR: [#71](https://github.com/marcuskrogh/PLCAssistant/pull/71) (merged, App **0.1.28**)
- Spec context: prior `docs/ITERATE.md` (SWD-169), `docs/PLAN.md` (SWD-146), Lovelace Operate board

## Problem
After App **0.1.28**, the Lovelace **Operate** board still showed blank / unavailable values for **Tank level**, **Inlet flow**, and related plant rows while Soft-PLC OUT sensors rendered correctly. SWD-169 assumed Number AUTO/slider rendering; post-ship evidence pointed at orphaned Number entity_ids and Numbers as a fragile HMI display surface vs Sensors.

## Clarifications
- Soft-PLC stays mock-unaware; MQTT IN remains process↔PLC transport.
- Process card **displays** plant PVs as Sensors (same hydrate/cache pattern as OUT).
- Plant Numbers remain for operator nudges.
- Active flow SP (`sensor.plcassistant_sp_flow`) stays on the Soft-PLC OUT path.
- Request SP (`SP_LEVEL_REQ`) keeps `{entry_id}_{tag}_req` unique_ids so Level setpoint does not orphan.

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

## Shipped
1. Plant IN Sensors + `in_values` cache / bus hydrate
2. Lovelace Process + history → sensors; dashboard version **15**
3. Registry orphan cleanup (unavailable-only) + stable plant unique_ids
4. review-fix CLEAN after 2 iters (iter1: SP_LEVEL_REQ unique_id / purge / run.sh / tests; iter2: 0)
5. App **0.1.29**

## Tracker
- Task: [SWD-170](https://marcusknielsen.atlassian.net/browse/SWD-170)
- Relates: [SWD-169](https://marcusknielsen.atlassian.net/browse/SWD-169)
- Branch: `cursor/swd-170-plant-in-sensors-b6e1`
- PR: [#72](https://github.com/marcuskrogh/PLCAssistant/pull/72)

## Next
Done — phase closed.
