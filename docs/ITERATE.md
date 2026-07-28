# Iterate: Block Editor Ingress 404 + thin integration value / version lock

## Status
**In Review** — App **0.1.9** via [PR #43](https://github.com/marcuskrogh/PLCAssistant/pull/43)

## Prior work
- Task: SWD-130 (PR #42, App 0.1.8 store Latest / `#main`)
- Spec context: `docs/packaging/01-shape.md`, `docs/packaging/04-updates.md`, `docs/wedge/02-io-hmi-contract.md`, `docs/io/03-thin-integration-stub.md`

## Problem
After SWD-130 / App **0.1.8** on HA OS:

1. **Block Editor empty + `Error: 404: Not Found`** (top-right) when opened via HA Ingress. Absolute `fetch('/api/...')` hits Home Assistant Core’s `/api/...` instead of the App under the ingress prefix. Library and program panes stay empty.
2. **App and thin integration should share one version.** Separate versioning is confusing; operator reports the integration only loads properly at **0.1.1**. `plc_assistant/config.yaml` and both `custom_components/plcassistant/manifest.json` copies must always match.
3. **Thin integration has little visible value.** Mock mode only exposes `LT_TANK` IN and `CMD_Speed` OUT. No flow (`FT_INLET`), no other wedge PVs/setpoints, and Start/Stop/Reset are services-only (no button entities).

## Acceptance criteria
1. Canvas API calls use **relative** paths so Ingress and host-port **8099** both load library + program (no 404 status banner).
2. App `version` and integration `manifest.json` `version` are **identical**; CI/tests enforce the lock; bump both to **0.1.9**.
3. Default mock bindings cover wedge process I/O including **`FT_INLET` (flow)**, `LT_TANK`, `LT_RES`, and useful setpoints/outputs (`SP_LEVEL_REQ`, `SP_LEVEL`, `SP_FLOW`, `CMD_SPEED`). Start/Stop/Reset exposed as HA **button** entities.
4. Docs note shared versioning and expanded mock entities.

## Out of scope
- Full Lovelace dashboard packaging
- Binding UI / reconfigure flow for custom entity maps
- Fixing HA Core Ingress itself

## Work packages
1. Ingress-safe relative API base in canvas JS + regression test
2. Expand default wedge bindings (incl. flow) + button platform; sync App `default_wedge_binding_config`
3. Version lock 0.1.9 + tests/docs

## Tracker
- Task: [SWD-131](https://marcusknielsen.atlassian.net/browse/SWD-131)
- Relates: SWD-130
- Branch: `cursor/swd-131-ingress-integration-1bbe`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/43

## Next
`/review-fix SWD-131` — Review and auto-fix until clean
