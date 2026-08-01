# Implementation plan: App engineering surface (SWD-181)

## Summary
- Replace the empty/library-first App entry with a **mobile-first main page** of **Program cards**.
- Open a Program into **Diagram | Log | Settings** (+ **Back** to main).
- **Create** via a separate page → land on that Program’s **Diagram**; new Programs are **empty + unscheduled**.
- Keep today’s Diagram **edit + Hot Apply / Apply restart**.
- Scheduling UI deferred to [SWD-191](https://marcusknielsen.atlassian.net/browse/SWD-191); library-on-main / richer online stay on SWD-180 / SWD-183 / SWD-184.
- Acceptance: **unit**, **integration**, **system**.

## Scope

### In
- Main page: **one-column** Program cards (all viewports; mobile-first on every page)
- Card primary: **Program name**; secondary: unified status **running | not running | unscheduled**; **health** symbol **ok | warning | error**; tertiary richer KPIs only if cheap/present
- Always show the Program set (one card if only one Program)
- Create Program: **separate page** (name + optional description) → Save/Create → **that Program’s Diagram**
- New Programs: **empty**, **unscheduled** by default
- Program shell: top bar **Diagram | Log | Settings** + **Back** to main
- **Log**: chronological info/warn/error list for that Program
- **Settings**: same fields as create; Save keeps blocks; **Delete** with **Are you sure?** confirm
- Diagram: existing canvas editing + **Hot Apply** / Apply restart for the selected Program
- Wire UI to Soft-PLC **project API** (list/create/update/delete Programs; load selected Program body)
- Tests: unit + integration + system for load/navigate/create/settings/diagram/log paths

### Out (extend roadmap — small Tasks, not this mammoth)
- **Task/Program scheduling editor** → [SWD-191](https://marcusknielsen.atlassian.net/browse/SWD-191)
- Library define/edit hosted on main page → **SWD-180**
- Integration tag/datablock mapping → **SWD-184**
- Rich live values / force / deep online → **SWD-183**
- True multi-rate Task intervals; vendor IDE clone

## Decisions
| Topic | Decision |
|-------|----------|
| Entry UX | Always Program-cards main page (not auto-skip to single diagram) |
| Naming | **Program** (not Application); Soft-PLC → Task → Program → blocks |
| Status chip | One chip: running \| not running \| unscheduled |
| Health | ok / warning / error symbol; details via Log inside Program |
| Create | Separate page; then open new Program Diagram |
| New Program | Empty + unscheduled |
| Schedule | Deferred — SWD-191 |
| Edit logic | Inside Diagram (Hot Apply kept) |
| Rename/delete | Settings page; delete confirmed |
| Create/Settings fields | Name + optional description (same set) |
| Layout | One-column cards; mobile-first all pages |
| Main page | Navigate + create (not in-place diagram edit) |

## Constraints
- Dual trees (`plcassistant/` ↔ packaged App) stay synced when shipping
- Preserve SWD-182 project model and apply policy
- Hot apply auth unchanged (superuser); restart always available
- Soft-PLC remains mock-unaware

## Inputs (supportive)
- `docs/ROADMAP.md` (SWD-178), `docs/RESEARCH.md` (SWD-179), shipped SWD-182 (`/api/project`, Main + tank Program)
- `docs/surface/05-app-editor.md`

## Acceptance criteria
- [x] App load shows main Program cards (including unscheduled); name is the dominant card label
- [x] Each card shows status (running / not running / unscheduled) and health (ok / warning / error)
- [x] Create Program → create page → Save → Diagram of new empty unscheduled Program; card appears on main after Back
- [x] Program top bar: Diagram | Log | Settings + Back to main
- [x] Log shows chronological info/warn/error entries (empty list OK)
- [x] Settings can rename/description-save without losing blocks; delete requires confirm and removes Program
- [x] Diagram retains edit + Hot Apply / Apply restart for the selected Program
- [x] Mobile: one-column cards; Diagram/Log/Settings/Create usable on narrow viewports
- [x] **Unit** tests for Program list/create/settings/delete and status/health derivation helpers
- [x] **Integration** tests for App HTTP + project API round-trips (create → get → settings → delete)
- [x] **System** test: HA + App path loads project, shows cards, opens tank Program diagram

## Work packages
1. **Main Program cards** — Done (SWD-190)
2. **Program shell** — Done (SWD-192)
3. **Create + Settings** — Done (SWD-194)
4. **Diagram binding** — Done (SWD-195)
5. **Tests** — Done (SWD-193)
6. **Roadmap extend** — scheduling editor Task SWD-191

## Shipped
- App **0.1.33**
- Program cards main page; Diagram | Log | Settings; create → Diagram; Settings delete confirm
- Program-scoped APIs + user templates; Hot Apply retained
- PR [#77](https://github.com/marcuskrogh/PLCAssistant/pull/77)

## Tracker
- Provider: jira
- Story: [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)
- Task: [SWD-181](https://marcusknielsen.atlassian.net/browse/SWD-181)
- Sub-tasks: SWD-190, SWD-192, SWD-194, SWD-195, SWD-193 (Done)
- Follow-on Task: [SWD-191](https://marcusknielsen.atlassian.net/browse/SWD-191) (scheduling editor)
- Branch: `cursor/swd-181-app-engineering-surface-a52c`
- PR: [#77](https://github.com/marcuskrogh/PLCAssistant/pull/77)

## Next
Done — phase closed.
