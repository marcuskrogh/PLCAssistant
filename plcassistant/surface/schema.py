"""Program YAML-shaped dict round-trip, validation, place_block, reset_instance (SWD-119).

Dict-first pattern (see plcassistant/io/binding.py): callers work with plain Python
dicts; yaml.safe_dump / yaml.safe_load are optional wrappers the caller supplies.
No Home Assistant dependency; no hard-wired I/O.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from plcassistant.surface.model import (
    BlockInstance,
    BlockTemplate,
    PinDirection,
    PinSpec,
    Program,
    Wire,
)


# ---------------------------------------------------------------------------
# Public operations: place_block, reset_instance
# ---------------------------------------------------------------------------


def place_block(
    template: BlockTemplate,
    instance_id: str,
    *,
    params: dict[str, Any] | None = None,
    x: float = 0.0,
    y: float = 0.0,
) -> BlockInstance:
    """Return an independent placed copy of *template*.

    ``params`` (when supplied) are merged on top of a deep copy of
    ``template.params``; omitted keys retain template defaults.
    Mutating the returned instance never affects the template or other instances.
    """
    merged: dict[str, Any] = copy.deepcopy(template.params)
    if params:
        merged.update(copy.deepcopy(params))
    return BlockInstance(
        instance_id=instance_id,
        template_id=template.template_id,
        library=template.library,
        params=merged,
        x=x,
        y=y,
    )


def reset_instance(instance: BlockInstance, template: BlockTemplate) -> BlockInstance:
    """Return a new BlockInstance with params restored to *template* defaults.

    ``instance_id``, ``x``, and ``y`` are preserved.
    Raises ``ValueError`` when the instance's template identity does not match.
    """
    if (instance.template_id, instance.library) != (
        template.template_id,
        template.library,
    ):
        raise ValueError(
            f"template mismatch: instance references "
            f"{instance.library}/{instance.template_id!r} "
            f"but template is {template.library}/{template.template_id!r}"
        )
    return BlockInstance(
        instance_id=instance.instance_id,
        template_id=template.template_id,
        library=template.library,
        params=copy.deepcopy(template.params),
        x=instance.x,
        y=instance.y,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_program(program: Program) -> None:
    """Validate structural consistency of *program*.

    Raises ``ValueError`` with a descriptive message on the first violation:

    * Each instance has non-empty ``instance_id``, ``template_id``, ``library``;
      the dict key must match ``instance_id``.
    * ``execution_order`` entries exist in ``instances``; no duplicates.
    * Wire ``src_instance`` / ``dst_instance`` exist in ``instances``.
    * At most one wire drives a given ``(dst_instance, dst_pin)`` pair.
    """
    for iid, inst in program.instances.items():
        if not iid:
            raise ValueError("instance_id must be non-empty")
        if iid != inst.instance_id:
            raise ValueError(
                f"instance key {iid!r} does not match instance_id {inst.instance_id!r}"
            )
        if not inst.template_id:
            raise ValueError(f"instance {iid!r} has empty template_id")
        if not inst.library:
            raise ValueError(f"instance {iid!r} has empty library")

    seen_order: set[str] = set()
    for iid in program.execution_order:
        if iid not in program.instances:
            raise ValueError(
                f"execution_order references unknown instance {iid!r}"
            )
        if iid in seen_order:
            raise ValueError(
                f"execution_order contains duplicate instance {iid!r}"
            )
        seen_order.add(iid)

    dst_pins: set[tuple[str, str]] = set()
    for wire in program.wires:
        if wire.src_instance not in program.instances:
            raise ValueError(
                f"wire src_instance {wire.src_instance!r} not in instances"
            )
        if wire.dst_instance not in program.instances:
            raise ValueError(
                f"wire dst_instance {wire.dst_instance!r} not in instances"
            )
        dst_key = (wire.dst_instance, wire.dst_pin)
        if dst_key in dst_pins:
            raise ValueError(
                f"multiple wires drive pin {wire.dst_pin!r} on instance"
                f" {wire.dst_instance!r}"
            )
        dst_pins.add(dst_key)


# ---------------------------------------------------------------------------
# Serialisation helpers (private)
# ---------------------------------------------------------------------------


def _pin_to_dict(pin: PinSpec) -> dict[str, Any]:
    d: dict[str, Any] = {
        "name": pin.name,
        "direction": pin.direction.value,
        "data_type": pin.data_type,
    }
    if pin.default is not None:
        d["default"] = pin.default
    return d


def _pin_from_dict(data: Mapping[str, Any], idx: int) -> PinSpec:
    for key in ("name", "direction"):
        if key not in data:
            raise ValueError(f"pins[{idx}] missing required key {key!r}")
    raw_dir = str(data["direction"]).upper()
    try:
        direction = PinDirection(raw_dir)
    except ValueError as exc:
        raise ValueError(
            f"pins[{idx}] invalid direction {data['direction']!r}"
        ) from exc
    return PinSpec(
        name=str(data["name"]),
        direction=direction,
        data_type=str(data.get("data_type", "float")),
        default=data.get("default"),
    )


def _template_to_dict(tmpl: BlockTemplate) -> dict[str, Any]:
    return {
        "template_id": tmpl.template_id,
        "library": tmpl.library,
        "description": tmpl.description,
        "pins": [_pin_to_dict(p) for p in tmpl.pins],
        "params": copy.deepcopy(tmpl.params),
        "body": tmpl.body,
    }


def _template_from_dict(tid: str, data: Mapping[str, Any]) -> BlockTemplate:
    raw_pins = data.get("pins") or []
    if not isinstance(raw_pins, list):
        raise ValueError(f"template {tid!r} 'pins' must be a list")
    pins = [_pin_from_dict(p, i) for i, p in enumerate(raw_pins)]
    raw_params = data.get("params") or {}
    if not isinstance(raw_params, Mapping):
        raise ValueError(f"template {tid!r} 'params' must be a mapping")
    return BlockTemplate(
        template_id=tid,
        library=str(data.get("library", "user")),
        description=str(data.get("description", "")),
        pins=pins,
        params=dict(raw_params),
        body=str(data.get("body", "")),
        is_builtin=False,
    )


def _instance_to_dict(inst: BlockInstance) -> dict[str, Any]:
    d: dict[str, Any] = {
        "template_id": inst.template_id,
        "library": inst.library,
        "params": copy.deepcopy(inst.params),
    }
    if inst.x != 0.0 or inst.y != 0.0:
        d["x"] = inst.x
        d["y"] = inst.y
    return d


def _instance_from_dict(iid: str, data: Mapping[str, Any]) -> BlockInstance:
    for key in ("template_id", "library"):
        if key not in data:
            raise ValueError(f"instance {iid!r} missing required key {key!r}")
    raw_params = data.get("params") or {}
    if not isinstance(raw_params, Mapping):
        raise ValueError(f"instance {iid!r} 'params' must be a mapping")
    return BlockInstance(
        instance_id=iid,
        template_id=str(data["template_id"]),
        library=str(data["library"]),
        params=dict(raw_params),
        x=float(data.get("x", 0.0)),
        y=float(data.get("y", 0.0)),
    )


def _wire_to_dict(wire: Wire) -> dict[str, Any]:
    return {
        "src_instance": wire.src_instance,
        "src_pin": wire.src_pin,
        "dst_instance": wire.dst_instance,
        "dst_pin": wire.dst_pin,
    }


def _wire_from_dict(data: Mapping[str, Any], idx: int) -> Wire:
    for key in ("src_instance", "src_pin", "dst_instance", "dst_pin"):
        if key not in data:
            raise ValueError(f"wires[{idx}] missing required key {key!r}")
    return Wire(
        src_instance=str(data["src_instance"]),
        src_pin=str(data["src_pin"]),
        dst_instance=str(data["dst_instance"]),
        dst_pin=str(data["dst_pin"]),
    )


# ---------------------------------------------------------------------------
# Public round-trip: program_to_dict / program_from_dict
# ---------------------------------------------------------------------------


def program_to_dict(program: Program) -> dict[str, Any]:
    """Serialise *program* to a YAML-shaped dict.

    Pass the result directly to ``yaml.safe_dump`` for YAML output.
    Built-in templates are referenced by (library, template_id) only and are
    **not** embedded; user templates are stored under ``user_templates``.
    """
    result: dict[str, Any] = {"version": program.version}
    if program.user_templates:
        result["user_templates"] = {
            tid: _template_to_dict(tmpl)
            for tid, tmpl in program.user_templates.items()
        }
    result["instances"] = {
        iid: _instance_to_dict(inst)
        for iid, inst in program.instances.items()
    }
    result["wires"] = [_wire_to_dict(w) for w in program.wires]
    result["execution_order"] = list(program.execution_order)
    return result


def program_from_dict(data: Mapping[str, Any]) -> Program:
    """Load and validate a Program from a YAML-shaped dict.

    Raises ``ValueError`` for structural violations (missing required keys,
    unknown execution_order entries, conflicting wire drivers, …).
    If ``execution_order`` is absent it defaults to instance insertion order.
    """
    if not isinstance(data, Mapping):
        raise ValueError("program data must be a mapping")

    version = str(data.get("version", "1.0"))

    raw_utemplates = data.get("user_templates") or {}
    if not isinstance(raw_utemplates, Mapping):
        raise ValueError("'user_templates' must be a mapping")
    user_templates: dict[str, BlockTemplate] = {}
    for tid, tdata in raw_utemplates.items():
        if not isinstance(tdata, Mapping):
            raise ValueError(f"user_templates[{tid!r}] must be a mapping")
        user_templates[str(tid)] = _template_from_dict(str(tid), tdata)

    raw_instances = data.get("instances") or {}
    if not isinstance(raw_instances, Mapping):
        raise ValueError("'instances' must be a mapping")
    instances: dict[str, BlockInstance] = {}
    for iid, idata in raw_instances.items():
        if not isinstance(idata, Mapping):
            raise ValueError(f"instances[{iid!r}] must be a mapping")
        instances[str(iid)] = _instance_from_dict(str(iid), idata)

    raw_wires = data.get("wires") or []
    if not isinstance(raw_wires, list):
        raise ValueError("'wires' must be a list")
    wires = [_wire_from_dict(w, i) for i, w in enumerate(raw_wires)]

    raw_order = data.get("execution_order")
    if raw_order is None:
        execution_order = list(instances.keys())
    else:
        if not isinstance(raw_order, list):
            raise ValueError("'execution_order' must be a list")
        execution_order = [str(x) for x in raw_order]

    program = Program(
        instances=instances,
        wires=wires,
        execution_order=execution_order,
        user_templates=user_templates,
        version=version,
    )
    validate_program(program)
    return program


__all__ = [
    "place_block",
    "program_from_dict",
    "program_to_dict",
    "reset_instance",
    "validate_program",
]
