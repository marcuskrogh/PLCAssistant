# PLCAssistant thin integration (bundled)

Home Assistant custom component that owns:

- Entity ↔ Soft-PLC tag **bindings**
- **Mock / sim** entities (writable Number for request SPs; read-only Sensors for Soft-PLC OUT)
- Operator **button** entities and services for **start / stop / reset** (MQTT cmd topics)
- Default **Lovelace** dashboard template (`lovelace/plcassistant.yaml`)

Default mock bindings (wedge process I/O):

| Tag | Direction | HA entity | Role |
|-----|-----------|-----------|------|
| `SP_LEVEL_REQ` | IN | `number.plcassistant_sp_level_req` | Level setpoint **request** (writable) |
| `LT_TANK` | OUT | `sensor.plcassistant_lt_tank` | Tank level (Soft-PLC plant) |
| `LT_RES` | OUT | `sensor.plcassistant_lt_res` | Reservoir level |
| `FT_INLET` | OUT | `sensor.plcassistant_ft_inlet` | Inlet flow |
| `CMD_SPEED` | OUT | `sensor.plcassistant_cmd_speed` | Pump speed command |
| `SP_LEVEL` | OUT | `sensor.plcassistant_sp_level` | Active level setpoint |
| `SP_FLOW` | OUT | `sensor.plcassistant_sp_flow` | Active flow setpoint |

Talks to the Soft-PLC **App** over MQTT (`dependencies: ["mqtt"]`). Full install steps: [`README.md`](../../README.md). Packaging contract: [`docs/packaging/`](../../docs/packaging/README.md).

**Version:** always matches the PLCAssistant App (`plc_assistant/config.yaml` ↔ this `manifest.json`).

**Install (HA OS):** starting the PLCAssistant App copies this folder into
`/config/custom_components/plcassistant/` and refreshes
`/config/dashboards/plcassistant.yaml`. Restart Core once, then add the
integration under Devices & services, then add the Lovelace board (see
`dashboards/plcassistant_README.md`).
