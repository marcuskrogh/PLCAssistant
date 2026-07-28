# PLCAssistant thin integration (bundled)

Home Assistant custom component that owns:

- Entity ↔ Soft-PLC tag **bindings**
- **Mock / sim** entities (writable Number IN + Number OUT; mock path ≡ field path)
- Operator **button** entities and services for **start / stop / reset** (MQTT cmd topics)

Default mock bindings (wedge process I/O):

| Tag | Direction | Role |
|-----|-----------|------|
| `LT_TANK` | IN | Tank level |
| `LT_RES` | IN | Reservoir level |
| `FT_INLET` | IN | Inlet flow |
| `SP_LEVEL_REQ` | IN | Level setpoint request |
| `CMD_SPEED` | OUT | Pump speed command |
| `SP_LEVEL` | OUT | Active level setpoint |
| `SP_FLOW` | OUT | Active flow setpoint |

Talks to the Soft-PLC **App** over MQTT (`dependencies: ["mqtt"]`). Full install steps: [`README.md`](../../README.md). Packaging contract: [`docs/packaging/`](../../docs/packaging/README.md).

**Version:** always matches the PLCAssistant App (`plc_assistant/config.yaml` ↔ this `manifest.json`).

**Install (HA OS):** starting the PLCAssistant App copies this folder into
`/config/custom_components/plcassistant/`. Restart Core once, then add the
integration under Devices & services.
