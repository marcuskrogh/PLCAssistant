# Iterate notes: Configurable dynamics core + skid preset (SWD-146)

**Done** — App **0.1.22**; shipped PR [#63](https://github.com/marcuskrogh/PLCAssistant/pull/63) (`f53ca6f`)

## Shipped
1. Integration dynamics core (`ModelSpec`, fixed-step ≤100 ms) under `custom_components/plcassistant/dynamics/`
2. Skid preset ported from `MockProcess` (oracle tests at 1e-9)
3. HA `HassPlantSimulator`: status/`scan_period_s`, `CMD_SPEED` OUT → plant IN; freeze on offline/fault; CMD watchdog; retained-status hydrate on start
4. Plant Numbers display/nudge only (no competing MQTT while simulator owns)
5. Lovelace v10 live-motion copy; packaging/README/wedge docs; dual trees synced

## Operator note
Update App to **0.1.22+**, wait for Core reload. Expect live tank/reservoir/flow on Start.

## Next
`/define SWD-144` — Unit-op library + custom equation authoring (or `/define SWD-143` for mock UI)
