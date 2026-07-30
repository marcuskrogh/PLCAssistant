# PLCAssistant thin integration (bundled)

Home Assistant custom component that owns:

- Entity ↔ Soft-PLC tag **bindings**
- **Mock / plant IN** entities — Operate **Sensors** for live plant PVs (SWD-170) plus writable Numbers for request SPs and plant nudges (SWD-146/169) — and read-only Sensors for Soft-PLC OUT
- Operator **button** entities and services for **start / stop / reset** (MQTT cmd topics)
- Default **Lovelace** dashboard registered in the **HA sidebar** (`lovelace_dashboard.py`)

Default mock bindings (wedge process I/O):

| Tag | Direction | HA entity | Role |
|-----|-----------|-----------|------|
| `SP_LEVEL_REQ` | IN | `number.plcassistant_sp_level_req` | Level setpoint **request** (writable) |
| `LT_TANK` | IN | `sensor.plcassistant_lt_tank_in` (+ `number.*` nudge) | Tank level (plant → Soft-PLC) |
| `LT_RES` | IN | `sensor.plcassistant_lt_res_in` (+ `number.*` nudge) | Reservoir level (plant → Soft-PLC) |
| `FT_INLET` | IN | `sensor.plcassistant_ft_inlet_in` (+ `number.*` nudge) | Inlet flow (plant → Soft-PLC) |
| `CMD_SPEED` | OUT | `sensor.plcassistant_cmd_speed` | Pump speed command |
| `SP_LEVEL` | OUT | `sensor.plcassistant_sp_level` | Active level setpoint |
| `SP_FLOW` | OUT | `sensor.plcassistant_sp_flow` | Active flow setpoint |
| `MODE` | OUT | `sensor.plcassistant_mode` | `STOP` / `RUNNING` / `TRIPPED` |
| `PERM_OK` | OUT | `sensor.plcassistant_perm_ok` | Start ready when idle (`on`/`off`; Off while RUNNING expected) |
| `TRIP_ACTIVE` | OUT | `sensor.plcassistant_trip_active` | Latched trip (`on`/`off`) |
| *(App status)* | — | `sensor.plcassistant_status` | Soft-PLC scan: `running` / `stopped` / `fault` / `offline` (+ `scan_period_s` on MQTT) |

Talks to the Soft-PLC **App** over MQTT (`dependencies: ["mqtt", "frontend", "lovelace"]`). Full install steps: [`README.md`](../../README.md). Packaging contract: [`docs/packaging/`](../../docs/packaging/README.md).

**Ownership (SWD-145/146/169/170):** Soft-PLC is mock-unaware. Process ↔ Soft-PLC I/O is MQTT. The stand-alone process simulator lives in this integration and publishes plant IN; Operate Process uses plant **sensors** hydrated from the simulator (`in_values` cache + bus) so levels/flows stay readable.

**Version:** always matches the PLCAssistant App (`plc_assistant/config.yaml` ↔ this `manifest.json`).

**Install (HA OS):** starting the PLCAssistant App copies this folder into
`/config/custom_components/plcassistant/`. Restart Core once, then add the
integration under Devices & services. After a later App Update (once
**0.1.27+** is already loaded), if Core has not yet reloaded, Settings →
System → Updates shows **Restart of Home Assistant required** on the
PLCAssistant update card. The integration installs
`/config/dashboards/plcassistant.yaml` (if missing) and adds
**PLCAssistant** to the sidebar — no paste step.
