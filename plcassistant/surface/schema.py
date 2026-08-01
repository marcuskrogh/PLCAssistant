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
    DEFAULT_LEGACY_PROGRAM_ID,
    MAIN_TASK_ID,
    PinDirection,
    PinSpec,
    Program,
    SoftPlcProject,
    Task,
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
        equation=copy.deepcopy(template.body),
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
        equation=copy.deepcopy(template.body),
        x=instance.x,
        y=instance.y,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


# Pin names owned by the fixed mode/safety shell.  They must be fed from the
# scan context (e.g. pump permit), never from another block via a wire.
_SHELL_OWNED_IN_PINS: frozenset[str] = frozenset({"running"})


def validate_program(program: Program) -> None:
    """Validate structural consistency of *program*.

    Raises ``ValueError`` with a descriptive message on the first violation:

    * Each instance has non-empty ``instance_id``, ``template_id``, ``library``;
      the dict key must match ``instance_id``.
    * ``execution_order`` entries exist in ``instances``; no duplicates.
    * Wire ``src_instance`` / ``dst_instance`` exist in ``instances``.
    * At most one wire drives a given ``(dst_instance, dst_pin)`` pair.
    * No wire drives a shell-owned IN pin (currently ``running``).
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
        if wire.dst_pin in _SHELL_OWNED_IN_PINS:
            raise ValueError(
                f"wire cannot drive shell-owned pin {wire.dst_pin!r} on "
                f"instance {wire.dst_instance!r}; that pin is fed by the "
                f"fixed mode/safety shell via context"
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
    library = str(data.get("library", "user"))
    if library == "builtin":
        raise ValueError(
            f"user_templates[{tid!r}] cannot use library='builtin'; "
            "built-in templates stay stock and are not embedded in the program"
        )
    return BlockTemplate(
        template_id=tid,
        library=library,
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
    if inst.equation:
        d["equation"] = inst.equation
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
        equation=str(data.get("equation", "")),
        x=float(data.get("x", 0.0)),
        y=float(data.get("y", 0.0)),
    )


def _migrate_instance_to_pid(inst: BlockInstance) -> BlockInstance:
    """Auto-migrate legacy level_pi/flow_pi blocks to placed PID copies."""
    from plcassistant.surface.builtin import (
        PID_EQUATION,
        PID_TEMPLATE_ID,
        pid_default_params,
    )

    if inst.library != "builtin":
        return inst

    hold_when_stopped: bool | None = None
    if inst.template_id == "level_pi":
        hold_when_stopped = True
    elif inst.template_id == "flow_pi":
        hold_when_stopped = False
    elif inst.template_id != PID_TEMPLATE_ID:
        return inst

    params = pid_default_params()
    params.update(copy.deepcopy(inst.params))
    if hold_when_stopped is not None:
        params["hold_when_stopped"] = hold_when_stopped
    return BlockInstance(
        instance_id=inst.instance_id,
        template_id=PID_TEMPLATE_ID,
        library="builtin",
        params=params,
        equation=inst.equation or PID_EQUATION,
        x=inst.x,
        y=inst.y,
    )


def migrate_program_to_pid(program: Program) -> Program:
    """Return *program* with legacy built-in PI instances rewritten to PID."""
    migrated = {
        iid: _migrate_instance_to_pid(inst)
        for iid, inst in program.instances.items()
    }
    if all(migrated[iid] is program.instances[iid] for iid in program.instances):
        return program
    return Program(
        name=program.name,
        description=program.description,
        instances=migrated,
        wires=list(program.wires),
        execution_order=list(program.execution_order),
        user_templates=dict(program.user_templates),
        version=program.version,
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
    if program.name:
        result["name"] = program.name
    if program.description:
        result["description"] = program.description
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
    name = str(data.get("name", ""))
    description = str(data.get("description", ""))

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
        name=name,
        description=description,
        instances=instances,
        wires=wires,
        execution_order=execution_order,
        user_templates=user_templates,
        version=version,
    )
    program = migrate_program_to_pid(program)
    validate_program(program)
    return program


# ---------------------------------------------------------------------------
# Soft-PLC project (SWD-182): tasks, programs, legacy migration
# ---------------------------------------------------------------------------


def is_legacy_program_dict(data: Mapping[str, Any]) -> bool:
    """Return True when *data* is a flat v1 Program dict (no project envelope)."""
    if not isinstance(data, Mapping):
        return False
    if "tasks" in data or "programs" in data:
        return False
    return "instances" in data or data.get("version", "1.0") == "1.0"


def migrate_legacy_program_dict(
    data: Mapping[str, Any],
    *,
    program_id: str = DEFAULT_LEGACY_PROGRAM_ID,
    task_id: str = MAIN_TASK_ID,
    priority: int = 1,
) -> dict[str, Any]:
    """Wrap a flat Program dict in a Soft-PLC project with one Main Task."""
    program = program_from_dict(data)
    return {
        "version": "2.0",
        "scan_period_s": 0.1,
        "programs": {program_id: program_to_dict(program)},
        "tasks": [{"id": task_id, "priority": priority, "programs": [program_id]}],
    }


def validate_project(project: SoftPlcProject) -> None:
    """Validate project structure.

    Raises ``ValueError`` on:

    * Unknown program ids referenced by Tasks.
    * A Program scheduled on more than one Task.
    * Duplicate Task ids or invalid Task fields.
    """
    if project.scan_period_s <= 0:
        raise ValueError("scan_period_s must be positive")

    seen_tasks: set[str] = set()
    program_to_task: dict[str, str] = {}

    for task in project.tasks:
        if not task.task_id:
            raise ValueError("task id must be non-empty")
        if task.task_id in seen_tasks:
            raise ValueError(f"duplicate task id {task.task_id!r}")
        seen_tasks.add(task.task_id)

        for prog_id in task.programs:
            if not prog_id:
                raise ValueError(f"task {task.task_id!r} has empty program id")
            if prog_id not in project.programs:
                raise ValueError(
                    f"task {task.task_id!r} references unknown program {prog_id!r}"
                )
            if prog_id in program_to_task:
                raise ValueError(
                    f"program {prog_id!r} is scheduled on tasks "
                    f"{program_to_task[prog_id]!r} and {task.task_id!r}"
                )
            program_to_task[prog_id] = task.task_id

    for prog_id, prog in project.programs.items():
        if not prog_id:
            raise ValueError("program id must be non-empty")
        validate_program(prog)


def project_to_dict(project: SoftPlcProject) -> dict[str, Any]:
    """Serialise *project* to a YAML/JSON-shaped dict."""
    return {
        "version": project.version,
        "scan_period_s": project.scan_period_s,
        "programs": {
            pid: program_to_dict(prog) for pid, prog in project.programs.items()
        },
        "tasks": [
            {
                "id": task.task_id,
                "priority": task.priority,
                "description": task.description,
                "programs": list(task.programs),
            }
            for task in project.tasks
        ],
    }


def project_from_dict(data: Mapping[str, Any]) -> SoftPlcProject:
    """Load a SoftPlcProject, auto-migrating legacy flat Program YAML."""
    if not isinstance(data, Mapping):
        raise ValueError("project data must be a mapping")

    if is_legacy_program_dict(data):
        data = migrate_legacy_program_dict(data)

    version = str(data.get("version", "2.0"))
    scan_period_s = float(data.get("scan_period_s", 0.1))

    raw_programs = data.get("programs") or {}
    if not isinstance(raw_programs, Mapping):
        raise ValueError("'programs' must be a mapping")
    programs: dict[str, Program] = {}
    for pid, pdata in raw_programs.items():
        if not isinstance(pdata, Mapping):
            raise ValueError(f"programs[{pid!r}] must be a mapping")
        programs[str(pid)] = program_from_dict(pdata)

    raw_tasks = data.get("tasks") or []
    if not isinstance(raw_tasks, list):
        raise ValueError("'tasks' must be a list")
    tasks: list[Task] = []
    for idx, tdata in enumerate(raw_tasks):
        if not isinstance(tdata, Mapping):
            raise ValueError(f"tasks[{idx}] must be a mapping")
        for key in ("id", "priority"):
            if key not in tdata:
                raise ValueError(f"tasks[{idx}] missing required key {key!r}")
        raw_progs = tdata.get("programs") or []
        if not isinstance(raw_progs, list):
            raise ValueError(f"tasks[{idx}] 'programs' must be a list")
        tasks.append(
            Task(
                task_id=str(tdata["id"]),
                priority=int(tdata["priority"]),
                programs=[str(p) for p in raw_progs],
                description=str(tdata.get("description", "")),
            )
        )

    project = SoftPlcProject(
        programs=programs,
        tasks=tasks,
        scan_period_s=scan_period_s,
        version=version,
    )
    validate_project(project)
    return project


def project_structure_signature(project: SoftPlcProject) -> tuple:
    """Hashable signature of Task/Program membership (structure-only)."""
    task_sig = tuple(
        sorted(
            (t.task_id, t.priority, tuple(t.programs)) for t in project.tasks
        )
    )
    return (tuple(sorted(project.programs.keys())), task_sig)


def classify_project_apply(
    old: SoftPlcProject | None,
    new: SoftPlcProject,
) -> str:
    """Classify apply mode: ``restart`` for structure changes, else ``hot``.

    Structure covers Task ids/priorities/call lists and the set of program ids.
    Program body changes (instances, wires, params) within unchanged structure
    qualify for ``hot``.
    """
    if old is None:
        return "restart"
    if project_structure_signature(old) != project_structure_signature(new):
        return "restart"
    return "hot"


def main_program(project: SoftPlcProject) -> Program | None:
    """Return the Program on ``MAIN_TASK_ID``, or the first scheduled Program."""
    for task in project.tasks:
        if task.task_id == MAIN_TASK_ID and task.programs:
            return project.programs.get(task.programs[0])
    for task in sorted(project.tasks, key=lambda t: t.priority):
        for prog_id in task.programs:
            prog = project.programs.get(prog_id)
            if prog is not None:
                return prog
    return None


def scheduled_programs(
    project: SoftPlcProject,
) -> list[tuple[Task, str, Program]]:
    """Programs to execute this scan: Tasks by priority, programs in call order."""
    result: list[tuple[Task, str, Program]] = []
    for task in sorted(project.tasks, key=lambda t: (t.priority, t.task_id)):
        for prog_id in task.programs:
            prog = project.programs.get(prog_id)
            if prog is not None:
                result.append((task, prog_id, prog))
    return result


__all__ = [
    "classify_project_apply",
    "is_legacy_program_dict",
    "main_program",
    "migrate_legacy_program_dict",
    "migrate_program_to_pid",
    "place_block",
    "program_from_dict",
    "program_to_dict",
    "project_from_dict",
    "project_structure_signature",
    "project_to_dict",
    "reset_instance",
    "scheduled_programs",
    "validate_program",
    "validate_project",
]
