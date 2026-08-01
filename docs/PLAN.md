# Implementation plan: Task/Program scheduling editor (SWD-191)

## Summary
- Add a mobile-first **Task editor** reached from a **top nav bar** on the App main page (above Programs).
- Full **Task CRUD** (create / rename-or-edit meta / delete) plus ordered **Program call lists** (add / remove / reorder).
- Picker only offers **unscheduled** Programs; one Program stays on at most one Task.
- Delete Task (with confirm) **unschedules** its Programs.
- Soft-PLC may have **zero Tasks**.
- **Save** persists schedule edits (survives navigation, reload, App restart); **Apply (restart)** commits to the live Soft-PLC.
- Extend Task model with optional **description**.
- Acceptance: **unit**, **integration**, **system**.

## Scope

### In
- Top nav from main (Program cards) → Task / Schedule editor
- Task list: select a Task; create Task (**id + priority + optional description**)
- Edit selected Task meta (id/priority/description as agreed with schema constraints)
- Ordered call list: add (from unscheduled only), remove, reorder
- Delete Task with **Are you sure?** → Programs on that Task become unscheduled
- Allow empty Soft-PLC (no Tasks)
- **Save** = persist project schedule to project-of-record (disk / App state) without requiring live apply
- **Apply (restart)** = restart-apply schedule into running Soft-PLC (SWD-182 structure rule)
- Unsaved-vs-saved-vs-applied UX clear enough that Save then leave/reload keeps the saved schedule ready to Apply
- Mobile-first, one-column layout
- API/schema: Task `description`; schedule mutate + persist + apply endpoints as needed
- Tests: unit + integration + system

### Out
- Per-Task scan intervals / multi-rate (still Soft-PLC `scan_period_s` only)
- Startup/phase one-shot sequences (Tasks remain cyclic call lists)
- Library-on-main (SWD-180), tag mapping (SWD-184), deep online (SWD-183)
- Changing Program body from the Task editor

## Decisions
| Topic | Decision |
|-------|----------|
| Entry | Top nav bar → Task editor (from main) |
| Editor | Full Task CRUD + ordered Program call lists |
| Picker | Only unscheduled Programs |
| Program↔Task | At most one Task (unchanged SWD-182) |
| Delete Task | Confirm; Programs become unscheduled |
| Empty project | Zero Tasks allowed (Main deletable) |
| Create fields | Id + priority + optional description |
| Reorder | Yes |
| Persist vs apply | **Save** persists; **Apply (restart)** to live Soft-PLC; saved survives nav/reload/restart |
| Layout | Mobile-first, one-column |
| Task semantics | Cyclic scan call lists (not startup procedures) |

## Constraints
- Structure changes still require restart apply for the *live* Soft-PLC (SWD-182)
- Dual trees synced when shipping
- Preserve Program cards / Diagram|Log|Settings from SWD-181
- Soft-PLC remains mock-unaware

## Inputs (supportive)
- `docs/ROADMAP.md` (SWD-178), shipped SWD-182 (Task/Program model), SWD-181 (App surface)
- `docs/surface/04-apply-policy.md`

## Acceptance criteria
- [ ] Top nav opens Task editor from main; mobile one-column usable
- [ ] Create Task with id, priority, optional description; list/select Tasks
- [ ] Add only unscheduled Programs; remove; reorder call list
- [ ] Delete Task with confirm unschedules its Programs; Soft-PLC may have zero Tasks
- [ ] Save persists schedule across navigation, reload, and App restart without Apply
- [ ] Apply (restart) loads saved schedule into live Soft-PLC; card status reflects scheduled vs unscheduled after apply
- [ ] Program still on at most one Task (picker + validation)
- [ ] **Unit** tests for Task description, picker eligibility, delete→unschedule, save-vs-apply separation
- [ ] **Integration** tests for Task CRUD + call-list HTTP/API + persist round-trip
- [ ] **System** test: HA + App path save schedule, reload App, then Apply; tank under Main (or equivalent) runs when applied

## Work packages
1. **Schema + persist/apply split** — Task `description`; saved project-of-record vs live applied project — [SWD-196](https://marcusknielsen.atlassian.net/browse/SWD-196)
2. **Task editor API** — CRUD Tasks, mutate call lists, Save, Apply (restart) — [SWD-199](https://marcusknielsen.atlassian.net/browse/SWD-199)
3. **App UI** — top nav + Task editor (list, create, call list, reorder, delete confirm); mobile-first — [SWD-200](https://marcusknielsen.atlassian.net/browse/SWD-200)
4. **Wire Program cards** — status updates after Apply; unscheduled after Task delete — [SWD-197](https://marcusknielsen.atlassian.net/browse/SWD-197)
5. **Tests** — unit + integration + system — [SWD-198](https://marcusknielsen.atlassian.net/browse/SWD-198)

## Open items
- Exact persistence mechanism (same `program_path` JSON with a pending flag vs dual snapshot) — implement chooses simplest honest seam that meets Save-survives-reload + Apply-restarts-live

## Tracker
- Provider: jira
- Story: [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)
- Task: [SWD-191](https://marcusknielsen.atlassian.net/browse/SWD-191)
- Sub-tasks: SWD-196, SWD-199, SWD-200, SWD-197, SWD-198
- Branch: `cursor/swd-191-task-scheduling-editor-a52c`
- PR: (opening)

## Next
`/review-fix SWD-191` — Review and auto-fix until clean
(or `/ship SWD-191` to finish remaining through Done)
