# PLCAssistant Lovelace dashboard

Bundled template (`plcassistant.yaml`) is the default Soft-PLC HMI.

## Sidebar (automatic)

When the PLCAssistant integration loads, it:

1. Installs this YAML under `/config/dashboards/plcassistant.yaml` if missing
   (or refreshes a **stock** board that still lacks the status card, or is
   explicitly on `plcassistant_dashboard_version` 1/2)
2. Registers a Lovelace panel **PLCAssistant** at `/plcassistant-skid` with
   **Show in sidebar** enabled

After **App Update → restart Home Assistant Core → add/reload PLCAssistant**,
open **PLCAssistant** in the sidebar. No copy/paste step.

You can still create additional Lovelace dashboards in HA and reuse these
entities for your own SCADA boards. Fully custom YAML under
`dashboards/plcassistant.yaml` is left alone; stock boards missing
`sensor.plcassistant_status`, or still marked version 1/2, are refreshed on
update so the status card and offline help appear.

## Status (top of board)

| Entity | Values |
|--------|--------|
| `sensor.plcassistant_status` | `running` / `stopped` / `fault` / `offline` (App scan) |
| `sensor.plcassistant_mode` | `STOP` / `RUNNING` / `TRIPPED` (skid MODE) |
| `sensor.plcassistant_perm_ok` | `on` / `off` (Start permissive when idle) |
| `sensor.plcassistant_trip_active` | `on` / `off` |

Press **Start** → Soft-PLC status `running`, MODE `RUNNING`, and process sensors move.

## Writable vs read-only

| Entity | Role |
|--------|------|
| `number.plcassistant_sp_level_req` | Operator **level setpoint request** (writable) |
| `button.plcassistant_start` / `_stop` / `_reset` | Operator commands |
| `sensor.plcassistant_*` | Soft-PLC-owned PVs, active SPs, and status (read-only) |

## Upgrading from App 0.1.10

Entity IDs changed in **0.1.11** (OUT tags became sensors; setpoint request renamed):

| 0.1.10 | 0.1.11+ |
|--------|---------|
| `number.plcassistant_sp_level_req_in` | `number.plcassistant_sp_level_req` |
| `number.plcassistant_lt_tank_in` (mock plant IN) | `sensor.plcassistant_lt_tank` (Soft-PLC plant OUT) |
| `number.plcassistant_*_out` | `sensor.plcassistant_*` |

After App Update + Core restart: remove the old PLCAssistant integration entry (or delete stale unavailable entities in the entity registry), then add the integration again so entity IDs match. Update any personal dashboards/automations that referenced the old `*_in` / `*_out` Numbers.
