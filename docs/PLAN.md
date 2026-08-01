# Implementation plan: Soft-PLC program organization model (SWD-182)

## Summary
- Introduce Soft-PLC **project organization**: Soft-PLC → **Task(s)** → **Program(s)** → blocks.
- Ship the **single tank example Program** under one default **Main** Task; the model **allows several Tasks**.
- Preserve Soft-PLC **`scan_period_s`** as the single scan rate (MQTT status → integration mock).
- Apply policy follows industrial practice: **Hot Apply** for Program logic/params; **Apply (restart)** for Task/Program structure.
- Minimal App/API JSON exposure of the tree; visual navigator deferred to SWD-181.
- Acceptance at **unit**, **integration**, and **system** (full HA + App + MQTT) levels.

## Scope

### In
- Naming/metaphor: Soft-PLC → Task → Program → blocks (hide Configuration/Resource; avoid “Application”)
- Schema + persistence for project organization (versioned); **legacy flat Program YAML auto-migrates** to Soft-PLC + Main Task calling that Program
- Runtime: one shared scan; Tasks run as **ordered priority passes**; each Task’s Program call list executes in order
- Each Program on **at most one** Task; Programs on no Task remain **defined but unscheduled**
- Tasks carry **priority + Program call order** only (no per-Task interval driving the scheduler)
- Default wedge content: **one** tank Program + **one** Main Task that calls it; additional Tasks allowed (empty until filled)
- Apply: structure changes → restart apply; Program body/params/wires → hot apply (existing hot-apply auth rules)
- Soft-PLC continues exposing **`scan_period_s`** on MQTT; mock continues to apply it
- Minimal HTTP/JSON API so App can get/put the Soft-PLC project tree (no full navigator UI)
- Tests: unit + integration + **system** (HA + App + MQTT)

### Out (later route Tasks / explicit defer)
- Visual App navigator / canvas multi-program UI → SWD-181
- Library inspectability + generic PID → SWD-180
- Integration multi-datablock tag mapping UI → SWD-184
- Online live-value / force UI → SWD-183
- True multi-rate / preemptive Task intervals
- Per-Task interval as scan driver
- Same Program on multiple Tasks
- IEC LD/ST languages; full vendor IDE clone

## Decisions
| Topic | Decision |
|-------|----------|
| Hierarchy naming | Soft-PLC → Task → Program → blocks |
| Shipped example | One tank Program |
| Multi-Task | Allowed; default one Main Task calling the tank Program |
| Scan rate | Soft-PLC `scan_period_s` only; MQTT → mock |
| Multi-Task semantics | One scan; priority-ordered Task passes |
| Task fields (v1) | Priority + Program call list (no scheduling interval) |
| Unscheduled Programs | Defined, not executed |
| Program↔Task | At most one Task per Program |
| Legacy YAML | Auto-wrap into Soft-PLC + Main + that Program |
| Hot vs restart | Industrial: logic/params hot; structure restart |
| App in this slice | Minimal API/JSON tree only |
| System tests | Full HA + App + MQTT |

## Constraints
- Soft-PLC remains mock-unaware (SWD-145); plant dynamics stay integration-owned
- Existing apply auth: hot apply still superuser; restart always available
- Dual trees (`plcassistant/` and packaged App) stay version-synced when shipping
- Do not invent visual navigator scope here

## Inputs (supportive — not substitutes for decisions above)
- Research: `docs/RESEARCH.md` (SWD-179)
- Roadmap: `docs/ROADMAP.md` (SWD-178)
- Existing: `docs/surface/01-block-model.md`, `04-apply-policy.md`, `scan_period_s` MQTT (SWD-145)

## Acceptance criteria
- [ ] Project schema loads Soft-PLC with ≥1 Task and ≥0 Programs; validates “Program on at most one Task”
- [ ] Legacy flat Program YAML migrates to Soft-PLC + Main Task + that Program without manual edit
- [ ] Shipped tank example is one Program under Main; additional empty Tasks can be declared
- [ ] Scan executes Tasks by priority; unscheduled Programs do not run; `dt` from Soft-PLC `scan_period_s`
- [ ] MQTT status still publishes `scan_period_s`; mock steps using it (regression)
- [ ] Restart apply required for Task/Program structure changes; Hot Apply allowed for Program logic/params
- [ ] App/API returns/accepts Soft-PLC → Tasks → Programs JSON (minimal; no navigator UI required)
- [ ] **Unit** tests cover schema, migration, scheduling rules, apply classification
- [ ] **Integration** tests cover loader/runtime + MQTT `scan_period_s` with mock consumer
- [ ] **System** test: HA + App + MQTT path loads migrated tank project and runs Main Task successfully

## Work packages
1. **Schema + migration** — Soft-PLC project model; legacy Program auto-wrap; validation (one Task per Program)
2. **Runtime + apply** — priority Task passes in one scan; restart vs hot classification for structure vs logic
3. **Wedge content** — ship single tank Program under Main Task; allow extra empty Tasks in schema
4. **Minimal App/API** — get/put project tree JSON; keep canvas behavior compatible (single Program view OK)
5. **Tests** — unit + integration + system (HA + App + MQTT) for setup/load/run of organized project

## Open items
- Exact JSON/YAML field names (`softplc` vs `project`, Task id conventions) — implementer default OK if documented
- Whether empty extra Tasks ship in the default wedge file or only via schema capability — prefer schema capability + tests; wedge file stays Main + tank only unless needed for demos
- System-test harness details (compose vs existing CI patterns) — follow repo conventions; must be full HA+App+MQTT

## Tracker
- Provider: jira
- Story: [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)
- Task: [SWD-182](https://marcusknielsen.atlassian.net/browse/SWD-182)
- Sub-tasks:
  - [SWD-187](https://marcusknielsen.atlassian.net/browse/SWD-187) Schema + legacy Program migration
  - [SWD-185](https://marcusknielsen.atlassian.net/browse/SWD-185) Runtime Task passes + apply policy
  - [SWD-188](https://marcusknielsen.atlassian.net/browse/SWD-188) Wedge tank Program under Main Task
  - [SWD-189](https://marcusknielsen.atlassian.net/browse/SWD-189) Minimal App/API project tree JSON
  - [SWD-186](https://marcusknielsen.atlassian.net/browse/SWD-186) Unit + integration + system tests (HA/App/MQTT)
- Branch: `cursor/swd-182-softplc-program-model-a52c`
- PR: *(opened with this commit)*

## Next
`/implement SWD-182` — Build per this plan (same branch/PR)
