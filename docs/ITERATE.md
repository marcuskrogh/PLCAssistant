# Iterate: Lovelace HMI + Soft-PLC plant on Start

## Status
**Done** — App **0.1.11** shipped via [PR #46](https://github.com/marcuskrogh/PLCAssistant/pull/46)

## Prior work
- Task: SWD-132 (PR #44, App 0.1.10 App operator dashboard — wrong HMI home)
- Spec: `docs/wedge/02-io-hmi-contract.md`, `docs/packaging/01-shape.md`

## Problem
After 0.1.10:

1. Start looks idle — App demo scan is not wedge cascade + plant; `SP_FLOW`/`CMD_SPEED` stay 0.
2. Setpoints appear uneditable — HA Numbers for Soft-PLC **OUT** tags; writable request is `SP_LEVEL_REQ`.
3. Operator wanted **Lovelace** as HMI/SCADA, not an App-owned dashboard; App should be the program editor.

## Acceptance criteria
1. App Ingress default is the **Program / block editor** (no Soft-PLC operator SCADA as primary).
2. Thin integration ships a **default Lovelace dashboard** YAML under `lovelace/`; App copies it to HA `dashboards/plcassistant.yaml` with a short README.
3. Writable setpoint is `number.plcassistant_sp_level_req`; Soft-PLC-owned tags are **sensors**.
4. Mock Soft-PLC plant + Start moves process (`SP_FLOW` / `CMD_SPEED` / tank) via `SkidImageLogic`.
5. App + integration version **0.1.11**.

## Out of scope
- Full auto-registration of Lovelace into HA storage UI (paste/import documented)
- Field (non-mock) sensor binding UI

## Next
`/iterate` — next operator feedback

## Tracker
- Task: [SWD-133](https://marcusknielsen.atlassian.net/browse/SWD-133)
- Relates: SWD-132
- Branch: `cursor/swd-133-lovelace-hmi-plant-1bbe`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/46
