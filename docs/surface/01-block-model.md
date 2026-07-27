# Block Model Contract (SWD-119)

## Overview

The block programming surface uses a **progressive Python block library**: users place
copies of templates onto a visual canvas; the resulting program is the canonical source
of truth, serialised as YAML (or its dict equivalent). The block runtime executes the
program in a deterministic scan order inside the CONTROL phase of the Soft-PLC scan
shell.

---

## Core Concepts

### PinSpec

A typed connection point declared on a `BlockTemplate`.

| Field | Type | Meaning |
|---|---|---|
| `name` | `str` | Unique within the template; used to route wires. |
| `direction` | `PinDirection` | `IN` (value flows into the block) or `OUT` (block writes it). |
| `data_type` | `str` | Advisory type hint (`"float"`, `"bool"`, `"int"`, …). Not enforced at model layer; runtime may use it. |
| `default` | `Any` | Value used when the pin is not connected. `None` means no default (runtime error if unwired). |

### BlockTemplate

The **library definition**. Templates are never mutated by user actions. Built-in
templates (`is_builtin=True`) are shipped with the package and are strictly read-only.
User templates are stored inside `Program.user_templates` and round-tripped via YAML.

| Field | Type | Meaning |
|---|---|---|
| `template_id` | `str` | Unique within its `library`. |
| `library` | `str` | `"builtin"` for stock blocks; any string for user libraries. |
| `description` | `str` | Human-readable summary. |
| `pins` | `list[PinSpec]` | Ordered input/output pins. |
| `params` | `dict[str, Any]` | Default configurable parameters (Kp, Ki, setpoint, …). |
| `body` | `str` | Python source for user-defined blocks. Empty for built-ins (runtime wires them natively). |
| `is_builtin` | `bool` | True ⇒ stock/read-only; must not be edited in-place. |

### BlockInstance

A **placed copy** of a template. Placing always deep-copies template params so that
editing an instance never mutates the library entry.

| Field | Type | Meaning |
|---|---|---|
| `instance_id` | `str` | Unique within the `Program`. |
| `template_id` | `str` | ID of the originating template. |
| `library` | `str` | Library of the originating template (`"builtin"` or user). |
| `params` | `dict[str, Any]` | Per-instance parameter overrides (full copy; independent of template). |
| `x`, `y` | `float` | Canvas position hints (optional; default 0.0). |

#### Copy-on-place

`place_block(template, instance_id, **kwargs) -> BlockInstance`

- Creates a new `BlockInstance` with `params` deep-copied from `template.params`.
- Caller-supplied `params` are merged on top (also deep-copied).
- Two calls to `place_block` on the same template yield two independent instances; mutating one never affects the other or the template.

#### Reset-to-library

`reset_instance(instance, template) -> BlockInstance`

- Returns a **new** `BlockInstance` with `params` replaced by a deep copy of `template.params`.
- `instance_id`, `x`, `y` are preserved.
- Raises `ValueError` if `instance.template_id` / `instance.library` do not match the supplied template.

### Wire

A directional data connection between a `src_instance`/`src_pin` and a
`dst_instance`/`dst_pin`.

Constraints (validated by `validate_program`):
- `src_instance` and `dst_instance` must exist in `Program.instances`.
- At most **one wire** may drive a given `(dst_instance, dst_pin)` (single-source rule).
- Multiple wires from the same source are allowed (fan-out is fine).

### Program

The complete executable program.

| Field | Type | Meaning |
|---|---|---|
| `instances` | `dict[str, BlockInstance]` | All placed blocks, keyed by `instance_id`. |
| `wires` | `list[Wire]` | All data connections. |
| `execution_order` | `list[str]` | Deterministic scan order — list of `instance_id`s. |
| `user_templates` | `dict[str, BlockTemplate]` | User-defined templates embedded in the program YAML. |
| `version` | `str` | Schema version string (default `"1.0"`). |

#### execution_order

- Explicit list stored in the program. The runtime tick (SWD-116) iterates this list
  in order during CONTROL.
- If omitted on load, defaults to `list(instances.keys())` (insertion order).
- Validated: all entries must be valid `instance_id`s; no duplicates.
- Topological auto-sort is a runtime concern (SWD-116); the data model stores whatever
  order is provided.

---

## TemplateLibrary Seam

`TemplateLibrary` is an injectable registry used by the runtime and App. It is **not**
serialised into the program YAML; built-in blocks are registered by the built-in
library package (SWD-115) at startup, and user templates are re-registered from
`Program.user_templates` on load.

```
library.register(template)          # add/overwrite a template
library.get(library, template_id)   # look up by (library, id) → BlockTemplate | None
library.all_templates()             # list all registered templates
```

The runtime (SWD-116) calls `library.get(inst.library, inst.template_id)` to resolve
the body for each instance during execution. The App canvas (SWD-120) calls
`library.all_templates()` to populate the block picker.

---

## YAML / Dict Schema

Programs are serialised as plain Python dicts (YAML-ready). Built-in templates are
referenced by `library`/`template_id` only; they are not embedded in the program dict.

```yaml
version: "1.0"

user_templates:           # omitted when empty
  my_pid:
    library: user
    description: Custom PID block
    pins:
      - {name: pv,  direction: IN,  data_type: float, default: 0.0}
      - {name: sp,  direction: IN,  data_type: float, default: 0.0}
      - {name: cv,  direction: OUT, data_type: float}
    params:
      kp: 1.0
      ki: 0.0
      kd: 0.0
    body: |
      # Python block body executed each scan tick

instances:
  inst_sensor:
    template_id: level_sensor
    library: builtin
    params: {}
  inst_pid:
    template_id: my_pid
    library: user
    params:
      kp: 2.5
    x: 100.0
    y: 200.0

wires:
  - {src_instance: inst_sensor, src_pin: level_out,
     dst_instance: inst_pid,    dst_pin: pv}

execution_order:
  - inst_sensor
  - inst_pid
```

### Schema rules

- `version` — required string.
- `user_templates` — optional mapping; each entry serialises a `BlockTemplate`.
- `instances` — required mapping; each entry serialises a `BlockInstance`.
- `wires` — required list (may be empty); each entry has `src_instance`, `src_pin`, `dst_instance`, `dst_pin`.
- `execution_order` — optional list; if absent, defaults to instance insertion order.

### Validation errors (ValueError)

| Condition | Message pattern |
|---|---|
| `instance` missing `template_id` or `library` | `instance {id!r} missing required key …` |
| `execution_order` entry not in `instances` | `execution_order references unknown instance …` |
| Duplicate entry in `execution_order` | `execution_order contains duplicate instance …` |
| Wire `src_instance` / `dst_instance` not in `instances` | `wire src_instance … not in instances` |
| Two wires drive same `(dst_instance, dst_pin)` | `multiple wires drive pin … on instance …` |
| Wire drives shell-owned pin (`running`) | `wire cannot drive shell-owned pin …` |
| `reset_instance` template mismatch | `template mismatch: instance references …` |

---

## Seams for Future Packages

| Future package | How it uses this model |
|---|---|
| **SWD-116** Python block runtime | Iterates `program.execution_order`; calls `library.get(inst.library, inst.template_id)` to resolve body; reads `program.wires` for pin routing. |
| **SWD-115** Built-in block library | Calls `library.register(template)` for each stock block at startup; sets `is_builtin=True`. |
| **SWD-114** User library + editor | Creates `BlockTemplate` objects; stores in `program.user_templates`; calls `place_block` and `reset_instance`. |
| **SWD-120** App visual canvas | Calls `program_to_dict` / `program_from_dict` for YAML ↔ canvas round-trip; calls `place_block` on drag-drop. |
| **SWD-117** Apply policy | Calls `program_from_dict` on restart to load a new program. Hot-apply passes the new `Program` directly to the runtime. |
