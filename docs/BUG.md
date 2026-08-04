# Bug: One-tank Diagram empty; mobile cannot place blocks

## Summary
- Soft-PLC App **Programs → Diagram** for the example one-tank system opens with an empty canvas.
- Live tags (e.g. `LEVEL_*`, `FLOW_*`) are visible, but **PROGRAM JSON** has empty `instances` / `wires` / `execution_order`.
- Blocks have never appeared on this install; desktop drag from Block Library does place blocks, so canvas rendering works when instances exist.
- On mobile, blocks cannot be placed (no drag).

## Repro
1. Open PLCAssistant in the current HA install.
2. Open the one-tank example program **main** → **Diagram**.
3. Observe empty grid; side panel shows tags; PROGRAM JSON shows `"instances": {}`.
4. On desktop: drag **PID** from Block Library → block appears.
5. On mobile: attempt to place a block from the library → cannot (drag unavailable).

## Expected
- Seeded / applied / running programs show their block instances (and wires) on the Diagram — including PID blocks for the one-tank example — without manual placement.
- Mobile users can place a library block onto the Diagram without desktop drag.

## Actual
- One-tank Diagram is empty and has never shown blocks; program instances are empty while tags exist.
- Mobile placement is not possible.

## Impact
- Cannot inspect or edit the example (or any similarly empty) program logic on the Diagram.
- Mobile engineering is blocked for adding blocks.

## Suspected area
- Example / tank program seed or load path that should populate `instances` (and layout) for the Diagram — prior related fix **SWD-237**.
- App Diagram UI: mobile place gesture or tap-to-place for library blocks.
- Not a canvas paint-only bug if JSON already has no instances.

## Acceptance criteria
- Opening the one-tank example **Diagram** shows the program’s blocks (including PIDs) and wires consistent with a proper seeded/running program.
- A program that has instances in the engineering model is not shown as an empty Diagram.
- On mobile, a user can add a block from the Block Library onto the Diagram without desktop drag.
- Desktop drag-from-library placement continues to work.

## Out of scope
- **+ Program Block** / custom block definition editor (no-op when fields are empty is acceptable for this bug).
- Unrelated Lovelace PID card / HMI issues.
- Broader library labeling or code-editor formatting (covered previously under SWD-237).

## Work packages
1. Seed/load: ensure one-tank (and running) programs expose block instances + layout to the Diagram.
2. Mobile: add a non-drag way to place a library block on the Diagram.
3. Regression coverage for empty-vs-seeded diagram and mobile place path where testable.

## Tracker
- Task: [SWD-249](https://marcusknielsen.atlassian.net/browse/SWD-249)
- Sub-tasks: _(none)_
- Branch: `cursor/swd-249-empty-diagram-1e05`
- PR: _(draft — pending)_
- Relates: [SWD-237](https://marcusknielsen.atlassian.net/browse/SWD-237)

## Next
`/implement SWD-249` — Fix per BUG.md (same branch/PR)
