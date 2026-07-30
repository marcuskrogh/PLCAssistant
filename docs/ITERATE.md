# Iterate: Per-equation state/measurement authoring (SWD-167)

## Prior work
- Task: [SWD-166](https://marcusknielsen.atlassian.net/browse/SWD-166) — sidebar Dynamics block editor (App 0.1.25)
- Relates: [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143)

## Problem
The Dynamics UI still hides the actual dynamical equations. Custom ODE is a JSON blob; predefined blocks show only help text. Soft-PLC tags are identity maps to state keys — there is no first-class **measurement equation** surface (`y = g(x, u, θ)`).

Operators need to enter **state equations one at a time** and **measurement equations one at a time**, with predefined blocks exposing the same dynamical information. The surface must stay generic enough for arbitrary processes built from custom + catalog blocks.

## Design locks
1. **State equations** — one row per integrated variable: `state` + `d(state)/dt` expression (custom blocks). Catalog ops expose the same form (read-only, bind/param substituted).
2. **Measurement equations** — document-level rows: Soft-PLC **tag** + expression over state / inputs / params (and closed-form algebraics). Distinct from ODEs.
3. **Algebraic signals** (optional on custom blocks) — one row per `name = expr` written each step (not integrated).
4. **Backward compat** — legacy `outputs: {TAG: state_key}` synthesizes identity measurements; identity measurements still populate `output_tags` for Number nudge.
5. **Soft-PLC** remains mock-unaware; plant math stays in the thin integration.

## Example processes (verification cases — tests, not shipped presets)
| Example | States | Measurements | Intent |
|---------|--------|--------------|--------|
| FO lag | `y` ← `(u - y)/tau` | `Y_OUT = y` | Minimal custom state + identity meas |
| Single tank + orifice | `h` via tank; `q = k√h` algebraic | `LT = h`, `FT = k*sqrt(h)` | Catalog + closed-form meas |
| Heated tank | `h`, `T` custom ODEs | `LT = h`, `TT = T + bias` | Non-identity measurement |
| Mass-spring-damper | `x`, `v` | `POS = x`, `VEL = v` | Multi-state custom |
| RC filter | `v_c` ← `(u - v_c)/(R*C)` | `V_OUT = v_c` | Pure custom |
| skid_composed | existing ops | identity tags | Oracle vs SkidModel unchanged |

## Acceptance criteria
1. Custom block inspector: add/remove **state equation** rows; optional **algebraic** rows — no JSON blob required.
2. Document panel: add/remove **measurement** rows (tag + expr), separate from state ODEs.
3. Predefined blocks show substituted state/algebraic equation forms in the inspector.
4. Compiler/runtime evaluates measurement expressions for MQTT IN; legacy `outputs` still load.
5. Automated tests cover the six example processes above (behavior + editor contracts).
6. App + integration **0.1.26**; dual trees synced.

## Out of scope
- Soft-PLC program canvas / Ingress plant UI
- Mid-scan live graph rewiring without Apply
- Broad chem-eng catalog beyond existing ops
- Drawn wire graph (typed binds remain)

## Tracker
- Task: [SWD-167](https://marcusknielsen.atlassian.net/browse/SWD-167)
- Branch: `cursor/swd-167-ode-equations-ux-33f4`
- Implement: App **0.1.26** — In Review

## Next
`/review-fix SWD-167`
