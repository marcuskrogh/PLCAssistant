# Iterate: Operator dashboard default + major App UI refresh

## Status
**Done** — App **0.1.10** shipped via [PR #44](https://github.com/marcuskrogh/PLCAssistant/pull/44)

## Prior work
- Task: SWD-131 (PR #43, App 0.1.9 Ingress + thin-integration tags)
- Spec context: `docs/wedge/02-io-hmi-contract.md`, `docs/surface/05-app-editor.md`, `plcassistant/app/`

## Problem
After SWD-131 the Soft-PLC runs, but the App UI is still a crude Block Editor-only surface:

1. No default **operator dashboard** with live process signals.
2. Start / Stop / Reset and run-state are unclear.
3. Visual design is poor on desktop and especially **mobile**.

## Acceptance criteria
1. Default App view is an **operator dashboard** showing live wedge signals (LT_TANK, LT_RES, FT_INLET, CMD_SPEED, SP_LEVEL / SP_FLOW at minimum) with quality/run indication.
2. Prominent **Start / Stop / Reset** and clear **running / stopped / offline** status
   (offline = no MQTT scan attached — never claim an active scan when `mqtt: false`;
   scan faults publish on the MQTT status topic separately from the dashboard chip).
3. Block / program editor remains a secondary view.
4. Large visual refresh: modern layout, expressive typography, atmospheric background, mobile-usable nav + visualisations; Ingress-relative API paths preserved.
5. App + integration version **0.1.10** (locked equal).

## Out of scope
- Lovelace packaging
- Binding reconfigure UI
- Full Soft-PLC ladder redesign beyond operator surface

## Work packages
1. `/api/runtime` + `/api/cmd` wired to scan loop / fallback image
2. Dashboard-default UI + secondary Program editor; mobile layout
3. Version bump 0.1.10 + tests

## Tracker
- Task: [SWD-132](https://marcusknielsen.atlassian.net/browse/SWD-132)
- Relates: SWD-131
- Branch: `cursor/swd-132-operator-dashboard-ui-1bbe`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/44

## Next
`/iterate` — next operator feedback
