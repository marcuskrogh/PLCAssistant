# Iterate notes: Unit-op library + custom equation authoring (SWD-144)

**In Review (define)** — PLAN locked on `cursor/swd-144-unit-ops-define-33f4`

## Define locks
1. Unit ops compile → one collected `ModelSpec` (SWD-146 stepper unchanged)
2. v1 catalog: `tank`, `pump`, `orifice`, `lag`, `custom_ode` (skid decomposition)
3. Math AST whitelist sandbox (not Soft-PLC surface `exec`)
4. YAML/JSON model documents; live default stays code `skid`
5. HA UI / preset chooser → SWD-143

## Next
`/implement SWD-144` — after define approval
