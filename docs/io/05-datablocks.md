# 05 — Datablocks (SWD-184)

**Tracker:** [SWD-184](https://marcusknielsen.atlassian.net/browse/SWD-184)  
**Depends on:** [`02-binding-model.md`](02-binding-model.md)

## Purpose

Named **Datablocks** group Soft-PLC tags and HA entity bindings. Engineers
define mappings in the HA integration **Datablocks** configuration panel
(`/api/plcassistant/datablocks/ui`). Soft-PLC Programs declare Datablock id(s)
they can access and only see those tags.

## Shape

```json
{
  "datablocks": {
    "DB_Tank": {
      "id": "DB_Tank",
      "description": "Tank level/flow cascade process I/O (demo).",
      "tags": { "LT_TANK": { "default": 0.15, "unit": "m" } },
      "bindings": [
        { "tag": "LT_TANK", "entity": "number.plcassistant_lt_tank_in", "direction": "IN" }
      ]
    }
  },
  "program_access": { "tank": ["DB_Tank"] }
}
```

Persisted under `config/plcassistant/datablocks.json`. Binding uniqueness rules
from the [binding model](02-binding-model.md) still apply when Datablocks are
merged for accessible Programs.

## Ownership

| Concern | Owner |
|---------|-------|
| Datablock CRUD + bindings | HA integration store + panel |
| Program ↔ Datablock assignment | HA `program_access` (source of truth for wiring) |
| Soft-PLC tag visibility | Soft-PLC `Program.datablocks` (demo mirrors HA access) |
| Apply into MQTT / entities | HA `POST …/apply` updates entry `bindings` and reloads |

Keep Soft-PLC `Program.datablocks` aligned with HA `program_access` for the same
program ids. The packaging image declares only tags from the demo access map.

## Soft-PLC

`Program.datablocks` lists accessible Datablock ids. Helpers:

- `plcassistant.io.datablock.DatablockCatalog`
- `program_accessible_tags(catalog, program.datablocks)`
- `declare_default_image()` — declares tags from demo Program access only

The rebuilt demo uses `DB_Tank` and `tank` Program access. Flat
`default_wedge_binding_config()` is now a view of that access union for legacy
callers. PID faceplate tags (SP-source modes) are documented in
[`06-pid-faceplate.md`](06-pid-faceplate.md).

## Panel

Lovelace **Datablocks** tab embeds `/api/plcassistant/datablocks/ui`. The SPA
prefers `hass.callApi` (same pattern as Dynamics). APIs:

| Method | Path | Role |
|--------|------|------|
| GET | `/api/plcassistant/datablocks` | List |
| POST | `/api/plcassistant/datablocks` | Create |
| PUT/DELETE | `/api/plcassistant/datablocks/{id}` | Update/delete |
| GET/PUT | `/api/plcassistant/datablocks/access` | Program access |
| POST | `/api/plcassistant/datablocks/apply` | Write accessible bindings into entry + reload |
