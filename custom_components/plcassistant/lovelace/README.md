# PLCAssistant Lovelace dashboard

Bundled template (`plcassistant.yaml`) is the default Soft-PLC HMI.

## Sidebar (automatic)

When the PLCAssistant integration loads, it:

1. Installs this YAML under `/config/dashboards/plcassistant.yaml` if missing
   (or refreshes a **stock** board that still lacks the status card, or is
   explicitly on an older `plcassistant_dashboard_version`)
2. Registers a Lovelace panel **PLCAssistant** at `/plcassistant-skid` with
   **Show in sidebar** enabled

After **App Update → restart Home Assistant Core → add/reload PLCAssistant**,
open **PLCAssistant** in the sidebar. No copy/paste step.

You can still create additional Lovelace dashboards in HA and reuse these
entities for your own SCADA boards. Fully custom YAML under
`dashboards/plcassistant.yaml` is left alone; stock boards missing
`sensor.plcassistant_status`, or still marked on an older stock version, are
refreshed on update so the status card and help appear.

## Status (top of board)

| Entity | Values |
|--------|--------|
| `sensor.plcassistant_status` | `running` / `stopped` / `fault` / `offline` (App scan) |
| `sensor.plcassistant_mode` | `STOP` / `RUNNING` / `TRIPPED` (skid MODE) |
| `sensor.plcassistant_perm_ok` | `on` / `off` (Start ready when idle; Off while RUNNING is expected) |
| `sensor.plcassistant_trip_active` | `on` / `off` |

Press **Start** → Soft-PLC status `running`, MODE `RUNNING`, and Soft-PLC CVs
(`CMD_SPEED`, active SPs) update. Plant level/flow Numbers are Soft-PLC **IN**
from the integration simulator (SWD-146+); they show as **box** numbers with
live values (SWD-169).

## Writable vs read-only

| Entity | Role |
|--------|------|
| `number.plcassistant_sp_level_req` | Operator **level setpoint request** (writable) |
| `number.plcassistant_lt_tank_in` / `_lt_res_in` / `_ft_inlet_in` | Plant PVs as Soft-PLC **IN** (live simulator display + nudge) |
| `button.plcassistant_start` / `_stop` / `_reset` | Operator commands |
| `sensor.plcassistant_*` | Soft-PLC OUT (CVs, active SPs, MODE / status) — read-only |

## Upgrading from App 0.1.10 / 0.1.19

Entity IDs changed in **0.1.11** (OUT tags became sensors; setpoint request renamed)
and again in **0.1.20** (plant PVs flipped back to Soft-PLC IN Numbers):

| Era | Plant tags |
|-----|------------|
| 0.1.10 | `number.plcassistant_lt_tank_in` (early mock IN) |
| 0.1.11–0.1.19 | `sensor.plcassistant_lt_tank` (Soft-PLC plant OUT) |
| **0.1.20+** | `number.plcassistant_lt_tank_in` (Soft-PLC plant IN; live from SWD-146) |

After App Update + Core restart: remove the old PLCAssistant integration entry (or delete stale unavailable entities in the entity registry), then add the integration again so entity IDs match. Update any personal dashboards/automations that referenced the old plant sensors.
