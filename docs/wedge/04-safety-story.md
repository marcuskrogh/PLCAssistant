# 04 — Safety story spec

**Tracker:** [SWD-93](https://marcusknielsen.atlassian.net/browse/SWD-93)  
**Parent:** [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Define the **illustrative middle-ground safety layer** for the v1 skid: five required behaviors, latch/reset, and Start permissives. This is **not** a SIL framework, certified safety PLC, or rich bypass/audit model.

## Required behaviors (locked)

| # | Behavior | Action | Latch |
|---|----------|--------|-------|
| 1 | High process tank level | Stop pump (`CMD_SPEED = 0`) | Yes |
| 2 | Low reservoir level | Stop pump (dry-run protect) | Yes |
| 3 | Loss-of-signal on `LT_TANK`, `LT_RES`, or `FT_INLET` | Stop pump | Yes |
| 4 | Latched trip + operator reset | Remain stopped until `HMI_RESET` with conditions clear | — |
| 5 | HMI Start / Stop | Start only if permissives OK; **Stop always** | — |

## Trip conditions

Use reference limits from the I/O contract (overridable in config).

| Trip code | Condition | Notes |
|-----------|-----------|-------|
| `HH_TANK` | `LT_TANK >= LIM_LEVEL_HH` **and** `is_good(LT_TANK quality)` | Prefer evaluating HH only on good quality; non-GOOD is its own LOS trip |
| `LL_RES` | `LT_RES <= LIM_RES_LL` **and** `is_good(LT_RES quality)` | Dry-run protect |
| `LOS_LT_TANK` | `not is_good(LT_TANK quality)` | Loss-of-signal / BAD / UNCERTAIN |
| `LOS_LT_RES` | `not is_good(LT_RES quality)` | Loss-of-signal / BAD / UNCERTAIN |
| `LOS_FT_INLET` | `not is_good(FT_INLET quality)` | Loss-of-signal / BAD / UNCERTAIN |

On any trip assert:

1. Set corresponding bit/flag in `TRIP_CODE`
2. `TRIP_ACTIVE ← true`
3. `MODE ← TRIPPED`
4. `RUNNING ← false`
5. `CMD_SPEED ← 0` **immediately** (no soft coast required for v1 demo)

Multiple trips may be latched simultaneously; Reset clears only those whose conditions are no longer true (or clears all only when **all** conditions clear — pick one policy and stick to it; **recommended:** clear all latched codes in one Reset **iff every** underlying condition is clear; otherwise keep remaining latches).

## Reset (`HMI_RESET`)

Allowed when:

- Operator issues `HMI_RESET`, and
- **All** active trip conditions are currently false (levels back in band; qualities good)

Effect:

- Clear `TRIP_CODE` / `TRIP_ACTIVE`
- `MODE ← STOP` (operator must Start again)
- Do **not** auto-restart the pump

If conditions still present: ignore Reset (or pulse a “reset failed” diagnostic); remain `TRIPPED`.

## Start permissives (`PERM_OK`)

`PERM_OK` is true iff **all** of:

| Check | Requirement |
|-------|-------------|
| No latch | `TRIP_ACTIVE = false` |
| Tank level quality | `is_good(LT_TANK quality)` |
| Reservoir quality | `is_good(LT_RES quality)` |
| Flow quality | `is_good(FT_INLET quality)` |
| Not already HH | `LT_TANK < LIM_LEVEL_HH` |
| Not already LL | `LT_RES > LIM_RES_LL` |
| Mode | `MODE = STOP` (not `RUNNING` / not `TRIPPED`) |

`HMI_START` succeeds only if `PERM_OK`.  
`HMI_STOP` does **not** consult `PERM_OK`.

## Stop vs trip

| Event | `MODE` | Latch | Needs Reset to run again? |
|-------|--------|-------|---------------------------|
| `HMI_STOP` | `STOP` | No | No — Start when `PERM_OK` |
| Any safety trip | `TRIPPED` | Yes | Yes |

## Operator visibility

HMI must show at least:

- `TRIP_ACTIVE` and human-readable `TRIP_CODE`
- `PERM_OK` (why Start is blocked)
- That Stop remains available while `RUNNING`

## Explicit non-goals

- SIL / PL ratings, dual-channel, safety-rated I/O
- Bypass keys, force, or audit trail beyond simple latch/reset
- Independent safety PLC hardware

## Related specs

- Tags: [`02-io-hmi-contract.md`](02-io-hmi-contract.md)
- Modes: [`03-control-story.md`](03-control-story.md)
- Acceptance cases: [`06-mock-acceptance.md`](06-mock-acceptance.md)
- Per-tag quality: [`docs/io/01-image-quality.md`](../io/01-image-quality.md)
