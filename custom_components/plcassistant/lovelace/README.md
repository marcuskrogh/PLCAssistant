# PLCAssistant Lovelace dashboard

The App copies `dashboards/plcassistant.yaml` into this Home Assistant config
folder on start (when missing or older than the bundled file).

## Open the board

1. Restart Home Assistant Core after the App updates the thin integration.
2. Add / reconfigure the **PLCAssistant** integration (Devices & services) if needed.
3. **Settings → Dashboards → Add dashboard**
4. Choose **New dashboard from scratch**, open the raw configuration editor, and
   paste the contents of `dashboards/plcassistant.yaml` — or add a YAML-mode
   dashboard that includes that file if your HA setup uses YAML dashboards.

You can also duplicate the view into any existing Lovelace dashboard and extend
it (extra cards, other entities) — that is the intended SCADA path. The Soft-PLC
App Ingress is the **block / program editor**, not the operator HMI.

## Writable vs read-only

| Entity | Role |
|--------|------|
| `number.plcassistant_sp_level_req` | Operator **level setpoint request** (writable) |
| `button.plcassistant_start` / `_stop` / `_reset` | Operator commands |
| `sensor.plcassistant_*` | Soft-PLC-owned PVs and active SPs (read-only) |

## Upgrading from App 0.1.10

Entity IDs changed in **0.1.11** (OUT tags became sensors; setpoint request renamed):

| 0.1.10 | 0.1.11 |
|--------|--------|
| `number.plcassistant_sp_level_req_in` | `number.plcassistant_sp_level_req` |
| `number.plcassistant_lt_tank_in` (mock plant IN) | `sensor.plcassistant_lt_tank` (Soft-PLC plant OUT) |
| `number.plcassistant_*_out` | `sensor.plcassistant_*` |

After App Update + Core restart: remove the old PLCAssistant integration entry (or delete stale unavailable entities in the entity registry), then add the integration again so Lovelace IDs match. Update any personal dashboards/automations that referenced the old `*_in` / `*_out` Numbers.
