# PLCAssistant thin integration (bundled)

Home Assistant custom component that owns:

- Entity ↔ Soft-PLC tag **bindings**
- **Mock / sim** entities (writable Number IN + Number OUT; mock path ≡ field path)
- Operator services **start / stop / reset** (MQTT cmd topics)

Talks to the Soft-PLC **App** over MQTT (`dependencies: ["mqtt"]`). Full install steps: [`README.md`](../../README.md). Packaging contract: [`docs/packaging/`](../../docs/packaging/README.md).

**Install (HA OS):** starting the PLCAssistant App copies this folder into
`/config/custom_components/plcassistant/`. Restart Core once, then add the
integration under Devices & services.
