# Iterate notes: Unit-op library + custom equation authoring (SWD-144)

**Done** — App **0.1.23**; shipped PR [#65](https://github.com/marcuskrogh/PLCAssistant/pull/65)

## Shipped
1. Unit-op catalog: `tank`, `pump`, `orifice`, `lag`, `custom_ode`
2. Math AST whitelist sandbox (`expr.py`)
3. JSON/YAML model documents + compiler → collected `ModelSpec`
4. Composed skid document with 1e-9 oracle parity vs code `skid`
5. `PlantSimulator` typed to `DynamicsModel`; live default remains code `skid`
6. review-fix CLEAN after 1 iter (README 0.1.23 operator note)

## Operator note
Update App to **0.1.23+**. Live plant behavior unchanged (code `skid`). Unit-op authoring is in-code/file; HA chooser → SWD-143.

## Next
`/define SWD-143` — Integration mock UI + preset selection
