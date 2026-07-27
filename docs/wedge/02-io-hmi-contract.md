# 02 — I/O & HMI contract

**Tracker:** [SWD-87](https://marcusknielsen.atlassian.net/browse/SWD-87)  
**Parent:** [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Freeze the **logical signal contract** for the gravity-drained tank skid: field I/O, commands, setpoints, status, and HMI surfaces. HA entity IDs are bound later (SWD-86); this doc owns **tag names, direction, units, and update expectations**.

## Conventions

| Convention | Rule |
|------------|------|
| Tag names | Upper snake case (`LT_TANK`) |
| Bools | `true` = active / asserted |
| Commands | Edge- or pulse-friendly; controllers must be idempotent on sustained `true` |
| Bad / missing PV | Per-tag quality on the I/O image (`GOOD` / `UNCERTAIN` / `BAD` + reason); see [`docs/io/01-image-quality.md`](../io/01-image-quality.md) |
| Speed | 0–100% of drive span |
| Flow | L/min volumetric |
| Level | m preferred; % of configured span allowed on HMI |

## Process inputs (PV)

| Tag | Description | Unit | Required | Notes |
|-----|-------------|------|----------|-------|
| `LT_TANK` | Process tank level | m | **Yes** | Primary controlled variable |
| `LT_RES` | Reservoir level | m | **Yes** | Dry-run protection |
| `FT_INLET` | Inlet volumetric flow | L/min | **Yes** | Inner cascade loop PV |
| `SC_PUMP` | Pump speed feedback | % | No | Use when drive provides it; else treat as unavailable |

### Quality / loss-of-signal

There are **no** separate `*_BAD` tags. Each process PV carries **per-tag quality** on the Soft-PLC I/O image (`QualityStatus` + optional `ReasonCode`), as defined in [`docs/io/01-image-quality.md`](../io/01-image-quality.md).

| PV tag | Quality consumed by | Notes |
|--------|---------------------|-------|
| `LT_TANK` | Safety / HMI | LOS when `not is_good(quality)`; HH only on `GOOD` |
| `LT_RES` | Safety / HMI | LOS when `not is_good(quality)`; LL only on `GOOD` |
| `FT_INLET` | Safety / HMI | LOS when `not is_good(quality)` |
| `SC_PUMP` | HMI (informational) | Optional; treat as unavailable when quality ≠ `GOOD` |

Safety collapses quality with `is_good` / `collapse_quality` — only `GOOD` is trustworthy. Mock / tests inject quality via `force_quality(tag, BAD|UNCERTAIN, reason)` (thin `force_*_BAD` wrappers may remain for harness convenience). Process tag **names** (`LT_TANK`, …) are unchanged.

## Process outputs (CV / commands)

| Tag | Description | Unit | Required | Notes |
|-----|-------------|------|----------|-------|
| `CMD_SPEED` | Pump speed command to VFD | % | **Yes** | 0 = stopped / minimum; 100 = max. Safety and Stop force 0 |

No outlet flow command, no valve position command in v1.

## Operator / HMI commands

| Tag | Description | Type | Behavior |
|-----|-------------|------|----------|
| `HMI_START` | Request run | bool cmd | Honored only if `PERM_OK` and not already running; see control + safety |
| `HMI_STOP` | Request stop | bool cmd | **Always** honored: leaves Running, `CMD_SPEED → 0` |
| `HMI_RESET` | Clear latched trips | bool cmd | Clears trips only when trip conditions are clear; see safety |

## Setpoints & limits

Default setpoint pattern is **split IN + OUT** (not one `INOUT`): **operator / HA request** on the IN tag, **active Soft-PLC setpoint** on the OUT tag. Only the request side is operator-writable; the active SP is logic-owned (mirrored for HMI). See [`docs/io/02-binding-model.md`](../io/02-binding-model.md).

| Tag | Description | Unit | Default (ref) | Direction | Notes |
|-----|-------------|------|---------------|-----------|-------|
| `SP_LEVEL_REQ` | Operator / HA tank level setpoint request | m | 0.20 | `IN` | Operator-writable; bound to `input_number` (or equivalent) |
| `SP_LEVEL` | Active tank level setpoint Soft-PLC is applying | m | 0.20 | `OUT` | Soft-PLC-owned outer loop SP; mirrored for HMI (not operator-writable) |
| `SP_FLOW_MAN` | Manual flow SP (optional mode) | L/min | 2.0 | — | Used only in Flow / Manual modes |
| `LIM_LEVEL_HH` | High-high tank trip | m | 0.36 | — | Safety threshold |
| `LIM_RES_LL` | Low-low reservoir trip | m | 0.05 | — | Dry-run threshold |
| `SP_FLOW_MAX` | Clamp on cascade flow SP | L/min | 6.0 | — | Protects pump/plumbing |
| `CMD_SPEED_MAX` | Clamp on speed command | % | 100 | — | Optional demotion limit |

Tunable PID gains are configured on the Soft-PLC cascade FB (SWD-85 —
[`docs/control/02-fb-pid.md`](../control/02-fb-pid.md)); expose placeholders if needed:

| Tag | Description |
|-----|-------------|
| `PID_LVL_*` | Level-loop gains / Ti / Td (implementation-defined) |
| `PID_FLOW_*` | Flow-loop gains / Ti / Td (implementation-defined) |

## Status & diagnostics (HMI-readable)

| Tag | Description | Type |
|-----|-------------|------|
| `MODE` | `STOP` \| `RUNNING` \| `TRIPPED` (extendable; see control story) | enum |
| `PERM_OK` | All Start permissives true | bool |
| `TRIP_ACTIVE` | Any latched safety trip | bool |
| `TRIP_CODE` | Latched reason(s); see safety story | enum / bitfield |
| `SP_FLOW` | Active flow setpoint (cascade output or manual) | L/min |
| `RUNNING` | Control intends to run pump (subject to trips) | bool |

Recommended live displays (Lovelace / dashboard): `LT_TANK`, `LT_RES`, `FT_INLET`, `SC_PUMP` (if present), `CMD_SPEED`, `SP_LEVEL_REQ`, `SP_LEVEL`, `SP_FLOW`, `MODE`, `TRIP_CODE`, `PERM_OK`, plus each PV’s quality when troubleshooting LOS.

## HMI surface (reuse HA)

| Need | Approach |
|------|----------|
| Start / Stop / Reset | HA buttons / scripts / services bound to command tags |
| Setpoints | `number` / `input_number` entities bound to **request** SP tags (`SP_LEVEL_REQ`, …) |
| Trends | HA recorder / Influx + Grafana — no new historian in this Task |
| Mimic | Lovelace cards showing PVs + `MODE` / trip banner |

## Binding notes (not owned here)

Thin config integration maps HA entities ↔ tags. Mock and field share the **same binding-fed image path** into the Add-on (mock entities in the thin integration; no special inject-into-runtime I/O branch). Exact mapping mechanics: [`docs/io/02-binding-model.md`](../io/02-binding-model.md), stub: [`docs/io/03-thin-integration-stub.md`](../io/03-thin-integration-stub.md) (SWD-86).

## Related specs

- Process: [`01-reference-process.md`](01-reference-process.md)
- Modes & cascade: [`03-control-story.md`](03-control-story.md)
- Trips & permissives: [`04-safety-story.md`](04-safety-story.md)
- I/O image & quality: [`docs/io/01-image-quality.md`](../io/01-image-quality.md)
