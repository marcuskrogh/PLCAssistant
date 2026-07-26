# 06 — Mock acceptance scenarios

**Tracker:** [SWD-89](https://marcusknielsen.atlassian.net/browse/SWD-89)  
**Parent:** [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Runnable checklist proving the mock skid meets PLAN acceptance: Start/Stop, cascade, and each safety case with latch + reset. Execute against the tag contract in [`02-io-hmi-contract.md`](02-io-hmi-contract.md).

**SWD-83 runnable bar:** the Skid / tag API (`plcassistant.wedge.skid`) is the HMI stand-in — drive Start/Stop/Reset, setpoints, and injectors through that surface (or tests wrapping it). A full Lovelace binding is packaging follow-on, not required to claim this checklist green.

## Preconditions (all scenarios)

- [ ] Mock process enabled ([`05-mock-process.md`](05-mock-process.md))
- [ ] HMI bound for Start / Stop / Reset, `SP_LEVEL`, live PVs, `MODE`, `TRIP_CODE`, `PERM_OK`
- [ ] Initial state: `MODE = STOP`, `TRIP_ACTIVE = false`, qualities good
- [ ] Suggested initials: `LT_TANK ≈ 0.15 m`, `LT_RES ≈ 0.20 m`, `SP_LEVEL = 0.20 m`
- [ ] Limits loaded: `LIM_LEVEL_HH = 0.36 m`, `LIM_RES_LL = 0.05 m`

---

## A — Start / Stop

### A1 — Start blocked when not permissive

1. Force `TRIP_ACTIVE` or force `LT_TANK` quality BAD (or leave a prior trip).
2. Confirm `PERM_OK = false`.
3. Issue `HMI_START`.
4. **Expect:** remain `STOP` / `TRIPPED`; `CMD_SPEED = 0`.

### A2 — Clean Start

1. Ensure all permissives (`PERM_OK = true`).
2. Issue `HMI_START`.
3. **Expect:** `MODE = RUNNING`, `CMD_SPEED` leaves 0 as cascade engages, `FT_INLET` rises when speed > 0.

### A3 — Stop always works

1. From `RUNNING`, issue `HMI_STOP`.
2. **Expect:** `MODE = STOP`, `CMD_SPEED = 0` promptly, no trip latch.

---

## B — Cascade holds / responds

### B1 — Level step up

1. Start (A2). Wait until roughly settled near `SP_LEVEL`.
2. Raise `SP_LEVEL` by ~0.05 m.
3. **Expect within a few mock time-constants:** `SP_FLOW` increases, `CMD_SPEED` increases, `FT_INLET` tracks upward, `LT_TANK` moves toward new SP.

### B2 — Level step down

1. Lower `SP_LEVEL` by ~0.05 m.
2. **Expect:** flow/speed decrease; tank level trends down (gravity drain dominates as pump slows).

### B3 — Drain disturbance (optional but recommended)

1. While `RUNNING`, increase mock `K_DRAIN`.
2. **Expect:** level dips then cascade increases `SP_FLOW` / `CMD_SPEED` to recover toward `SP_LEVEL`.

---

## C — High tank level trip

1. Start clean.
2. Inject / nudge `LT_TANK` to `>= LIM_LEVEL_HH` (or fill via high SP + max speed if preferred).
3. **Expect:** `TRIP_CODE` includes `HH_TANK`, `MODE = TRIPPED`, `CMD_SPEED = 0`, `TRIP_ACTIVE = true`.
4. Issue `HMI_START` while still high / latched.
5. **Expect:** Start rejected (`PERM_OK = false`).
6. Return `LT_TANK` below HH; issue `HMI_RESET`.
7. **Expect:** `TRIP_ACTIVE = false`, `MODE = STOP`.
8. Start again; **Expect:** runs.

---

## D — Low reservoir trip

1. Start clean.
2. Nudge `LT_RES` to `<= LIM_RES_LL`.
3. **Expect:** `LL_RES` latched, pump stopped, `MODE = TRIPPED`.
4. Reset while still low → **Expect:** reset fails / trip remains.
5. Restore `LT_RES` above LL; `HMI_RESET` → `STOP`; Start works again.

---

## E — Loss-of-signal trips

Repeat for each PV:

| Scenario | Injector | Trip code |
|----------|----------|-----------|
| E1 | `force_quality("LT_TANK", BAD, …)` / `force_LT_TANK_BAD` | `LOS_LT_TANK` |
| E2 | `force_quality("LT_RES", BAD, …)` / `force_LT_RES_BAD` | `LOS_LT_RES` |
| E3 | `force_quality("FT_INLET", BAD, …)` / `force_FT_INLET_BAD` | `LOS_FT_INLET` |

For each:

1. Start clean (`RUNNING`).
2. Force BAD quality on the PV.
3. **Expect:** immediate `CMD_SPEED = 0`, `MODE = TRIPPED`, matching `TRIP_CODE`.
4. Clear injector (quality good again); without Reset, **Expect:** still latched / not running.
5. `HMI_RESET` → `STOP`; Start succeeds.

---

## F — Latch discipline

1. Create any trip (C/D/E).
2. Confirm Stop path: if somehow Running, Stop still zeros speed; trip latch remains until Reset.
3. Confirm no auto-restart after Reset alone.

---

## Pass criteria (summary)

| Area | Pass when |
|------|-----------|
| Start/Stop | A2 + A3 pass; A1 blocks appropriately |
| Cascade | B1 and B2 directionally correct |
| HH / LL | C and D latch, block Start, require Reset |
| LOS | E1–E3 each latch and require Reset |
| Product note | Mock path documented as supported capability, not a discarded harness |

## Sign-off

| Role | Name | Date | Result |
|------|------|------|--------|
| Executor | | | ☐ pass ☐ fail |
| Reviewer | | | ☐ pass ☐ fail |

## Related specs

- Control: [`03-control-story.md`](03-control-story.md)
- Safety: [`04-safety-story.md`](04-safety-story.md)
- Mock: [`05-mock-process.md`](05-mock-process.md)
