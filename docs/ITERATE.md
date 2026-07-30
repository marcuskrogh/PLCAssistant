# Iterate notes: Unit-op library + custom equation authoring (SWD-144)

**In Progress** — App **0.1.23**; implement on `cursor/swd-144-unit-ops-implement-33f4`

## Shipped in this PR
1. Unit-op catalog: `tank`, `pump`, `orifice`, `lag`, `custom_ode`
2. Math AST whitelist sandbox (`expr.py`)
3. JSON/YAML model documents + compiler → collected `ModelSpec`
4. Composed skid document with 1e-9 oracle parity vs code `skid`
5. `PlantSimulator` typed to `DynamicsModel`; live default remains code `skid`

## Next
`/review-fix SWD-144` — then `/ship SWD-144`
