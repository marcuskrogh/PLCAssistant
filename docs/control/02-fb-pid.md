# 02 — Continuous FB / PID semantics

**Tracker:** [SWD-105](https://marcusknielsen.atlassian.net/browse/SWD-105)  
**Parent:** [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Lock **minimum continuous function-block semantics** for the wedge cascade
(level → flow SP → speed) inside the Soft-PLC scan.

Code: `plcassistant.wedge.control` (`CascadeConfig`, `CascadeController`).

## Structure (unchanged from SWD-83)

```text
  SP_LEVEL ──► [Level PI] ──► SP_FLOW ──► [Flow PI] ──► CMD_SPEED
                  ▲                            ▲
               LT_TANK                      FT_INLET
```

## Sample time

- `Ts = dt` for both loops (caller-injected each scan).
- No internal wall-clock.
- `dt == 0`: no integral advance; outputs still recomputed from P (+ held I).

## PI with D stub

| Term | v1 |
|------|----|
| P | Required |
| I | Required (may be tuned to 0) |
| D | **Stub only** — `level_td` / `flow_td` default **0** and are ignored |

## Clamps

| Signal | Range |
|--------|-------|
| `SP_FLOW` | `[sp_flow_min, sp_flow_max]` (default 0 … 8 L/min; tracks plant `q_pump_max`) |
| `CMD_SPEED` | `[cmd_speed_min, cmd_speed_max]` (default 0 … 100 %) |

## Anti-windup (required)

**Incremental clamp** on the builtin PID (`PID_EQUATION`): listing 1 of the
IFAC 2024 reference adds `Δu` to `u_old` then saturates, so the integrator
cannot wind past `cv_min` / `cv_max`. When `ki = 0`, `u_old` is reset to bias
`u0` each auto scan (P / PD). External `windup` can also freeze the integral
increment in one or both directions.

The legacy `CascadeController` fallback (no block instances) still uses
**conditional integration**: accumulate integral only when the unsaturated
output is inside the clamp, or when error drives **out** of saturation.
When saturated and error would push further into the clamp, **freeze** I.

## Bumpless Start (required)

On rising edge of pump permit (`MODE` → `RUNNING`):

1. Call `prepare_bumpless(...)` before the first RUNNING `step`.
2. Initialize integrals so level loop holds prior `SP_FLOW` and flow loop
   targets `CMD_SPEED = 0` (post-Stop/trip).
3. First RUNNING scan must not produce an unbounded CV jump from empty I.

Wedge `Skid` performs this automatically on Start.

## Disable when not RUNNING

When `running` is false (STOP / TRIPPED / no permit):

- Reset integrators
- Hold last `SP_FLOW`
- Force `CMD_SPEED = 0`

## Builtin PID (SWD-367)

The Soft-PLC **PID** template is ISA-TR5.9 Parallel with the IFAC 2024
incremental reference (`plcassistant.control.pid.pid_scan` /
`plcassistant.surface.builtin.PID_EQUATION`). The wedge cascade still places
two **PI** copies (`kd = 0`, `tf_ts = 0`) at `level_pi` / `flow_pi`. Filter
bypass keeps those copies from needing retuning. ISA-TR5.9 Series form and
external-reset feedback remain later work.

## Non-goals

- Autotune / quantitative gain scheduling
- ISA-TR5.9 Series form and external-reset feedback
- Classic output Manual on the Lovelace card
