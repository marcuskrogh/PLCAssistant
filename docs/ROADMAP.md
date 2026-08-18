# Roadmap: ISA-101 / DCS-standard PID faceplates

## Destination

Operator PID faceplates follow ISA-101 high-performance HMI practice and the industrial analog-controller convention: paired vertical PV/SP bars, a horizontal CO bar, MAN / AUTO / REM modes, and grayscale emphasis of the writable parameter. ISA-TR5.9 names stay (PV, SP, CO). ANSI/ISA-112.00.01-2025 informs SCADA terminology and “keep an HMI style guide”, not faceplate geometry.

## Notes

- The February 2026 ISA announcement is **ISA-112** (SCADA lifecycle), not ISA-101.
- ISA-101 does not draw the two-bar layout; DCS analog-controller practice does. ISA-101 governs grayscale, colour-for-abnormal, analog indicators, consistent widgets.
- MAN means output Manual (write CO / Bauer `uman`). AUTO means local SP. REM means remote/cascade SP (not operator-writable on the faceplate).
- Colour remains reserved for caution/abnormal (SWD-366). Mode identity stays grayscale.
- Relates prior PID work: SWD-359, SWD-360, SWD-366, SWD-367.
- Research findings: [`docs/RESEARCH.md`](RESEARCH.md). Plan: [`docs/PLAN.md`](PLAN.md).

## Route

| Order | Task | Type | Blocked by | Status | Issue |
|-------|------|------|------------|--------|-------|
| 1 | Define & ship ISA-101 DCS PID faceplate (PV/SP bars, CO bar, MAN/AUTO/REM) | implement | — | Done | [SWD-369](https://marcusknielsen.atlassian.net/browse/SWD-369) |

## Cleared so far

- ISA-5.1 glyph, ISA-TR5.9 Parallel, Bauer/IFAC PID — PR [#101](https://github.com/marcuskrogh/PLCAssistant/pull/101) / [#103](https://github.com/marcuskrogh/PLCAssistant/pull/103)
- Lovelace ISA-101 colour-for-abnormal (no mode hues) — PR [#102](https://github.com/marcuskrogh/PLCAssistant/pull/102)
- PID faceplate sandbox + operator chrome (paned settings, SP ramp) — PR [#105](https://github.com/marcuskrogh/PLCAssistant/pull/105)

## Not yet specified

- Whether a later slice adds alarm-limit colour bands (HH/H/L/LL) on the PV bar (ISA-18.2 / analog-controller extras)
- Whether flow AUTO is relabelled CAS on the slave faceplate
- Percent-of-range internal scaling (ISA-TR5.9)

## Out of scope

- Full Operate dashboard rewrite to a four-level ISA-101 hierarchy
- Replacing Lovelace with a dedicated SCADA HMI product
- ISA-5.5 process-equipment glyphs
- Series form / external-reset feedback / autotune
- Colour-coding MAN / AUTO / REM (contrary to ISA-101)

## Tracker

- Provider: jira
- Story (map): [SWD-368](https://marcusknielsen.atlassian.net/browse/SWD-368)
- Tasks: [SWD-369](https://marcusknielsen.atlassian.net/browse/SWD-369)

## Next

Done — shipped PR [#104](https://github.com/marcuskrogh/PLCAssistant/pull/104)
