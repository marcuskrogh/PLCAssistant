# Implementation plan: Control semantics (SWD-85)

## Summary
- Soft-PLC core is an **IEC 61131-shaped cyclic scan**: IN → **safety** → **control** → OUT each cycle — not HA event callbacks as the control engine.
- **Continuous FB semantics** (cascade PI) run *inside* the scan with explicit `dt`, clamps, anti-windup, and bumpless Start.
- **Safety** at this ambition = latched trips / permissives / LOS on non-GOOD every scan, forcing CV to safe — **not** SIL, dual-channel, or formal verification of user programs.
- HA remains the **async I/O / HMI bus**; events update a sample buffer that the scan samples — they do not execute mid-scan logic.

## Scope
**In**
- Scan scheduler contract: period notion, injectable `dt`, fixed phase order, optional overrun/jitter diagnostics (hobby-grade)
- Continuous FB / PID minimum for wedge cascade: sample time = scan `dt`, P+I required, D optional/off by default, output clamps, conditional anti-windup, bumpless integral init on Start
- Safety precedence relative to continuous loops: evaluate every scan **before** control writes; trip/stop force `CMD_SPEED = 0` and freeze/disable integrators
- Mode enable rules: continuous FBs active only when `MODE = RUNNING` and pump permit; `STOP`/`TRIPPED` hold last SPs on HMI side as already specified
- Document HA↔cyclic boundary (sample buffer vs scan clock); align wedge control/runtime to the locked semantics
- Contract/unit tests covering scan order, safety override, anti-windup, bumpless Start, `dt` injectability
- Update wedge control story notes that deferred exact PID/timing to SWD-85

**Out**
- SIL / IEC 61508/62061 compliance, certified safety PLC, dual-channel I/O
- Full IEC 61131-3 language runtime (LD/ST/SFC editors) — programming surface is SWD-82
- IEC 61499 event-driven FB distribution as primary mental model
- Quantitative autotune / research-grade cascade tuning
- Change-detect OUT writes (still every-scan flush per SWD-86)
- Final packaging / Add-on install shape (SWD-84)
- Physical rig commissioning
- Formal model checking of user programs

## Decisions
- **Cyclic 61131-shaped core** over 61499-first; HA keeps async distribution
- Scan order locked: **IN → safety → control → OUT**
- Safety and control share the same scan; demo target period ≤ 100 ms (align packaging/mock timebase); `dt` injectable (no wall-clock hard-coding in core)
- Cascade FB: PI sufficient for v1; D deferred (API may reserve Td = 0)
- Anti-windup: conditional integration (clamp + freeze I when pushing further into saturation) — already sketched in wedge; lock as required behavior
- Bumpless Start: initialize integrals so first RUNNING scan does not jump `CMD_SPEED` / `SP_FLOW` unboundedly
- Trip/Stop: reset or freeze integrators; CV = 0 immediately
- Overrun/jitter: optional diagnostic counters/hooks only — not hard real-time guarantees
- Non-GOOD PV: safety LOS trips as wedge; control must not treat non-GOOD as live PV (existing `is_good` collapse)

## Constraints
- Preserve SWD-83 wedge tag names, cascade structure, modes, and five safety behaviors
- Preserve SWD-86 I/O image + quality + scan-boundary IN/OUT APIs
- Soft-PLC owns the scan clock; thin integration only feeds/sinks the image
- Must not claim SIL or “verified PLC” in docs or UX copy
- Demo-grade gains/timing OK; document defaults; leave tuning knobs (`PID_*`) as already sketched in I/O contract

## Acceptance criteria
- Documented scan contract states phase order, `dt` rules, and safety-before-control precedence
- Documented FB contract covers PI sample time, clamps, anti-windup, bumpless Start, disable-on-not-RUNNING
- HA↔cyclic boundary documented: events → buffer; scan samples image; no mid-scan HA-driven logic
- Wedge runtime (`plcassistant/wedge`) implements the locked order and FB behaviors (or thin adapter if scan shell lives beside skid)
- Tests prove: safety can zero CV the same scan a trip asserts; integrators do not wind unboundedly at clamp; Start does not produce an unbounded CV step; `dt` is caller-supplied; fixed phase order observable
- No real HA required for green tests

## Work packages
1. **Scan scheduler contract** — phase order, period/`dt`, overrun hooks → `docs/control/01-scan-scheduler.md`, scan shell sketch in `plcassistant/control/` (or wedge scan façade) ([SWD-103](https://marcusknielsen.atlassian.net/browse/SWD-103))
2. **Continuous FB / PID semantics** — cascade PI contract (clamps, anti-windup, bumpless, Ts=`dt`) → `docs/control/02-fb-pid.md`, align `plcassistant/wedge/control.py` ([SWD-105](https://marcusknielsen.atlassian.net/browse/SWD-105))
3. **Safety precedence in the scan** — safety-before-control, CV force-zero, integrator disable → `docs/control/03-safety-precedence.md`, align skid/safety orchestration ([SWD-104](https://marcusknielsen.atlassian.net/browse/SWD-104))
4. **HA↔cyclic boundary note** — sample buffer vs scan clock; cross-links to `docs/io/` → `docs/control/04-ha-cyclic-boundary.md` ([SWD-101](https://marcusknielsen.atlassian.net/browse/SWD-101))
5. **Wedge control-story update** — retire “PID/timing deferred to SWD-85” where now locked; point to control docs ([SWD-102](https://marcusknielsen.atlassian.net/browse/SWD-102))
6. **Contract/unit tests** — scan order, trip same-scan CV=0, anti-windup, bumpless Start, injectable `dt` ([SWD-106](https://marcusknielsen.atlassian.net/browse/SWD-106))

## Open items
- ~~Exact default scan period constant vs config field name~~ — resolved: `scan_period_s` default `0.1`
- ~~Whether D term lands as stub (`Td=0`) or is omitted from API until needed~~ — resolved: `level_td` / `flow_td` stubs at 0
- ~~Whether scan shell lives in new `plcassistant/control/` package vs extending `plcassistant/wedge/skid.py` only~~ — resolved: `plcassistant/control/` + Skid uses `ScanShell`
- ~~Overrun diagnostic surface (tag vs log-only)~~ — resolved: `ScanDiagnostics` counters (not HMI tags)

## Tracker
- Provider: jira
- Story: [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81)
- Task: [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85)
- Research: [`docs/RESEARCH.md`](RESEARCH.md)
- Sub-tasks:
  - [SWD-103](https://marcusknielsen.atlassian.net/browse/SWD-103) — Scan scheduler contract
  - [SWD-105](https://marcusknielsen.atlassian.net/browse/SWD-105) — Continuous FB / PID semantics
  - [SWD-104](https://marcusknielsen.atlassian.net/browse/SWD-104) — Safety precedence in the scan
  - [SWD-101](https://marcusknielsen.atlassian.net/browse/SWD-101) — HA↔cyclic boundary note
  - [SWD-102](https://marcusknielsen.atlassian.net/browse/SWD-102) — Wedge control-story update
  - [SWD-106](https://marcusknielsen.atlassian.net/browse/SWD-106) — Contract/unit tests

## Delivered
- Specs: `docs/control/` (01–05), wedge control/I/O/follow-on cross-links
- Code: `plcassistant/control/` (`ScanShell`), cascade bumpless + anti-windup, Skid phase orchestration
- Tests: `tests/test_swd85_acceptance.py` — `python3 -m pytest -q` — 121 passed at ship
- Shipped: [PR #18](https://github.com/marcuskrogh/PLCAssistant/pull/18) merge `a51cdbe`

## Next
Done — phase closed. Suggested initiative next: `/define SWD-82` (research: `docs/RESEARCH.md`)
