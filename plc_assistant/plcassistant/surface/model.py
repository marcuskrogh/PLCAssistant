"""Block program data model — templates, instances, pins, wires, program (SWD-119).

See docs/surface/01-block-model.md for the full contract.
No Home Assistant dependency; no hard-wired I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PinDirection(str, Enum):
    """Pin direction from the block's perspective."""

    IN = "IN"
    OUT = "OUT"


@dataclass
class PinSpec:
    """Typed connection point declared on a BlockTemplate."""

    name: str
    direction: PinDirection
    data_type: str = "float"
    default: Any = None


@dataclass
class BlockTemplate:
    """Library-held definition.

    Shipped templates (``is_builtin=True``, ``library="builtin"``) may be
    overridden via the App Library editor; Reset restores the factory copy.
    Custom templates use ``library="custom"``.  ``body`` holds the math
    equation text; placements copy it into ``BlockInstance.equation``.
    """

    template_id: str
    library: str
    description: str = ""
    pins: list[PinSpec] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    is_builtin: bool = False


@dataclass
class BlockInstance:
    """A placed copy of a template.

    Editing params or ``equation`` on an instance never affects the
    originating template.  Created by schema.place_block; reset by
    schema.reset_instance.
    """

    instance_id: str
    template_id: str
    library: str
    params: dict[str, Any] = field(default_factory=dict)
    equation: str = ""
    x: float = 0.0
    y: float = 0.0


@dataclass(frozen=True)
class Wire:
    """Directional data connection between a source pin and a destination pin."""

    src_instance: str
    src_pin: str
    dst_instance: str
    dst_pin: str


MAIN_TASK_ID = "main"
"""Canvas / API default task id for the primary scheduled program."""

DEFAULT_LEGACY_PROGRAM_ID = "main"
"""Program id assigned when auto-migrating a flat legacy Program YAML."""

DEFAULT_WEDGE_PROGRAM_ID = "tank"
"""Default wedge cascade program id under ``MAIN_TASK_ID``."""


@dataclass
class Task:
    """Soft-PLC scan task: priority-ordered pass that calls Programs in sequence.

    Lower ``priority`` values run earlier within one scan.  Tasks carry no
    per-Task interval — ``SoftPlcProject.scan_period_s`` drives ``dt``.
    """

    task_id: str
    priority: int
    programs: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class SoftPlcProject:
    """Soft-PLC project organization: Tasks schedule Programs of block instances.

    * ``programs`` — all defined Programs (scheduled or not).
    * ``tasks`` — priority-ordered Task passes; each lists program ids to call.
    * Each Program may appear on **at most one** Task; unscheduled Programs are
      defined but not executed.
    """

    programs: dict[str, Program] = field(default_factory=dict)
    tasks: list[Task] = field(default_factory=list)
    scan_period_s: float = 0.1
    version: str = "2.0"


@dataclass
class Program:
    """Complete block program: placed instances, wiring, deterministic execution order.

    Seam contract for downstream packages:

    * SWD-116 (runtime): iterate execution_order; resolve each instance via
      TemplateLibrary.get(inst.library, inst.template_id); route wires.
    * SWD-120 (canvas): round-trip via schema.program_to_dict / program_from_dict.
    * SWD-114 (user library): add user_templates; call place_block / reset_instance.
    * SWD-117 (apply policy): call program_from_dict on restart or hot-apply.
    """

    name: str = ""
    description: str = ""
    instances: dict[str, BlockInstance] = field(default_factory=dict)
    wires: list[Wire] = field(default_factory=list)
    execution_order: list[str] = field(default_factory=list)
    user_templates: dict[str, BlockTemplate] = field(default_factory=dict)
    # Soft-PLC only sees tags from these integration Datablocks (SWD-184).
    datablocks: list[str] = field(default_factory=list)
    version: str = "1.0"


class TemplateLibrary:
    """Injectable registry of block templates for the runtime and App.

    Built-in blocks (SWD-115) call register() at startup with is_builtin=True.
    User templates are re-registered from Program.user_templates on program load.
    The runtime (SWD-116) calls get() to resolve each placed instance.
    The App canvas (SWD-120) calls all_templates() to populate the block picker.
    """

    def __init__(self) -> None:
        self._templates: dict[tuple[str, str], BlockTemplate] = {}

    def register(self, template: BlockTemplate) -> None:
        """Add or overwrite an entry keyed by (library, template_id).

        Raises ``ValueError`` when a non-built-in template would overwrite an
        existing built-in at the same key (built-ins stay stock).
        """
        key = (template.library, template.template_id)
        existing = self._templates.get(key)
        if existing is not None and existing.is_builtin and not template.is_builtin:
            raise ValueError(
                f"cannot overwrite built-in template "
                f"{template.library}/{template.template_id!r} with a user template"
            )
        self._templates[key] = template

    def unregister(self, library: str, template_id: str) -> None:
        """Remove the template for (library, template_id). No-op if absent."""
        self._templates.pop((library, template_id), None)

    def get(self, library: str, template_id: str) -> BlockTemplate | None:
        """Return the template for (library, template_id) or None if absent."""
        return self._templates.get((library, template_id))

    def all_templates(self) -> list[BlockTemplate]:
        """Return all registered templates in registration order."""
        return list(self._templates.values())

    def __contains__(self, item: tuple[str, str]) -> bool:
        return item in self._templates

    def __len__(self) -> int:
        return len(self._templates)


__all__ = [
    "BlockInstance",
    "BlockTemplate",
    "DEFAULT_LEGACY_PROGRAM_ID",
    "DEFAULT_WEDGE_PROGRAM_ID",
    "MAIN_TASK_ID",
    "PinDirection",
    "PinSpec",
    "Program",
    "SoftPlcProject",
    "Task",
    "TemplateLibrary",
    "Wire",
]
