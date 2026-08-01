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
from the binding model still apply when Datablocks are merged for a Program.

## Soft-PLC

`Program.datablocks` lists accessible Datablock ids. Helpers:

- `plcassistant.io.datablock.DatablockCatalog`
- `program_accessible_tags(catalog, program.datablocks)`

The rebuilt demo uses `DB_Tank` and `tank` Program access. Flat
`default_wedge_binding_config()` is now a view of `DB_Tank` for legacy callers.

## Panel

Lovelace **Datablocks** tab embeds `/api/plcassistant/datablocks/ui`. APIs:

| Method | Path | Role |
|--------|------|------|
| GET | `/api/plcassistant/datablocks` | List |
| POST | `/api/plcassistant/datablocks` | Create |
| PUT/DELETE | `/api/plcassistant/datablocks/{id}` | Update/delete |
| GET/PUT | `/api/plcassistant/datablocks/access` | Program access |
| POST | `/api/plcassistant/datablocks/apply` | Flatten into runtime binding cache |
