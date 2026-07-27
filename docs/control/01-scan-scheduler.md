# 01 — Scan scheduler contract

**Tracker:** [SWD-103](https://marcusknielsen.atlassian.net/browse/SWD-103)  
**Parent:** [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Define the Soft-PLC **cyclic scan** shell: fixed phase order, injectable sample
time `dt`, configured period, and hobby-grade overrun diagnostics. This is the
IEC 61131-shaped runtime metaphor — not HA event callbacks as the control engine.

Code: `plcassistant.control` (`ScanPhase`, `ScanConfig`, `ScanShell`, `ScanDiagnostics`).

## Phase order (locked)

Every scan executes exactly:

```text
  ┌──────────────────────────────────────────────┐
  │  scan N                                      │
  │  1. IN       — refresh I/O image inputs      │
  │  2. SAFETY   — trips / permissives / modes   │
  │  3. CONTROL  — continuous FBs / cascade      │
  │  4. OUT      — flush outputs from image      │
  └──────────────────────────────────────────────┘
```

| Phase | Role |
|-------|------|
| **IN** | Sample bindings into the live `IoImage` (SWD-86 `scan_inputs` / `apply_input`) |
| **SAFETY** | Evaluate trips, latch, Start/Stop/Reset; decide pump permit |
| **CONTROL** | Cascade PI (and future FBs) using frozen image + permit |
| **OUT** | Flush written outputs (`scan_outputs` / `snapshot_outputs`) |

Safety **before** control is mandatory so a trip can force CV safe on the **same**
scan (see [`03-safety-precedence.md`](03-safety-precedence.md)).

## `dt` vs `scan_period_s`

| Symbol | Meaning |
|--------|---------|
| `dt` | Sample time passed into continuous FBs **this** scan (injectable; ≥ 0) |
| `scan_period_s` | Configured cycle period for scheduling / overrun (default **`0.1`**) |

Rules:

- Core FB/safety math **must not** read wall-clock; callers supply `dt`.
- Demo target: period ≤ 100 ms (`scan_period_s` default `0.1`).
- `dt == 0` is legal (hold continuous state; still run discrete safety/mode).
- Negative `dt` is an error.

## Overrun / jitter (hobby-grade)

`ScanDiagnostics` tracks:

| Field | Meaning |
|-------|---------|
| `scan_count` | Scans completed |
| `overrun_count` | Times `duration_s > scan_period_s` (when duration supplied) |
| `last_duration_s` | Last measured cycle duration (optional) |
| `last_dt_s` | Last injected `dt` |
| `last_phases` | Phases executed (must equal `PHASE_ORDER`) |

These are **counters / hooks**, not SIL timing guarantees and not required HMI tags.

## API sketch

```python
from plcassistant.control import ScanShell, ScanConfig

shell = ScanShell(ScanConfig(scan_period_s=0.1))
shell.run(
    dt=0.1,
    on_in=...,
    on_safety=...,
    on_control=...,
    on_out=...,
    duration_s=None,  # or measured wall time
)
```

Wedge `Skid.step` uses the same phase order (IN measurement → SAFETY → CONTROL →
plant/OUT façade) and exposes `scan_phases` / diagnostics on the snapshot.

## Non-goals

- Hard real-time / priority scheduling
- IEC 61499 event FB distribution
- Claiming deterministic cycle time under OS load
