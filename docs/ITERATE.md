# Iterate: PID card compact redesign (2dp, single-row KPIs, more-info popup)

## Prior work
- Task: [SWD-227](https://marcusknielsen.atlassian.net/browse/SWD-227)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/90 (App 0.1.47)
- Spec context: docs/ITERATE.md (prior), SWD-226 climate-style faceplate

## Problem
Direction of the climate-inspired PID faceplate is good, but operators still need a tighter HMI:

1. **Precision** — values show more than two decimal places; unnecessary for now.
2. **Mobile KPIs** — PV / Active SP / CV wrap to two rows on narrow viewports; all three must stay on one row.
3. **Compact + popup** — the card is too tall with inline editors; clicking the card should open a popup (like the native climate card) where mode and SP values can be changed.
4. **Design pass** — overall look should be more compact, sleek, user-friendly, and modern.

## Clarifications
- Invoke was rich; no further clarifying questions.
- Keep existing Set/mode float contracts (SWD-227) and draft-edit behaviour (SWD-226) inside the popup editors.

## Acceptance criteria
- [x] Displayed PV, Active SP, CV, and error use **two decimal places**
- [x] On mobile (narrow) widths, all three KPIs remain in a **single row** (no wrap to two rows)
- [x] Faceplate is **compact** (no inline Man/Auto/Rem SP editors on the card body)
- [x] **Clicking the card** opens a popup/dialog to change mode and SP values (climate-card-like)
- [x] Overall visual pass: compact, sleek, modern; mode accent retained
- [x] Prior float/Set contracts preserved (`button[data-mode]`, `number.set_value` finite floats)
- [x] App/integration **0.1.48**; dashboard **27**; dual trees synced; tests green

## Out of scope
- Classic output Manual (CV override)
- Changing Soft-PLC / Datablock semantics
- Non-PID specialised cards

## Work packages
1. Compact faceplate layout + 2dp formatting + single-row KPIs
2. More-info / popup editors for mode + SP (reuse draft/Set contracts)
3. Version bump, dual-tree sync, acceptance + contract tests

## Tracker
- Task: [SWD-228](https://marcusknielsen.atlassian.net/browse/SWD-228)
- Relates: SWD-227
- Branch: `cursor/swd-228-pid-card-compact-33f6`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/91
- App: **0.1.48** / dashboard **27**

## Next
`/review-fix SWD-228` — Review and auto-fix until clean
