# Iterate: Integration dashboard plant level/flow values unavailable

## Prior work
- Task: [SWD-146](https://marcusknielsen.atlassian.net/browse/SWD-146) — integration skid plant simulator + plant Number ownership
- PR: [#63](https://github.com/marcuskrogh/PLCAssistant/pull/63)
- Spec context: `docs/PLAN.md` (SWD-146/143), `custom_components/plcassistant/number.py`, Lovelace Operate board

## Problem
On the PLCAssistant Lovelace **Operate** board, **Process (IN — live simulator)** shows blank value areas for **Tank level**, **Reservoir level**, and **Inlet flow**, while Soft-PLC OUT rows (**Pump speed command**, **Active level/flow SP**) display correctly.

Plant Numbers relied on MQTT retain echo for display and used AUTO/slider mode, so mobile HMI often showed empty grey tracks with no readable engineering value — and missed same-process hydrate that OUT sensors already have.

## Clarifications
- Soft-PLC remains mock-unaware; MQTT IN stays the process↔PLC transport.
- HMI Numbers must show numerics immediately (box mode) and hydrate from the live plant simulator on add, with live updates via a HA bus event when the simulator publishes (MQTT remains for Soft-PLC).

## Acceptance criteria
- [x] Plant IN Number entities use box mode so Operate always shows a numeric value.
- [x] On add, simulator-owned plant Numbers hydrate from current plant outputs and write HA state (not MQTT-retain-only).
- [x] Plant simulator publishes fire `{domain}_plant_in` so Numbers update live without depending on MQTT round-trip for HMI.
- [x] MQTT subscribe path retained as secondary (Soft-PLC / external) update source.
- [x] Tests cover BOX mode + hydrate/bus wiring; App + integration version bumped to **0.1.28**; dual trees synced.

## Out of scope
- Soft-PLC HeldProcess / control / safety changes
- Redesigning Lovelace card layout beyond Number display mode
- Field (non-mock) I/O commissioning

## Tracker
- Task: [SWD-169](https://marcusknielsen.atlassian.net/browse/SWD-169)
- Relates: [SWD-146](https://marcusknielsen.atlassian.net/browse/SWD-146)
- Branch: `cursor/swd-169-plant-in-values-6867`
- PR: [#71](https://github.com/marcuskrogh/PLCAssistant/pull/71)

## Next
`/review-fix SWD-169` — Review and auto-fix until clean
