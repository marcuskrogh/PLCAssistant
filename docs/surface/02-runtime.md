# Block Runtime Contract (SWD-116)

## Overview

The block runtime executes a `Program` during the **CONTROL phase** of the
Soft-PLC scan shell. It iterates `execution_order`, resolves wires and
context tags into pin values, runs each block body, and writes outputs back
to the context. Safety and mode logic remain outside the runtime; the caller
(scan shell `on_control`) decides when to call `tick`.

---

## API

### `TagContext` (protocol)

An injectable tag store; no hard-wired Skid or HA dependency.

```python
class TagContext(Protocol):
    def get(self, name: str) -> Any: ...       # None if tag absent
    def set(self, name: str, value: Any) -> None: ...
```

`DictContext` is a plain-dict implementation for tests and standalone use.

### `BlockRuntime`

```python
class BlockRuntime:
    def __init__(self, library: TemplateLibrary) -> None: ...

    def register_callable(
        self,
        library: str,
        template_id: str,
        fn: BlockCallable,
    ) -> None: ...

    def tick(
        self,
        program: Program,
        context: TagContext,
        dt: float,
    ) -> None: ...

    def reset_state(self, instance_id: str | None = None) -> None: ...
```

### `tick` — one CONTROL-phase execution

```
tick(program, context, dt)
```

| Arg | Constraint |
|---|---|
| `program` | Validated `Program` (execution_order, instances, wires). |
| `context` | Injectable `TagContext`; not inspected beyond get/set. |
| `dt` | Sample time ≥ 0 (seconds). Raises `ValueError` if < 0. |

**Algorithm (per tick):**

1. Build wire lookup: `(dst_instance, dst_pin) → (src_instance, src_pin)`.
2. For each `instance_id` in `program.execution_order`:
   a. Resolve each **IN pin**:
      - Wired pin → value from executing block's cached output.
      - Unwired pin → `context.get("{instance_id}.{pin_name}")` or pin default.
      - Unwired with no context value and no default → `ValueError`.
   b. Look up template via `library.get(inst.library, inst.template_id)`;
      fall back to `program.user_templates[template_id]` only when that
      template's `library` matches the instance; raise `ValueError` if absent.
   c. Dispatch execution:
      - **Instance equation** (SWD-180): when `inst.equation` is non-empty, evaluate
        with `plcassistant.surface.equations.evaluate_equation` (math assignments).
        Failures raise `EquationError` (no Python `exec` fallback on this path).
      - **Built-in callable**: registered `BlockCallable` when present.
      - **Template body**: try math evaluation of `template.body`; legacy
        user templates with empty instance equation may fall back to restricted
        `exec(body)` only on that path.
   d. Write each **OUT pin** value to the per-tick pin cache and to
      `context.set("{instance_id}.{pin_name}", value)`.

**Safety constraint** — Safety must NOT be inside block runtime. The scan
shell `on_safety` callback runs before `on_control`; user blocks cannot
reach or override safety outputs.  Shell-owned IN pins (currently
``running``) must not be driven by wires — `validate_program` rejects such
wires, and the skid clamp forces CMD_SPEED = 0 when permit is false.

---

## BlockCallable (built-in signature)

```python
BlockCallable = Callable[
    [dict[str, Any], dict[str, Any], dict, float],
    dict[str, Any],
]
# (input_pins, params, state, dt) -> output_pins
```

- `input_pins`: resolved IN pin values keyed by pin name.
- `params`: instance params (already deep-copied from template at place time).
- `state`: mutable per-instance dict persisted across ticks by the runtime.
- `dt`: sample time passed from `tick`.
- Returns `output_pins`: OUT pin values keyed by pin name.

---

## User Block Body

When a `BlockTemplate` has a non-empty `body` string (user-defined block),
the runtime `exec`s it with this namespace:

| Name | Meaning |
|---|---|
| `<pin_name>` (IN) | Resolved input value |
| `<param_name>` | Instance param value |
| `state` | Mutable per-instance dict (persisted across ticks) |
| `dt` | Sample time |
| `<pin_name>` (OUT) | Expected to be set by the body |

---

## Tag naming convention

| Event | Tag name |
|---|---|
| Unwired IN pin read | `context.get("{instance_id}.{pin_name}")` |
| OUT pin write | `context.set("{instance_id}.{pin_name}", value)` |

Callers bridge process tags (e.g. `LT_TANK`) to instance pins by pre-loading
the context (e.g. `context.set("level_pi.pv", image.get_value("LT_TANK"))`),
or preferably via the shared `TagPinWire` helpers in
`plcassistant.surface.io_wires` (SWD-224) so the map is one testable list.

---

## Per-instance state lifecycle

`BlockRuntime` holds `_state[instance_id]` as a mutable `dict`. Built-in
callables read and write this dict to persist integrals, flags, and cached
outputs across ticks. `reset_state(instance_id)` clears one instance;
`reset_state()` clears all. State is NOT serialised to the program YAML.

---

## Error table

| Condition | Exception |
|---|---|
| `dt < 0` | `ValueError` |
| `execution_order` entry not in `program.instances` | `ValueError` |
| Template absent from library and user_templates | `ValueError` |
| Unwired IN pin, no context value, no default | `ValueError` |
| `exec` raises (user body error) | propagated as-is |

---

## Scan shell integration

```python
shell.run(
    dt,
    on_in=...,
    on_safety=lambda: safety.tick(...),   # Safety BEFORE control
    on_control=lambda: runtime.tick(program, context, dt),
    on_out=...,
)
```

The safety callback runs in `SAFETY` phase (before `CONTROL`). The runtime
never sees safety state and cannot bypass it.

---

## Seams for future packages

| Package | How it uses the runtime |
|---|---|
| SWD-115 Built-in library | Calls `runtime.register_callable` + `library.register` at startup. |
| SWD-114 User library | User templates in `program.user_templates`; runtime `exec`s body. |
| SWD-117 Apply policy | Hot-apply passes new `Program` to same `BlockRuntime` instance. |
| SWD-121 Wedge migration | `on_control` calls `runtime.tick`; safety shell unchanged. |
