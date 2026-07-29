# Iterate notes: Configurable dynamics core + skid preset (SWD-146)

**In Progress** — App **0.1.22**; implement on `cursor/swd-146-dynamics-core-define-33f4`

## Shipped in this PR
1. Integration dynamics core (`ModelSpec`, fixed-step ≤100 ms) under `custom_components/plcassistant/dynamics/`
2. Skid preset ported from `MockProcess` (oracle tests at 1e-9)
3. HA `HassPlantSimulator`: status/`scan_period_s`, `CMD_SPEED` OUT → plant IN; freeze on offline/fault; CMD watchdog
4. Plant Numbers display/nudge only (no competing MQTT while simulator owns)
5. Lovelace v10 live-motion copy; packaging docs updated; dual trees synced

## Operator note
Update App to **0.1.22+**, wait for Core reload. Expect live tank/reservoir/flow on Start.

## Next
`/review-fix SWD-146` — then `/ship SWD-146`
