# Iterate: PID cards Lovelace typography + 2dp everywhere

## Prior work
- Task: [SWD-229](https://marcusknielsen.atlassian.net/browse/SWD-229) (Operate SCADA declutter)
- Also: [SWD-228](https://marcusknielsen.atlassian.net/browse/SWD-228) (compact PID faceplate / 2dp KPIs)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/92 (App 0.1.49)
- Spec context: docs/ITERATE.md (prior), custom_components/.../www/pid-loop-card.js

## Problem
After 0.1.49 the PID faceplates still feel foreign next to stock Lovelace cards, and some numeric values still show excessive decimal places:

1. **Typography** — custom rem sizes + Segoe UI / Roboto fallback do not match surrounding entities / glance cards (HA body / header tokens).
2. **Decimals** — faceplate KPIs, dialog summary, error line, and committed SP editor text must always show exactly two decimal places; compound PID attributes still publish raw float noise into more-info.

## Clarifications
- Invoke was rich; no further clarifying questions.
- Scope is the PID card (+ compound PID attribute rounding that feeds it). Operate Process glance may get `suggested_display_precision: 2` so adjacent values match.
- "Truncate to two decimals" means display with two fractional digits (`toFixed(2)` / round-half-away display), not a new control algorithm.

## Acceptance criteria
- [ ] PID card uses Home Assistant design tokens for font family and text sizes (title / labels / values / controls), so it reads as a native Lovelace card beside entities/glance
- [ ] Every numeric value rendered on the PID card (PV, Active SP, CV, err, Man/Auto/Rem committed inputs) is formatted to exactly two decimal places
- [ ] Compound PID sensor attributes (`pv`, `sp`, `sp_*`, `cv`, `kp`, `ki`, `kd`) are rounded to 2dp when published
- [ ] App/integration **0.1.50**; dual trees synced; JS + Python regression tests green

## Out of scope
- Changing Soft-PLC / PID control semantics or mode logic
- New SCADA graphics
- Classic output Manual (CV override)
- Operate layout / declutter changes beyond display precision on Process PVs

## Work packages
1. PID card CSS → HA font tokens; harden 2dp formatting paths
2. Round compound PID attributes in `pid_loop.py`; optional Process sensor display precision
3. Version bump 0.1.50 + dual-tree sync + acceptance tests

## Tracker
- Task: [SWD-230](https://marcusknielsen.atlassian.net/browse/SWD-230)
- Relates: SWD-229
- Branch: `cursor/swd-230-pid-card-lovelace-fonts-04d5`
- App: **0.1.50**

## Next
`/review-fix SWD-230` — Review and auto-fix until clean
