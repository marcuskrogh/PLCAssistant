"""Block program runtime: CONTROL-phase tick, pin resolution, tag I/O (SWD-116).

See docs/surface/02-runtime.md for the full contract.
No Home Assistant dependency; safety must NOT be inside this runtime.
The caller (scan shell on_control) decides when to invoke tick().
"""

from __future__ import annotations

import math as _math
from typing import Any, Callable, Protocol

from plcassistant.surface.model import (
    BlockTemplate,
    PinDirection,
    Program,
    TemplateLibrary,
)


class TagContext(Protocol):
    """Injectable tag I/O context: get/set named tag values.

    The runtime resolves unwired IN pins via ``get`` and writes all OUT pins
    via ``set`` using the ``"{instance_id}.{pin_name}"`` naming convention.
    No HA or Skid coupling; callers bridge process tags externally.
    """

    def get(self, name: str) -> Any:
        """Return current tag value, or ``None`` if the tag is absent."""
        ...

    def set(self, name: str, value: Any) -> None:
        """Write a tag value."""
        ...


class DictContext:
    """Plain-dict ``TagContext`` for tests and standalone use."""

    def __init__(self, tags: dict[str, Any] | None = None) -> None:
        self._tags: dict[str, Any] = dict(tags or {})

    def get(self, name: str) -> Any:
        return self._tags.get(name)

    def set(self, name: str, value: Any) -> None:
        self._tags[name] = value

    def as_dict(self) -> dict[str, Any]:
        return dict(self._tags)

    def __getitem__(self, name: str) -> Any:
        return self._tags[name]

    def __setitem__(self, name: str, value: Any) -> None:
        self._tags[name] = value

    def __contains__(self, name: object) -> bool:
        return name in self._tags


BlockCallable = Callable[
    [dict[str, Any], dict[str, Any], dict, float],
    dict[str, Any],
]
"""Built-in block callable: (input_pins, params, state, dt) -> output_pins."""


class BlockRuntime:
    """Execute a Program in deterministic CONTROL-phase order.

    Per-instance state (integrals, bumpless flags, last outputs) is held in
    ``_state[instance_id]``. Create one ``BlockRuntime`` per program lifetime.
    Pass a new ``Program`` to ``tick`` for hot-apply (SWD-117).

    Safety must NOT be embedded here — the scan shell ``on_safety`` callback
    runs before ``on_control``; user blocks cannot bypass safety outputs.

    Usage::

        library = TemplateLibrary()
        register_builtins(library, runtime)          # SWD-115
        runtime = BlockRuntime(library)
        # inside on_control:
        runtime.tick(program, context, dt)
    """

    def __init__(self, library: TemplateLibrary) -> None:
        self._library = library
        self._state: dict[str, dict] = {}
        self._callables: dict[tuple[str, str], BlockCallable] = {}

    def register_callable(
        self,
        library: str,
        template_id: str,
        fn: BlockCallable,
    ) -> None:
        """Register a native Python callable for a ``(library, template_id)`` pair.

        Built-in block packages (SWD-115) call this at startup.  Registration
        is separate from ``TemplateLibrary`` (template metadata) so runtime
        functions can be swapped without mutating templates.
        """
        self._callables[(library, template_id)] = fn

    def tick(
        self,
        program: Program,
        context: TagContext,
        dt: float,
    ) -> None:
        """Execute one CONTROL-phase tick of *program*.

        Args:
            program: Validated ``Program`` (execution_order, instances, wires).
            context: Injectable ``TagContext`` for tag I/O.
            dt: Sample time in seconds (must be ≥ 0).

        Raises:
            ValueError: ``dt < 0``, unknown instance in execution_order,
                        template not found, or unwired pin has no default.
        """
        if dt < 0:
            raise ValueError("dt must be non-negative")

        # Wire lookup: (dst_instance, dst_pin) → (src_instance, src_pin)
        wire_map: dict[tuple[str, str], tuple[str, str]] = {
            (w.dst_instance, w.dst_pin): (w.src_instance, w.src_pin)
            for w in program.wires
        }

        # Per-tick cache for inter-block wire values (supports fan-out)
        pin_cache: dict[tuple[str, str], Any] = {}

        for instance_id in program.execution_order:
            inst = program.instances.get(instance_id)
            if inst is None:
                raise ValueError(
                    f"execution_order references unknown instance {instance_id!r}"
                )

            template = self._resolve_template(inst.library, inst.template_id, program)

            # Resolve IN pin values
            input_pins: dict[str, Any] = {}
            for pin_spec in template.pins:
                if pin_spec.direction is not PinDirection.IN:
                    continue
                wire_key = (instance_id, pin_spec.name)
                if wire_key in wire_map:
                    src_inst, src_pin = wire_map[wire_key]
                    cache_key = (src_inst, src_pin)
                    if cache_key not in pin_cache:
                        raise ValueError(
                            f"wire source {src_inst!r}.{src_pin!r} → "
                            f"{instance_id!r}.{pin_spec.name!r} has not been "
                            f"computed yet: check execution_order (source must "
                            f"run before destination)"
                        )
                    value = pin_cache[cache_key]
                else:
                    tag_name = f"{instance_id}.{pin_spec.name}"
                    ctx_val = context.get(tag_name)
                    if ctx_val is not None:
                        value = ctx_val
                    elif pin_spec.default is not None:
                        value = pin_spec.default
                    else:
                        raise ValueError(
                            f"pin {pin_spec.name!r} on instance {instance_id!r} "
                            f"is unconnected and has no default"
                        )
                input_pins[pin_spec.name] = value

            # Ensure per-instance state dict exists
            if instance_id not in self._state:
                self._state[instance_id] = {}
            state = self._state[instance_id]

            output_pins = self._execute(inst.library, inst.template_id, template,
                                        input_pins, inst.params, state, dt)

            # Write outputs to cache and context
            for pin_spec in template.pins:
                if pin_spec.direction is not PinDirection.OUT:
                    continue
                value = output_pins.get(pin_spec.name)
                pin_cache[(instance_id, pin_spec.name)] = value
                context.set(f"{instance_id}.{pin_spec.name}", value)

    def _resolve_template(
        self,
        library: str,
        template_id: str,
        program: Program,
    ) -> BlockTemplate:
        tmpl = self._library.get(library, template_id)
        if tmpl is None:
            candidate = program.user_templates.get(template_id)
            # Fall back only when the stored template's library matches the
            # instance's library — never cross-resolve by template_id alone.
            if candidate is not None and candidate.library == library:
                tmpl = candidate
        if tmpl is None:
            raise ValueError(
                f"template {library!r}/{template_id!r} not found in library "
                f"or program.user_templates"
            )
        return tmpl

    def _execute(
        self,
        library: str,
        template_id: str,
        template: BlockTemplate,
        input_pins: dict[str, Any],
        params: dict[str, Any],
        state: dict,
        dt: float,
    ) -> dict[str, Any]:
        key = (library, template_id)
        if key in self._callables:
            return self._callables[key](input_pins, params, state, dt)
        if template.body:
            return _exec_user_body(template, input_pins, params, state, dt)
        raise ValueError(
            f"no callable registered and no body for {library!r}/{template_id!r}"
        )

    def reset_state(self, instance_id: str | None = None) -> None:
        """Clear per-instance runtime state.

        Call with ``instance_id=None`` to clear all instances (e.g. on stop).
        """
        if instance_id is None:
            self._state.clear()
        else:
            self._state.pop(instance_id, None)

    def set_instance_state(self, instance_id: str, updates: dict) -> None:
        """Merge *updates* into the per-instance state dict.

        Creates the entry for *instance_id* if it does not yet exist.
        Used by callers that need to pre-seed integrator or bumpless-start
        state before the first RUNNING tick (e.g. SWD-121 wedge migration).
        """
        if instance_id not in self._state:
            self._state[instance_id] = {}
        self._state[instance_id].update(updates)

    @property
    def state(self) -> dict[str, dict]:
        """Read-only view of current per-instance state (for diagnostics)."""
        return self._state


_SAFE_BUILTINS: dict[str, Any] = {
    "abs": abs,
    "bool": bool,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "max": max,
    "min": min,
    "range": range,
    "round": round,
    "sum": sum,
    "zip": zip,
    # Boolean singletons (referenced by name in exec'd code)
    "True": True,
    "False": False,
    "None": None,
}
"""Restricted built-ins available inside user block bodies.

Dangerous functions (``__import__``, ``open``, ``eval``, ``exec``,
``compile``, ``getattr``, ``setattr``, ``__class__``, …) are **not**
included.  ``math`` is injected separately as a module-level name so that
``math.sqrt(x)`` works without allowing arbitrary imports.
"""


def _exec_user_body(
    template: BlockTemplate,
    input_pins: dict[str, Any],
    params: dict[str, Any],
    state: dict,
    dt: float,
) -> dict[str, Any]:
    """Execute a user-defined block body string and return output pin values.

    Execution namespace: all IN pin names as variables, all param names,
    ``state`` dict, ``dt``, ``math`` module.  OUT pin names are read back from
    the namespace after execution.

    ``__builtins__`` is restricted to :data:`_SAFE_BUILTINS` so that dangerous
    callables (``__import__``, ``open``, ``eval``, ``exec``, …) are
    unavailable inside user bodies.
    """
    globals_ns: dict[str, Any] = {"__builtins__": _SAFE_BUILTINS, "math": _math}
    locals_ns: dict[str, Any] = {}
    locals_ns.update(params)
    locals_ns.update(input_pins)
    locals_ns["state"] = state
    locals_ns["dt"] = dt

    exec(template.body, globals_ns, locals_ns)  # noqa: S102

    return {
        pin.name: locals_ns.get(pin.name, pin.default)
        for pin in template.pins
        if pin.direction is PinDirection.OUT
    }


def make_runtime(library: TemplateLibrary) -> BlockRuntime:
    """Convenience factory: create a ``BlockRuntime`` backed by *library*."""
    return BlockRuntime(library)


__all__ = [
    "BlockCallable",
    "BlockRuntime",
    "DictContext",
    "TagContext",
    "make_runtime",
]
