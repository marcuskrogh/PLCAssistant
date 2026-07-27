# App Visual Canvas + HTTP API (SWD-120)

## Overview

The App (`plcassistant/app/`) provides a visual block editor backed by a
plain-Python `http.server`-based HTTP server.  It:

- Serves a single-page canvas (vanilla HTML/JS) at `GET /`.
- Exposes a JSON API so the canvas and external clients can round-trip the program.
- Holds an in-memory `ProgramLoader` and `BlockRuntime`; no HA dependency.

### Start

```bash
python -m plcassistant.app              # default port 8099
python -m plcassistant.app --port 8080
```

Open `http://localhost:8099` in any browser.

---

## HTTP API

### `GET /`

Visual canvas — HTML/JS single-page app.

- Left sidebar: block library (builtin + user templates); drag to place.
- Centre canvas: placed blocks (SVG); drag to move; wire OUT→IN pins.
- Right panel: live JSON textarea (edit directly); user block Python editor.
- Top bar: *Apply (restart)*, *Hot Apply*, *Remove* buttons.

---

### `GET /api/program`

Returns the current program as a JSON-shaped dict.

```json
{
  "version": "1.0",
  "instances": { ... },
  "wires": [ ... ],
  "execution_order": [ ... ],
  "user_templates": { ... }
}
```

---

### `PUT /api/program`

Replace the active program.  Body must be a JSON dict conforming to the
program schema.  Applies via `restart_apply` (clears runtime state).

```http
PUT /api/program
Content-Type: application/json

{ "version": "1.0", "instances": { ... }, "wires": [], "execution_order": [] }
```

Returns the validated program dict.

---

### `GET /api/library`

Returns all registered templates (builtin + user) as a JSON array.

```json
[
  {
    "template_id": "level_pi",
    "library": "builtin",
    "description": "...",
    "pins": [ { "name": "pv", "direction": "IN", "data_type": "float", "default": 0.0 }, ... ],
    "params": { "kp": 40.0, "ki": 5.0, "cv_min": 0.0, "cv_max": 6.0 },
    "body": "",
    "is_builtin": true
  }
]
```

---

### `POST /api/library/user`

Create or update a user template.  The body is a JSON dict:

```json
{
  "template_id": "my_gain",
  "description": "Multiply x by gain",
  "library": "user",
  "pins": [
    {"name": "x",   "direction": "IN",  "data_type": "float", "default": 0.0},
    {"name": "out", "direction": "OUT", "data_type": "float"}
  ],
  "params": {"gain": 1.0},
  "body": "out = x * gain"
}
```

Returns `{"template_id": "my_gain", "library": "user"}` on success.

The template is stored in `program.user_templates` and registered into the
`TemplateLibrary`.

---

### `DELETE /api/library/user/<template_id>`

Delete a user template from the active program and the library.

---

### `POST /api/place`

Place a block instance on the canvas.

```json
{
  "template_id": "level_pi",
  "library": "builtin",
  "instance_id": "lpi_1",
  "x": 100.0,
  "y": 200.0
}
```

Returns the updated program dict.

---

### `POST /api/reset_instance`

Reset an instance's params to the library template defaults.

```json
{ "instance_id": "lpi_1" }
```

Returns the updated program dict.

---

### `POST /api/apply`

Apply the current in-memory program to the runtime.

```json
{ "mode": "restart" }
```

or (hot-apply — requires server-side authority):

```json
{ "mode": "hot" }
```

| `mode` | Effect |
|---|---|
| `"restart"` | `ProgramLoader.restart_apply` — clears runtime state |
| `"hot"` | `ProgramLoader.hot_apply` — preserves runtime state |

Hot-apply succeeds only when `PLCASSISTANT_SUPERUSER_HOT_APPLY=1` was set in
the process environment before the App started.  Any client-supplied
`superuser` field is **ignored**.

Returns `{"applied": "restart"}` or `{"applied": "hot"}`.  Hot without
authority returns `403`.

---

## Canvas interactions

| Interaction | Effect |
|---|---|
| Drag library item → canvas | Place new block instance |
| Drag block | Move block; position saved on mouse-up |
| Double-click block | Open block properties (param editor) |
| Drag OUT pin → IN pin | Create wire |
| Click wire | Delete wire |
| Edit JSON textarea | Replace program (parsed on valid JSON) |
| ✕ Remove button | Delete selected block and its wires |
| User Block Editor (right panel) | Create / edit / delete user Python blocks |

---

## Architecture

```
plcassistant/app/
├── __init__.py          # re-exports AppState, make_handler, run_app
├── __main__.py          # python -m plcassistant.app entry point
├── server.py            # HTTP server, AppState, route handlers
└── _canvas.py           # HTML/JS visual canvas (returned by GET /)
```

`AppState` holds one `ProgramLoader`, one `TemplateLibrary`, and one
`BlockRuntime`.  All HTTP handlers operate on the shared `AppState`.

---

## Testing

```bash
python3 -m pytest -q tests/test_app_api.py
```

Tests use `urllib.request` directly against a real `HTTPServer` bound to a
random port — no Selenium, no browser required.

---

## Seams

| Package | Integration |
|---|---|
| SWD-114 User library | `POST /api/library/user` calls `add_user_template` + `make_user_template` |
| SWD-117 Apply policy | `POST /api/apply` calls `ProgramLoader.restart_apply` or `hot_apply` |
| SWD-116 Runtime | `AppState.runtime` is the same `BlockRuntime` used for `tick` |
| SWD-119 Schema | `PUT /api/program` calls `program_from_dict`; `GET /api/program` calls `program_to_dict` |
