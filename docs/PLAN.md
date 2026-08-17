# Implementation plan: ISA-101 DCS PID faceplate (SWD-369)

## Summary
- Replace the compact climate-style PID card with an **analog-controller faceplate**: two vertical bars (PV, SP), a horizontal **CO** bar, MAN / AUTO / REM, grayscale emphasis of the writable analog.
- Conform the original ask to the standards: **CO not MV**; MAN is **output Manual** (Bauer `auto`/`uman`); AUTO writes local SP; REM is remote/cascade (not operator-writable); no mode hues (ISA-101).
- Keep ISA-5.1 ε/P/I/D chrome and ISA-101 caution/abnormal colour from SWD-366.

## Scope
### In
- Lovelace `plcassistant-pid-card`: analog bars on the card face; click-to-set on the writable bar; typed numeric still available (dialog)
- Mode semantics: MAN = CO write (`auto=false`, `uman`); AUTO = local SP; REM = remote/cascade SP, PID running, bar not operator-writable
- Wedge scan: wire Bauer `auto`/`uman` from mode; flow AUTO stays cascade (slave CAS behaviour, existing SWD-221 default); flow MAN writes pump CO; level MAN writes level CO (cascade request)
- Compound PID sensor: `cv_man_entity`, scale attributes; CO Number IN tags `CO_LEVEL_MAN` / `CO_FLOW_MAN`
- Bumpless MAN entry: seed CO_MAN from last live CO when the operator selects MAN
- Tests + faceplate docs + dual-tree sync + App **0.1.58**

### Out
- Full ISA-101 four-level Operate rewrite
- Colour-coding modes; green AVEVA-style mode buttons
- Relabelling flow AUTO as CAS on the button (keep AUTO; slave AUTO remains cascade)
- Alarm-limit colour bands on PV (later)
- Series form / ERF / percent-of-range / autotune
- Changing pin name `cv` (label stays CO)

## Decisions
| Topic | Decision |
|-------|----------|
| ISA-112 vs ISA-101 | Linked announcement is ISA-112 (lifecycle/terminology). Faceplate chrome follows ISA-101 + DCS analog-controller convention. |
| Geometry | Two vertical bars PV (left) and SP (right); horizontal CO below. Numeric PV / SP / ε / CO stay on one row (SWD-228). |
| Output name | **CO** (ISA-TR5.9). User “MV” maps to this bar. |
| MAN | Output Manual. Highlight CO (grayscale selected chrome). Click CO bar / numeric writes `CO_*_MAN` → `uman`. PID `auto=false`. |
| AUTO | Local SP on the primary (level). Highlight SP. Click SP bar writes Auto SP. Flow AUTO remains cascade (SP entity is a sensor; SP bar not writable). |
| REM | Remote/cascade SP. No operator write from the faceplate. PID stays in auto. |
| Highlight | Outline / invert / stronger gray on the writable analog only. Colour still caution/abnormal only. |
| Click | Click on writable bar sets value from click position (clamped to scale). Typed Set remains in the dialog. |
| Scales | Level PV/SP 0–0.40 m; flow PV/SP 0–8 L/min; level CO 0–8 L/min; flow CO 0–100 %. |
| Defaults | Level AUTO (PID computes cascade request from `SP_LEVEL_REQ`); Flow AUTO (cascade). Level MAN is available for operator CO. |
| Bumpless | Selecting MAN copies live CO into `CO_*_MAN` before the algorithm holds. |
| Demo tags | New IN `CO_LEVEL_MAN`, `CO_FLOW_MAN`. Existing Man SP tags remain but are not the MAN write target. |

## Classification
- Class: feature
- Confidence: high
- Why: new analog-controller faceplate plus controller-mode semantics (output Manual) are a buildable product slice, not a defect fix

## Workflow
- Template: feature-standard
- Parameters:
  - implement.mode: single
  - implement.verify: tests
  - implement.iteration: one-shot
  - review.mode: single
  - review.depth: focused
  - side_paths: research
- Chain: implement → review-fix → ship
- Rationale: localised to faceplate JS + PID mode wiring; research already on this branch; not a new layer/API surface that needs multiagent full review

## Inputs
- Research: [`docs/RESEARCH.md`](RESEARCH.md)
- Model: —

## Constraints
- Dual trees (`plcassistant/` and `custom_components/plcassistant/`) stay in sync; run `scripts/sync-ha-app-package.sh`
- Wedge cascade must still settle: level CO → flow SP, flow CO → `CMD_SPEED`
- Do not reintroduce `--pid-man` / `--pid-auto` / `--pid-rem` hues
- Keep SWD-227 click routing: mode only from `button[data-mode]`; Set never hijacked
- Dialog stays a sibling of `.pid-card` (overflow:hidden on the card only)
- Default `pytest` stays fast (no live marker unless the stack is required)
- Issue keys stay off product surfaces (card copy, Lovelace yaml)

## Acceptance criteria
- [ ] PID card shows two vertical bars (PV, SP) and a horizontal CO bar
- [ ] MAN highlights CO (grayscale); click/set writes CO; algorithm holds `uman`
- [ ] AUTO highlights SP when the Auto SP entity is a Number; click/set writes local SP
- [ ] REM does not highlight a writable analog; PID remains in auto
- [ ] Colour still only caution/abnormal (ε bands, CO clamp); no mode hues
- [ ] ISA-5.1 ε/P/I/D chrome retained; KPIs PV / SP / ε / CO at 2dp
- [ ] Level AUTO + Flow AUTO cascade still settles after Start
- [ ] Unit/JS tests cover writable target, bar click mapping, MAN hold, and faceplate contract
- [ ] Dual-tree sync + App **0.1.58**

## Work packages
1. **Controller-mode contract + CO_MAN tags + Bauer auto/uman wiring**
2. **Lovelace analog-controller PID card (bars, highlight, click-to-set)**
3. **Tests, docs, dual-tree, App 0.1.58**

## Open items
- Alarm-limit colour bands on PV — later
- Relabel flow AUTO as CAS — later if operators find AUTO on the slave confusing

## Tracker
- Provider: jira
- Story: [SWD-368](https://marcusknielsen.atlassian.net/browse/SWD-368)
- Task: [SWD-369](https://marcusknielsen.atlassian.net/browse/SWD-369)
- Sub-tasks: [SWD-370](https://marcusknielsen.atlassian.net/browse/SWD-370), [SWD-371](https://marcusknielsen.atlassian.net/browse/SWD-371), [SWD-372](https://marcusknielsen.atlassian.net/browse/SWD-372)
- Branch: `cursor/swd-369-isa101-pid-faceplate-5304`
- PR: [#104](https://github.com/marcuskrogh/PLCAssistant/pull/104)
- Classification: feature
- Workflow: feature-standard

## Next
`/review-fix SWD-369` — after implement lands on the draft PR
