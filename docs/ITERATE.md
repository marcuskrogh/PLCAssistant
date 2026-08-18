# Iterate: PID faceplate settings fields reset while editing

## Prior work
- Task: [SWD-373](https://marcusknielsen.atlassian.net/browse/SWD-373)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/105 (App 0.1.64)
- Spec context: docs/PLAN.md, docs/io/06-pid-faceplate.md, SWD-226 dirty-draft SP editors

## Problem
- Controller **settings** fields (Gains / Structure / Output / Filter / Ramp) reset to the live current value more than once per second while the operator is typing, so Apply cannot keep the intended values.
- Analog SP/MV popup editors already keep dirty drafts across hass updates (SWD-226). Settings `data-tune` fields only skipped a rewrite when `document.activeElement` was that input, which fails in Lovelace shadow DOM and restomps every other field as soon as focus leaves it.

## Clarifications
- Scope is **settings dialog fields only** — analog popup SP/MV editors stay as they are.
- While the settings dialog is open, the form is a draft until Apply or Cancel/Escape. Reopening loads live params.

## Acceptance criteria
- [x] Live hass / `applyPidFaceplateState` paints do not rewrite settings fields while the settings dialog is open
- [x] Typed or toggled settings drafts survive focus movement and incomplete text such as `0.`
- [x] Apply still commits current field values; Cancel / Escape / close discards the draft so the next open shows live params
- [x] Analog popup editors are unchanged
- [x] Regression tests cover freeze-while-open plus `data-dirty` drafts
- [x] Dual-tree sync + App **0.1.65** (Lovelace `?v=` cache-bust)

## Out of scope
- Changing PID parameter semantics or which keys appear in settings
- Reworking analog popup draft handling
- ISA-101 / chrome layout changes

## Work packages
1. Freeze `data-tune` paints while the settings dialog is shown (`pid-faceplate-elements.js`)
2. Lovelace card snapshots / restores settings drafts across hass (same pattern as SP dirty drafts)
3. Tests, docs, dual-tree, App 0.1.65

## Tracker
- Task: [SWD-382](https://marcusknielsen.atlassian.net/browse/SWD-382)
- Relates: SWD-373
- Branch: `cursor/swd-382-pid-settings-drafts`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/106
- App: **0.1.65**

## Next
`/review-fix SWD-382` — Review and auto-fix (single pass)
