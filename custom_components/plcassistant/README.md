# PLCAssistant thin integration (bundled)

Home Assistant custom component that owns:

- Entity ↔ Soft-PLC tag **bindings**
- **Mock / sim** entities (writable Number IN + Number OUT; mock path ≡ field path)
- Operator services **start / stop / reset** (MQTT cmd topics)

Talks to the Soft-PLC **App** over MQTT (`dependencies: ["mqtt"]`). See [`docs/packaging/`](../../docs/packaging/README.md) and [`ha_app/INSTALL.md`](../../ha_app/INSTALL.md).

**Install (v1):** copy this folder to `/config/custom_components/plcassistant/` then restart Core.
