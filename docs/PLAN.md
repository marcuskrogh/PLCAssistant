# Implementation plan: Library inspectability + generic PID (SWD-180)

## Summary
- Ship one generic library block **`PID`** (full PID; D optional via `td=0` for PI loops).
- Remove opaque `level_pi` / `flow_pi` from the library; **auto-migrate** the tank program to two **PID** instance copies with level/flow params and wiring preserved.
- **Place = copy**: each placed block is an editable copy (equation + params); library edits do not rewrite existing instances.
- **Library editor** (top nav, mobile-first): edit shipped blocks (persist as new library definition; **Reset to default** for factory), add **custom** blocks; keep shipped vs custom clearly separated.
- Equations are **math expressions** (equation editor — not framed as Python), evaluated by the Soft-PLC.
- On Diagram: only **placed** blocks expose equation/params/wiring editing.
- Acceptance: **unit**, **integration**, **system**.

## Scope

### In
- Generic builtin (shipped) template **`PID`** with documented default math equations and standard pins/params (`pv`, `sp`, `running`, `cv`, `kp`, `ki`, `kd`/`td`, clamps, etc. as needed for full PID)
- Library no longer offers `level_pi` / `flow_pi`
- Migration: existing wedge/tank instances → two PID copies matching level and flow configuration + wiring
- Instance model: placed block stores its **own** equation/params copy; new placements clone current library definition
- Library editor UI from top nav (`Programs | Tasks | Library`): list shipped vs custom; edit; reset shipped to factory; create custom
- Persist library edits (shipped overrides + custom) across App restart
- Diagram: select placed block → edit equation (math), params, wiring
- Soft-PLC evaluates instance math expressions each scan (replace opaque native-only empty bodies)
- Tests: unit + integration + system for migration, equation exposure, PID instance mapping, library persist/reset

### Out
- Tag/datablock mapping UI → SWD-184
- Deep online live-value/force UI → SWD-183
- Requiring Python as the authoring language for block equations
- Auto-updating placed copies when the library definition changes
- Full clone of vendor library browsers beyond this editor

## Decisions
| Topic | Decision |
|-------|----------|
| Library shape | One generic **`PID`**; drop `level_pi`/`flow_pi` |
| Controller | Full PID; PI via D disabled (`td`/`kd` = 0) |
| Place semantics | Always a **copy** of the current library definition |
| Instance edit | Equation + params on the copy; does not change library or other instances |
| Library edit | Separate Library editor; persists as new library definition |
| Shipped vs custom | Clear separation; shipped can Reset to factory |
| Equation form | Math expressions (equation editor), Soft-PLC-evaluated |
| Diagram | Equations only on placed blocks (not bare library list) |
| Migration | Auto-migrate tank to two PID copies (level + flow wiring/params) |
| Entry | Top nav → Library |
| Layout | Mobile-first, one-column |

## Constraints
- Dual trees synced when shipping
- Preserve Program/Task surfaces from SWD-181/191
- Soft-PLC remains mock-unaware
- Structure/apply policy unchanged for Task/Program organization

## Inputs (supportive)
- `docs/ROADMAP.md`, `docs/RESEARCH.md` (generic PID practice — supportive only)
- `docs/surface/03-builtin-library.md`, shipped SWD-182/181/191 App surface
- Existing dynamics math-expression work (SWD-144 lineage) as a possible seam for evaluation — confirm in implement, do not assume product identity

## Acceptance criteria
- [x] Library lists **`PID`** (shipped) and custom blocks separately; no `level_pi`/`flow_pi` for new placements
- [x] Tank/wedge program migrates to two PID instances with level/flow params and wiring equivalent to prior cascade
- [x] Placing PID clones library definition onto the instance; editing instance equation/params does not change library or sibling instances
- [x] Library editor (top nav) can edit shipped PID, Reset to factory, and add/edit custom blocks; edits persist across restart
- [x] Placed-block UI shows math equation editor + params + wiring
- [x] Soft-PLC evaluates instance equations (level/flow loops still control as before under system test)
- [x] Mobile-first one-column Library and instance editors
- [x] **Unit** tests: PID defaults, copy-on-place, library override + reset, migration mapping
- [x] **Integration** tests: library API + place/edit instance equation + persist reload
- [x] **System** test: HA + App + MQTT path runs migrated tank with two PID instances

## Work packages
1. **Equation runtime + PID template** — [SWD-203](https://marcusknielsen.atlassian.net/browse/SWD-203)
2. **Copy-on-place + instance equation storage** — [SWD-202](https://marcusknielsen.atlassian.net/browse/SWD-202)
3. **Migration** — [SWD-205](https://marcusknielsen.atlassian.net/browse/SWD-205)
4. **Library editor UI + API** — [SWD-206](https://marcusknielsen.atlassian.net/browse/SWD-206)
5. **Diagram instance editor** — [SWD-201](https://marcusknielsen.atlassian.net/browse/SWD-201)
6. **Tests** — [SWD-204](https://marcusknielsen.atlassian.net/browse/SWD-204)

## Implementation notes
- PID pins: `pv`, `sp`, `running`, `cv`; params: `kp`, `ki`, `kd`, `td`, `cv_min`, `cv_max`, `hold_when_stopped`.
- Equation language is assignment-line math expressions evaluated by `plcassistant.surface.equations`; stateful assigned locals persist per instance.
- Shipped library overrides and global custom templates persist in the App JSON under `library`, outside the Soft-PLC project graph.

## Tracker
- Provider: jira
- Story: [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)
- Task: [SWD-180](https://marcusknielsen.atlassian.net/browse/SWD-180)
- Sub-tasks: SWD-203, SWD-202, SWD-205, SWD-206, SWD-201, SWD-204
- Branch: `cursor/swd-180-library-pid-a52c`
- PR: pending after push

## Next
`/review-fix SWD-180` — Review and auto-fix until clean
