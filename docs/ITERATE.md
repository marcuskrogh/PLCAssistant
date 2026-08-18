# Iterate: Flow cascade slave defaults to Remote

## Prior work
- Task: [SWD-373](https://marcusknielsen.atlassian.net/browse/SWD-373)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/105 (App 0.1.64)
- Spec context: `docs/io/06-pid-faceplate.md`, `docs/RESEARCH.md` (MAN / AUTO / REM), SWD-221/223 mux

## Problem
The PID faceplate describes **REM** as cascade/remote and read-only. The flow loop is the cascade slave, but the backend defaults it to **Automatic** and treats Automatic as the cascade path (level CO → flow SP). Remote applied `SP_FLOW_REM` instead, so the highlighted mode did not match DCS cascade semantics.

## Clarifications
- Invoke was enough: align backend with the existing REM description; do not change MAN/AUTO/REM chrome copy.
- Level stays Automatic (primary). Flow demo default becomes Remote (slave CAS).
- Automatic on the flow loop becomes local SP (`SP_FLOW_REQ`), which is what AUTO means on a DCS slave.

## Acceptance criteria
- [x] Datablock and HA Number default `FLOW_MODE=2` (Remote)
- [x] Remote keeps the cascade wire (level CV → flow SP); faceplate writes none
- [x] Start with Level Auto + Flow Rem → `SP_FLOW` tracks `SP_FLOW_AUTO` and `CMD_SPEED` moves
- [x] Flow Automatic uses local `SP_FLOW_REQ`, not the level CV
- [x] Manual stays output Manual (`CO_FLOW_MAN`)
- [x] Docs + dual-tree + App **0.1.65**

## Out of scope
- Alarm-limit colour bands
- Retuning cascade PI copies
- Renaming `SP_FLOW_AUTO` (level CV OUT tag stays)

## Work packages
1. Backend mux + defaults (`FLOW_MODE=2`, REM=cascade, AUTO=`SP_FLOW_REQ`)
2. HA catalog / Number / compound sensor + docs
3. Tests, dual-tree, App 0.1.65

## Tracker
- Task: [SWD-383](https://marcusknielsen.atlassian.net/browse/SWD-383)
- Relates: [SWD-373](https://marcusknielsen.atlassian.net/browse/SWD-373)
- Branch: `cursor/swd-383-flow-cascade-remote-68c1`
- App: **0.1.65**

## Next
`/review-fix SWD-383` — Review and auto-fix on the new delivery PR
