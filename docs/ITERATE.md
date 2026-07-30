# Iterate: Per-equation state/measurement authoring (SWD-167)

**Done** — App **0.1.26**; shipped PR [#69](https://github.com/marcuskrogh/PLCAssistant/pull/69)

## Prior work
- Task: [SWD-166](https://marcusknielsen.atlassian.net/browse/SWD-166) — sidebar Dynamics block editor (App 0.1.25)

## Shipped
1. Custom ODE: **state equations** one row at a time (`state` + `d(state)/dt`); optional **algebraic** rows
2. Document-level **measurement equations** (`TAG = expr` over state/inputs/params) — distinct from ODEs
3. Predefined blocks expose bind/param-substituted dynamics in the inspector
4. Compiler evaluates measurement expressions for MQTT IN; legacy `outputs` still load
5. Example-process tests: FO lag, tank+orifice, heated tank, MSD, RC, skid_composed oracle
6. review-fix CLEAN after 1 iter (measurement refresh + inventory dt=0 + default ODE)

## Operator note
Update App to **0.1.26+**. Open **PLCAssistant → Dynamics**: select a Custom ODE to edit equations; use **Measurement equations** for Soft-PLC tags; predefined blocks show their underlying forms.

## Tracker
- Task: [SWD-167](https://marcusknielsen.atlassian.net/browse/SWD-167)
- Relates: [SWD-166](https://marcusknielsen.atlassian.net/browse/SWD-166)
- Branch: `cursor/swd-167-ode-equations-ux-33f4`

## Next
Done — phase closed.
