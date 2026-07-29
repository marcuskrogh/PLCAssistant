# Iterate: Soft-PLC HMI stuck offline — Start does nothing

## Status
**In Progress** — App **0.1.14**

## Prior work
- Task: SWD-135 (PR #49, App 0.1.13 — Lovelace status + Start/MODE wiring)
- Spec context: prior ITERATE.md (SWD-135)

## Problem
Operator feedback after 0.1.13:

1. **Soft-PLC status stuck at `offline`** — Mode STOP, Start permissive Off, Trip Off (entity defaults). Status never becomes `stopped` / `running`.
2. **Start does nothing** — pressing Start leaves the board unchanged; with Soft-PLC looking offline and permissive Off, the skid cannot be started from the HMI.

Root cause: thin integration subscribes to the retained App `status` topic **before** status sensors listen on the HA bus. The retained `stopped` payload is fired with no listener and never reapplied. Soft-PLC only republishes status on state change, so the chip stays `offline` indefinitely. OUT sensors also do not hydrate from the MQTT payload cache on add.

## Acceptance criteria
1. After Core restart / integration reload with Soft-PLC App Started + MQTT healthy, Soft-PLC status shows `stopped` (not stuck `offline`) without pressing Start/Stop.
2. Start permissive shows On when healthy idle; pressing **Start** moves status → `running` and MODE → `RUNNING`; process sensors respond.
3. Soft-PLC republishes status periodically (heartbeat) so a missed retained delivery self-heals; disconnect surfaces as `offline` (MQTT LWT).
4. Integration caches status/OUT MQTT payloads and hydrates sensors on add (no subscribe-before-listen loss).
5. App + integration version **0.1.14**.

## Out of scope
- Mosquitto / HA MQTT misconfiguration (ops) — status correctly stays `offline` when the App is not connected.
- New HMI features beyond recovering live status / Start.

## Tracker
- Task: [SWD-136](https://marcusknielsen.atlassian.net/browse/SWD-136)
- Relates: SWD-135
- Branch: `cursor/swd-136-soft-plc-offline-start-33f4`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/51

## Next
`/review-fix SWD-136` — Review and auto-fix until clean
