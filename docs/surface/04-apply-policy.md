# Apply Policy (SWD-117)

## Overview

`ProgramLoader` (`plcassistant/surface/apply.py`) owns the active `Program`
and its associated `BlockRuntime`.  It exposes two apply modes:

| Mode | State cleared | Auth required | Use case |
|---|---|---|---|
| `restart_apply` | Yes (full reset) | No | Default; always safe |
| `hot_apply` | No | Superuser | Development; bumpless swap |

---

## API

```python
from plcassistant.surface.apply import ProgramLoader
from plcassistant.surface.model import TemplateLibrary
from plcassistant.surface.runtime import BlockRuntime
from plcassistant.surface.builtin import register_builtins

library = TemplateLibrary()
runtime = BlockRuntime(library)
register_builtins(library, runtime)

loader = ProgramLoader(library, runtime)
```

### `load(program)` / `restart_apply(program)`

Default apply path.  Equivalent — `load` is the canonical name; `restart_apply`
is an alias for clarity in the apply context.

```python
loader.load(program)         # or
loader.restart_apply(program)
```

**Effect:**

1. Registers all user templates from `program.user_templates` into the library.
2. Clears **all** runtime state (`runtime.reset_state()`).
3. Sets `loader.program = program`.

The next `runtime.tick()` starts from a clean slate (integrals at zero,
bumpless flags cleared, no cached outputs).

---

### `hot_apply(program, *, superuser=False)`

Swaps the active program without clearing runtime state.

```python
loader.hot_apply(new_program, superuser=True)
```

**Effect:**

1. Validates superuser authority (see below).
2. Registers user templates from the new program.
3. Sets `loader.program = new_program` — existing runtime state is preserved.

**Raises `PermissionError`** if not authorised.

---

## Superuser authorisation

`hot_apply` is protected by a **server-side** check only:

| Mechanism | How to enable |
|---|---|
| Caller flag | Pass `superuser=True` from a trusted server-side caller |
| Environment variable | Set `PLCASSISTANT_SUPERUSER_HOT_APPLY=1` before starting the App |

Either condition grants authority.  The HTTP server (`POST /api/apply`) reads
the env var once at `AppState` construction and **ignores** any `superuser`
field supplied in the request body — client code cannot self-elevate.

Typical configuration:

- **Environment flag:** set `PLCASSISTANT_SUPERUSER_HOT_APPLY=1` in the
  process environment (e.g. `.env` file or Docker Compose override) before
  running `python -m plcassistant.app`.  The App canvas ⚡ Hot Apply button
  will then succeed without further client-side configuration.

> **Security note:** Hot-apply is for development only.  Do not enable it in
> safety-critical or production deployments.  The environment flag name starts
> with `PLCASSISTANT_SUPERUSER_` to make its intent explicit.

---

## State lifecycle

| Event | Runtime state |
|---|---|
| `restart_apply` | Cleared (`reset_state()`) |
| `hot_apply` | Preserved |
| Manual `runtime.reset_state()` | Cleared all (caller's choice) |
| `runtime.reset_state(instance_id)` | Cleared one instance |

After `hot_apply`, the loader automatically:

- **Drops** runtime state for instance IDs no longer present in the new program.
- **Resets** runtime state for instances whose `template_id` changed (new
  template has a different state schema).
- **Prunes** stale user templates from the `TemplateLibrary`.

Remaining state (same instances, same templates) is preserved for bumpless
continuity.

---

## Properties

| Property | Type | Meaning |
|---|---|---|
| `loader.program` | `Program \| None` | Active program; `None` before first load |
| `loader.runtime` | `BlockRuntime` | The runtime held by the loader |

---

## Integration with scan shell

```python
# Scan shell on_control callback:
def on_control():
    if loader.program is not None:
        runtime.tick(loader.program, context, dt)
```

---

## Seams

| Package | How it uses apply policy |
|---|---|
| SWD-120 App | Calls `loader.restart_apply` or `loader.hot_apply` from `POST /api/apply` |
| SWD-116 Runtime | `loader.runtime` is the same `BlockRuntime` instance used for `tick` |
| SWD-114 User library | User templates from new program are auto-registered on apply |
