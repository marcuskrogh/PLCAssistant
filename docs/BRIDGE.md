# Bridge developer note (SWD-71)

How the HACS integration maps [IO_HAL.md](IO_HAL.md) fields to UI + addon sync.

## Packages

| Path | Role |
|------|------|
| `packages/plcassistant_contract/` | Binding models, validation, coercion, fail-safe, HTTP control-plane client |
| `custom_components/plcassistant/` | Config entry, binding store/UI, diagnostic entities, HA services |

The **scan HAL loop** is **not** here — that is [SWD-69](https://marcusknielsen.atlassian.net/browse/SWD-69) inside the addon. This phase only owns registry SoT + `PutBindings` / `GetStatus` client.

## Binding JSON (options UI)

Options flow field `bindings_json` is a JSON array of binding objects. Example:

```json
[
  {
    "tag": "IX0",
    "direction": "input",
    "entity_id": "binary_sensor.door",
    "value_type": "bool",
    "unavailable_policy": "hold_last",
    "cold_start_policy": "force_zero"
  },
  {
    "tag": "QX0",
    "direction": "output",
    "entity_id": "switch.pump",
    "value_type": "bool",
    "write_mode": "service",
    "service": { "domain": "switch", "service": "turn_on", "data_template": {} },
    "critical": true,
    "on_bridge_fault": "hold_last_command"
  },
  {
    "tag": "MW0",
    "direction": "memory_mirror",
    "entity_id": "input_number.setpoint",
    "value_type": "number",
    "mirror_to_ha": false
  }
]
```

Validation uses `plcassistant_contract.validate_bindings` (same rules as IO_HAL).

## Control-plane HTTP (addon)

Base URL from config entry `addon_url`. Bearer token optional (`token`).

| Method | Path | Body |
|--------|------|------|
| PUT | `/api/bindings` | `{ "bindings": [ ... ] }` |
| PUT | `/api/scan_options` | `{ "scan_period_ms": 100, ... }` |
| GET | `/api/status` | → `RuntimeStatus` fields (diagnostics) |
| POST | `/api/start` \| `/api/stop` \| `/api/reload` | `{}` |

HA services `plcassistant.reload` / `start` / `stop` call these. If the addon is down, reload/start/stop raise; diagnostic entities show `bridge_connected=false` / `runtime_state=stopped`.

## Tests

```bash
python3 -m pip install -e packages/plcassistant_contract pytest
python3 -m pytest packages/plcassistant_contract/tests -q
```

Contract + client tests do not require Home Assistant Core.
