# Iterate notes: Soft-PLC ↔ integration mock ownership (SWD-145)

**In Review** — App **0.1.20**; PR [#59](https://github.com/marcuskrogh/PLCAssistant/pull/59)

## What changed
1. Soft-PLC retained MQTT `status` includes `scan_period_s` (one-way integration observe).
2. Live App scan uses `HeldProcess` — no `MockProcess` plant physics on the Soft-PLC path.
3. Plant tags (`LT_TANK`, `LT_RES`, `FT_INLET`) are Soft-PLC **IN** via MQTT; Soft-PLC publishes control/status OUT only.
4. Bindings / HMI / file-bridge cleaned up; plant motion dark until SWD-146 (intentional).
5. Docs updated for integration-owned simulator ownership.

## Operator check (HA OS)
1. Update App to **0.1.20+**, wait for Core reload.
2. Soft-PLC status MQTT JSON includes `scan_period_s`.
3. Start still drives `CMD_SPEED` / active SPs; tank/flow Numbers stay static until SWD-146.
4. Soft-PLC does not publish plant PVs as OUT.

## Next
`/review-fix SWD-145` then `/ship SWD-145`
