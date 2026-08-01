# App Program Surface + HTTP API (SWD-120, SWD-181)

## Overview

The App (`plcassistant/app/`) provides a mobile-first Soft-PLC Program
engineering surface backed by a plain-Python `http.server` HTTP server. It:

- Serves a vanilla HTML/JS single-page app at `GET /`.
- Shows one-column Program cards and opens each Program into Diagram, Log, and Settings.
- Exposes JSON APIs so clients can list, create, edit, apply, and delete Programs.
- Holds an in-memory `ProjectLoader`, `TemplateLibrary`, and `BlockRuntime`; no HA dependency.

### Start

```bash
python -m plcassistant.app              # default port 8099
python -m plcassistant.app --port 8080
```

Open `http://localhost:8099` in any browser.

## Routes

- `#/` and `#/programs`: one-column Program cards.
- `#/programs/new`: create Program form; new Programs are empty and unscheduled.
- `#/programs/<id>/diagram`: existing block editor canvas, Hot Apply, and Apply restart for the selected Program.
- `#/programs/<id>/log`: chronological info/warn/error Program log.
- `#/programs/<id>/settings`: name/description save and confirmed delete.

Scheduling UI is intentionally out of scope for SWD-181.

## HTTP API

### `GET /api/programs`

Returns Program cards:

```json
[
  {
    "id": "tank",
    "name": "Tank",
    "description": "Default tank level-flow cascade program.",
    "status": "not running",
    "health": "ok",
    "task_id": "main"
  }
]
```

`status` is `unscheduled` when no Task calls the Program. Scheduled Programs are
`running` only when the runtime snapshot reports `MODE=RUNNING`; otherwise they
are `not running`. `health` is derived from Program logs: `error` wins, then
`warning`, else `ok`.

### `POST /api/programs`

Create an empty unscheduled Program from `{ "name": "...", "description": "..." }`.
The id is a unique slug from the name. Returns the created card.

### `GET /api/programs/<id>`

Returns the Program dict, including `name` and `description`.

### `PUT /api/programs/<id>/meta`

Updates only `name` and `description`. Instances, wires, execution order, and user
templates are preserved.

### `DELETE /api/programs/<id>`

Removes a Program and deletes it from any Task call lists. The App applies the
resulting project with restart semantics. Missing ids return `404`.

### `GET /api/programs/<id>/log`

Returns chronological log entries:

```json
[{"ts": "2026-08-01T07:00:00+00:00", "level": "info", "message": "Program Tank loaded"}]
```

### `GET /api/program?id=<program_id>`

Returns the selected Program as a JSON-shaped dict. Without `id`, defaults to the
first Main-task Program for backward compatibility.

### `PUT /api/program?id=<program_id>`

Replaces the selected Program body and returns the validated Program dict. Without
`id`, defaults to the first Main-task Program.

### `GET /api/project` / `PUT /api/project`

Round-trips the full Soft-PLC project tree (`tasks`, `programs`, and
`scan_period_s`). Structure changes restart; logic-only project changes use the
existing hot-apply policy.

### `GET /api/library`

Returns all registered templates (builtin + user) as a JSON array.

### `POST /api/library/user` / `DELETE /api/library/user/<template_id>`

Create/update/delete a user template. Pass `?id=<program_id>` or body
`program_id` to target a selected Program; omitted id targets the Main Program.

### `POST /api/place`

Place a block instance on the selected canvas. Accepts `?id=<program_id>` or body
`program_id`; omitted id targets the Main Program. Returns the updated Program.

### `POST /api/reset_instance`

Reset an instance params to library defaults on the selected Program. Accepts
`?id=<program_id>` or body `program_id`.

### `POST /api/apply`

Apply the in-memory project to the runtime. The optional selected Program id is
used for logging:

```json
{ "mode": "restart", "program_id": "tank" }
```

Hot apply requires server-side authority via `PLCASSISTANT_SUPERUSER_HOT_APPLY=1`
(or trusted server-side state). Client-supplied `superuser` remains ignored.

## Canvas interactions

| Interaction | Effect |
|---|---|
| Drag library item -> canvas | Place new block instance |
| Drag block | Move block; position saved on mouse-up |
| Double-click block | Open block properties |
| Drag OUT pin -> IN pin | Create wire |
| Click wire | Delete wire |
| Edit JSON textarea | Replace selected Program body |
| Remove button | Delete selected block and its wires |
| User Block Editor | Create / edit / delete user Python blocks |

## Testing

```bash
python3 -m pytest -q tests/test_app_api.py tests/test_swd181_acceptance.py
```

Tests use `urllib.request` directly against a real `HTTPServer` bound to a random
port.
