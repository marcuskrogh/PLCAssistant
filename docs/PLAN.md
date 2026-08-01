# Implementation plan: Task/Program scheduling editor (SWD-191)

## Summary
- Add a mobile-first **Task editor** reached from a **top nav bar** on the App main page (above Programs).
- Full **Task CRUD** (create / rename-or-edit meta / delete) plus ordered **Program call lists** (add / remove / reorder).
- Picker only offers **unscheduled** Programs; one Program stays on at most one Task.
- Delete Task (with confirm) **unschedules** its Programs.
- Soft-PLC may have **zero Tasks**.
- **Save** persists schedule edits (survives navigation, reload, App restart); **Apply (restart)** commits to the live Soft-PLC (including scan-loop Skid loader).
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
- **Apply (restart)** = restart-apply schedule into running Soft-PLC + live Skid loader
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
- [x] Top nav opens Task editor from main; mobile one-column usable
- [x] Create Task with id, priority, optional description; list/select Tasks
- [x] Add only unscheduled Programs; remove; reorder call list
- [x] Delete Task with confirm unschedules its Programs; Soft-PLC may have zero Tasks
- [x] Save persists schedule across navigation, reload, and App restart without Apply
- [x] Apply (restart) loads saved schedule into live Soft-PLC; card status reflects scheduled vs unscheduled after apply
- [x] Program still on at most one Task (picker + validation)
- [x] **Unit** tests for Task description, picker eligibility, delete→unschedule, save-vs-apply separation
- [x] **Integration** tests for Task CRUD + call-list HTTP/API + persist round-trip
- [x] **System** test: HA + App path save schedule, reload App, then Apply; tank under Main (or equivalent) runs when applied

## Work packages
1. **Schema + persist/apply split** — Done (SWD-196)
2. **Task editor API** — Done (SWD-199)
3. **App UI** — Done (SWD-200)
4. **Wire Program cards** — Done (SWD-197)
5. **Tests** — Done (SWD-198)

## Shipped
- App **0.1.34**
- Task editor + Save/Apply split; live Skid loader sync on Apply
- PR [#78](https://github.com/marcuskrogh/PLCAssistant/pull/78)

## Tracker
- Provider: jira
- Story: [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)
- Task: [SWD-191](https://marcusknielsen.atlassian.net/browse/SWD-191)
- Sub-tasks: SWD-196, SWD-199, SWD-200, SWD-197, SWD-198 (Done)
- Branch: `cursor/swd-191-task-scheduling-editor-a52c`
- PR: [#78](https://github.com/marcuskrogh/PLCAssistant/pull/78)

## Next
Done — phase closed.
