# Iterate: PID card Set SP fails — expected float (data-mode click hijack)

## Prior work
- Task: [SWD-226](https://marcusknielsen.atlassian.net/browse/SWD-226)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/89 (App 0.1.46)
- Spec context: screenshot — Set Man SP 0.3 → toast `expected float`; Active SP stays 0.200

## Problem
Setting SP from the climate-style PID card fails with
`Failed to perform the action number/set_value. expected float for dictionary value @ data['value']`.

Root cause: card root used `data-mode="man|auto|rem"` for accent styling; click
handler used `closest("[data-mode]")`, so Set clicks matched the card root,
called `_setMode("man")` → `Number("man")` is NaN, and `_applySp` never ran.

## Acceptance criteria
- [x] Set / Enter commits SP as a finite float via `number.set_value`
- [x] Mode buttons still switch via codes 0/1/2 only (`button[data-mode]`)
- [x] Card accent uses `data-pid-mode` (not conflicting with mode buttons)
- [x] App/integration **0.1.47**; dashboard **26**; dual trees; tests green
- [x] **Regression tests** for integration ↔ HMI communication:
  - Node contract (`tests/js/pid_faceplate_contract.test.mjs`): Set under ancestor
    `data-mode` resolves to **apply** (not mode); `numberServiceValue("man")` is
    null; finite floats build `{ value: <number> }` for `number.set_value`
  - Pytest wraps the Node harness + asserts faceplate entity ids / float flip codes

## Out of scope
- Further visual redesign
- Classic output Manual

## Tracker
- Task: [SWD-227](https://marcusknielsen.atlassian.net/browse/SWD-227)
- Relates: SWD-226
- Branch: `cursor/swd-227-pid-card-set-float-5ef6`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/90

## Fix-forward (open PR)
User asked to require tests so incorrect HMI ↔ integration communication cannot
ship again. Implemented on the same open PR #90 (not a parallel iterate Task).

## Next
`/review-fix SWD-227` — Review and auto-fix until clean
