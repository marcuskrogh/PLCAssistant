# Implementation plan: Online / runtime visibility + PID HMI faceplates (SWD-183)

## Summary
- Give Soft-PLC App **online visibility** of what is defined vs loaded/running, plus live tag/instance values on the engineering surface.
- Give operators **Lovelace faceplates** driven by Datablock-backed compound entities: a specialised **PID** card and a **generic list card** for other/custom blocks.
- Soft-PLC **PID mode logic** selects the active setpoint from Manual / Automatic / Remote SP sources; Datablock remains system source of truth (industrial SCADA style).
- Acceptance: **unit**, **integration**, and **system** tests for online visibility and PID mode/HMI path.

## Scope

### In
- Soft-PLC App online: loaded vs running / saved vs applied identity; live I/O tag values; live Diagram pin/instance overlays where practical
- PID SP-source modes: **Manual | Automatic | Remote** with Soft-PLC logic selecting `*_SP_MAN` / `*_SP_AUTO` / `*_SP_REM` → `*_SP`
- Writing Manual SP (or Remote SP) from HMI **auto-flips** mode to that source; return to Automatic requires **explicit** mode set
- Tunings and loop faceplate state live in the **PLC Datablock** (entities/HMI write into DB); DB is SoT
- HA **compound loop entity** (climate-like), e.g. `PLC_PID.INLET_FLOW` / domain entity with attributes for PV, SP, SP_MAN, SP_AUTO, SP_REM, mode, CV, tunings, status
- Lovelace **PID card** auto-configured by pointing at that one entity
- Lovelace **generic list card** for other library + custom blocks (same entity-hook pattern where applicable)
- Demo: rebuild tank level/flow loops to the new PID mode + Datablock + card contract
- Tests: unit (mode select / flip rules), integration (entity ↔ DB ↔ Soft-PLC), system (HMI/card path + App online)

### Out
- Classic **output Manual** (operator sets CV/valve directly, PID bypassed) — follow-on
- Additional specialised cards (beyond PID + generic) — later Tasks
- Certified SIL / force tables / field commissioning toolchains
- Replacing Lovelace with Soft-PLC-native SCADA
- Full DCS mode set (IMAN, ROUT, Program/Operator ownership split, etc.) — document as future

## Decisions
| Topic | Decision |
|-------|----------|
| Cards | Specialised **PID** + **generic list** for everything else; more specialised cards later |
| SoT | **Datablock / PLC DB**; HMI and entities write into it |
| PID modes (v1) | **SP-source** Manual \| Automatic \| Remote (research-informed; MAN≠CV override) |
| Mode flip | Write MAN SP → Manual; write REM SP → Remote; Auto only via explicit mode |
| Soft-PLC App | **Both** App online visibility **and** Lovelace cards in this Task |
| Card binding | **Climate-like compound entity**; card hooks one entity and auto-configures |
| Output Manual | Deferred |
| Cascade as separate mode | Not a fourth faceplate mode in v1; cascade/MPC use **Remote** (or Auto writer) SP source |

## Constraints
- Soft-PLC remains mock-unaware; plant dynamics stay integration-owned
- Extend Datablocks (SWD-184) + BindingTable; do not invent a parallel I/O language
- Dual trees synced when shipping App/package/integration changes
- Prefer HA patterns (climate / water_heater style entities + custom Lovelace card)
- Keep Tasks implementable; PID faceplate + generic card + App online may be multiple Sub-tasks but one delivery PR
- Bumpless transfer / SP-tracking niceties: implement best-effort if cheap; full DCS bumpless not required for Done

## Inputs (supportive — not substitutes for decisions above)
- `docs/ROADMAP.md` route order 7; Story [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)
- `docs/RESEARCH.md` (SWD-179) — online monitor / force / identity
- Industrial mode survey (define session): DCS MAN/AUTO/CAS/RCAS/ROUT; Rockwell PIDE; instrumentation texts — SP-source Remote is typical; MAN often means CV override (deferred here)
- Prior: SWD-181 App surface, SWD-180 generic PID, SWD-184 Datablocks
- Existing: `GET /api/runtime` tag snapshot; schedule saved vs applied; Program card run status

## Acceptance criteria
- [ ] App shows clear **defined / saved vs loaded/applied vs running** state for Soft-PLC / Programs
- [ ] App online path surfaces live **tag** values and meaningful **instance/pin** live values on the engineering surface
- [ ] Soft-PLC PID (demo loops) implements **Manual / Automatic / Remote** SP selection into the active SP tag
- [ ] Writing Manual SP from HMI/entity flips mode to Manual; same for Remote; Automatic requires explicit mode write
- [ ] Tunings + mode + faceplate fields persist in Datablock / entity SoT and round-trip Soft-PLC ↔ HA
- [ ] Compound **PID loop entity** exists; Lovelace **PID card** configures from that entity alone
- [ ] **Generic list card** works for non-PID / custom blocks via a documented entity hook
- [ ] Demo tank HMI uses the PID card(s) for level and/or flow loop with clean operator UX
- [ ] **Unit** tests: mode multiplexer + auto-flip rules; entity attribute schema
- [ ] **Integration** tests: Datablock/entity ↔ Soft-PLC image for mode/SP/tunings
- [ ] **System** tests: App online visibility path + Lovelace/card (or API-equivalent) end-to-end

## Work packages
1. **PID SP-source mode logic + Datablock tag contract** — [SWD-217](https://marcusknielsen.atlassian.net/browse/SWD-217)
2. **HA compound PID loop entity platform** — [SWD-214](https://marcusknielsen.atlassian.net/browse/SWD-214)
3. **Lovelace PID card + generic list card** — [SWD-215](https://marcusknielsen.atlassian.net/browse/SWD-215)
4. **Soft-PLC App online visibility** — [SWD-213](https://marcusknielsen.atlassian.net/browse/SWD-213)
5. **Demo rebuild + docs** — [SWD-218](https://marcusknielsen.atlassian.net/browse/SWD-218)
6. **Tests** — [SWD-216](https://marcusknielsen.atlassian.net/browse/SWD-216)

## Open items
- Exact HA domain/platform name (`plcassistant_pid` vs extending existing platforms) — implement choice within climate-like decision
- Whether one compound entity covers both level and flow loops as two instances or two entities — implement: **one entity per loop instance**
- Depth of App Diagram pin overlay vs watch panel — implement may choose either as long as acceptance “live instance/pin values” is met
- SP-tracking / bumpless on mode change — best-effort; full DCS behaviour deferred

## Tracker
- Provider: jira
- Story: [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)
- Task: [SWD-183](https://marcusknielsen.atlassian.net/browse/SWD-183)
- Sub-tasks: SWD-217, SWD-214, SWD-215, SWD-213, SWD-218, SWD-216
- Branch: `cursor/swd-183-online-visibility-a52c`
- PR: *(draft — filled after open)*

## Next
`/implement SWD-183` — Build per this plan on the same branch/PR  
(or `/ship SWD-183` to finish remaining through Done)
