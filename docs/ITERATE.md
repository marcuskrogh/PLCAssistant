# Iterate: Lovelace Operate SCADA-style declutter

## Prior work
- Task: [SWD-228](https://marcusknielsen.atlassian.net/browse/SWD-228)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/91 (App 0.1.48)
- Spec context: docs/ITERATE.md (prior PID compact), lovelace/plcassistant.yaml Operate view

## Problem
The Operate dashboard is an entity dump, not a SCADA screen:

1. **Clutter** — changelog markdown, block-list card, PID fallback entity rows, duplicate SP / active-SP cards, and an always-on history graph show nearly every exposed tag.
2. **Wrong job** — operators need relevant process values, PID faceplates, and clear Start / Stop / Reset / Mode controls — not a browser of every entity.
3. **History** — important values should open HA more-info (history) on click, not force a permanent graph.

## Clarifications
- Invoke was rich; no further clarifying questions.
- Skid **Mode** means `sensor.plcassistant_mode` (`STOP` / `RUNNING` / `TRIPPED`), shown with command buttons.
- Dynamics / Datablocks engineering tabs stay; declutter is Operate-only.
- PID cards remain the SP / mode editors (tap popup from SWD-228).

## Acceptance criteria
- [x] Operate view is a compact SCADA layout: Soft-PLC status, Mode, Trip, Start / Stop / Reset, key PVs, Level + Flow PID cards
- [x] No changelog markdown wall, block-list card, PID fallback entity dump, duplicate SP / active-SP entities cards, or always-on history-graph on Operate
- [x] Key process values (tank / reservoir / inlet flow / pump speed) are shown; clicking opens more-info / history
- [x] Dynamics and Datablocks tabs retained
- [x] Stock dashboard upgrade includes version **27** → **28**; App/integration **0.1.49**; dual trees synced; tests green

## Out of scope
- New custom SCADA graphics / P&ID drawing canvas
- Changing Soft-PLC / Datablock / PID semantics
- Removing Dynamics / Datablocks engineering surfaces
- Classic output Manual (CV override)

## Work packages
1. Rewrite Operate Lovelace YAML as SCADA HMI + README
2. Bump dashboard upgrade path (27→28) + App 0.1.49 + dual-tree sync
3. Acceptance / regression tests for declutter contract

## Tracker
- Task: [SWD-229](https://marcusknielsen.atlassian.net/browse/SWD-229)
- Relates: SWD-228
- Branch: `cursor/swd-229-lovelace-scada-declutter-566c`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/92
- App: **0.1.49** / dashboard **28**

## Next
`/review-fix SWD-229` — Review and auto-fix until clean
