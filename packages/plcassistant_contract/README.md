# plcassistant_contract

Pure-Python binding schema, coercion, and fail-safe policies for PLCAssistant.
No Home Assistant or OpenPLC imports. No HTTP client (see
`custom_components/plcassistant/control_plane.py`).

A vendored copy ships with the HACS integration under
`custom_components/plcassistant/vendor/plcassistant_contract/`. After editing
modules here, run `./scripts/sync_contract_vendor.sh`.

See [docs/IO_HAL.md](../../docs/IO_HAL.md) and [docs/BRIDGE.md](../../docs/BRIDGE.md).
