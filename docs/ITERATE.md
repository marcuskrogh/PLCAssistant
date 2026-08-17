# Iterate: Align builtin PID with IFAC 2024 reference implementation

## Prior work
- Task: [SWD-360](https://marcusknielsen.atlassian.net/browse/SWD-360) (algorithm); [SWD-366](https://marcusknielsen.atlassian.net/browse/SWD-366) (latest ship)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/101 (App 0.1.55); https://github.com/marcuskrogh/PLCAssistant/pull/102 (App 0.1.56)
- Spec context: docs/PLAN.md, docs/RESEARCH.md, IFAC-PapersOnLine 58(7) 370–375 (doi:10.1016/j.ifacol.2024.08.090)

## Problem
The shipped builtin PID follows ISA-TR5.9 names and a simplified hybrid update. It does not implement the IFAC 2024 reference (Sundström, Hägglund, Bauer, Eker, Soltesz) that this iterate takes as the standardisation source:

- Listing 1 incremental law with `u_old` / `up_old` / `ud_old` / `uff_old`
- Listings 2–3 critically damped second-order measurement filter and ZOH
- Jitter scale `Tx`
- Output Manual (`auto` / `uman`) and external `windup` on the integral increment

## Clarifications
- Invoke named the paper as the standardisation reference; no further questions.
- ISA-TR5.9 names stay: `pv` ≈ y, `sp` ≈ r, `cv` ≈ u, `beta` ≈ b.
- `ki` stays in 1/s so wedge tunings do not change (`Dui = ki * e * dt`).
- `running` stays the permit pin. Lovelace Man / Auto / Rem stays the setpoint-source mux.
- Wedge cascade PI copies bypass the measurement filter (`tf_ts = 0`) so they do not need retuning.
- Reimplement from the paper; do not vendor github.com/copybit/pid.

## Acceptance criteria
- [x] Builtin PID listing-1 incremental update, including `ki = 0` bias `u0` and tracking
- [x] Second-order measurement filter (paper `TfTs` default 10) with ZOH; `tf_ts <= 0` bypasses
- [x] `Tx = dt / ts` scales derivative and documents jitter; integral uses `ki * dt`
- [x] Pins `auto` (default true), `uman`, `windup` (0 none / 1 upper / 2 lower / 3 both)
- [x] `running` false still holds or zeros CO; Lovelace SP-source modes unchanged
- [x] Wedge `level_pi` / `flow_pi` still settle without retuning
- [x] Unit tests cover filter, auto/manual, windup, Tx, and equation ≡ Python reference
- [x] Docs + dual-tree sync + App **0.1.57**

## Out of scope
- Lovelace UI for output Manual
- Series form / external-reset feedback / percent-of-range scaling
- Threaded listing-5 runtime (Soft-PLC scan is the runtime)
- Autotune
- Vendoring copybit/pid

## Work packages
1. Python reference (`plcassistant/control/pid.py`) + equation helpers
2. Builtin PID equation, pins/params, bumpless seed
3. Tests, docs, App 0.1.57, dual-tree sync

## Tracker
- Task: [SWD-367](https://marcusknielsen.atlassian.net/browse/SWD-367)
- Relates: SWD-360, SWD-366
- Branch: `cursor/swd-367-ifac-pid-reference-6900`

## Next
`/review-fix SWD-367` — Review and auto-fix on the new delivery PR
