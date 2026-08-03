# Bug: App UI — cards, diagram, place, built-in labels, code formatting

## Summary
- Soft-PLC App engineering surface: overview cards require a dedicated button; tank/test program diagram shows no blocks; placing blocks fails; library says “Shipped” instead of built-in with **name (description)**; library code/definition editor formatting is nearly unreadable.
- One Bug Task / one delivery PR for all fixes.

## Repro
1. Overview → Programs or Tasks: open via the action button only (card body is not clickable).
2. Open the tank (test example) program Diagram: canvas is empty (blocks not shown).
3. Drag/place a library block onto the diagram: placement does not work.
4. Library: built-in blocks labeled “Shipped …” (e.g. “Shipped PID”).
5. Open a block definition: equation / JSON / code is poorly formatted and hard to read.

## Expected
- Clicking a program or task **card** navigates the same as today’s primary action.
- Tank/test program diagram renders existing blocks (and wires).
- Placing blocks from the library onto the diagram succeeds.
- Built-in copy uses **built-in**; referrals use **name (description)** (not “Shipped PID”).
- Library code/definition surfaces: readable **monospace layout and indentation** only.

## Actual
- Cards require a specific button.
- Diagram empty for the main/test program.
- Adding blocks does not work.
- “Shipped” labeling.
- Janky, nearly unreadable formatting in the code/definition editor.

## Impact
- Core App engineering UX: cannot reliably view or edit the sample program diagram; library labeling and editors mislead or frustrate authors.

## Suspected area
- `plcassistant/app/_canvas.py` — overview cards (`loadPrograms` / `loadTasks`), diagram `render` / `place`, library “Shipped” copy, `#lib-body` / equation editors.
- `plcassistant/app/server.py` — `/api/program`, `/api/place`, library APIs.
- `plcassistant/surface/schema.py` / `builtin.py` — place + tank seed layout (blocks may lack usable canvas positions).

## Acceptance criteria
- [ ] Program and task cards are clickable end-to-end (same destinations as current actions).
- [ ] Tank/test program diagram renders existing blocks.
- [ ] Library place/add onto the diagram works.
- [ ] “Shipped” replaced by built-in; referrals use name (description).
- [ ] Equation/JSON/code editors: readable monospace + indentation (no syntax highlighting / structural redesign).

## Out of scope
- Syntax highlighting
- Broader editor UX redesign / clearer field-structure overhaul
- Unrelated feature work

## Work packages
1. Overview: make program and task cards clickable
2. Diagram: render tank/test blocks; fix place/add from library
3. Library: built-in labeling + name (description)
4. Library editors: monospace layout + indentation readability

## Tracker
- Task: [SWD-237](https://marcusknielsen.atlassian.net/browse/SWD-237)
- Sub-tasks: _(none — single PR)_
- Branch: `cursor/swd-237-app-ui-bugs-2b92`
- PR: _(pending)_

## Next
`/implement SWD-237` — Fix per BUG.md (same branch/PR)
