# Iterate notes: Soft-PLC ↔ integration mock ownership (SWD-145)

**Done** — App **0.1.21**; shipped PR [#59](https://github.com/marcuskrogh/PLCAssistant/pull/59) (0.1.20) + review-fix PR [#60](https://github.com/marcuskrogh/PLCAssistant/pull/60) (`53bdeda`)

## Shipped
1. Soft-PLC mock-unaware live path (`HeldProcess`); plant PVs MQTT IN
2. MQTT status / LWT include `scan_period_s`
3. Bindings / HMI / file-bridge cleaned; plant motion dark until SWD-146
4. review-fix: real plant LOS after sample trips; plant Numbers do not write `inputs.json`

## Operator note
Update App to **0.1.21+**, wait for Core reload. Expect static plant Numbers until SWD-146; Start still drives CVs/status.

## Next
`/define SWD-146` — Configurable dynamics core + skid preset
