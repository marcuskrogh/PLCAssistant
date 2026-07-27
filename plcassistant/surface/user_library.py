"""User block library CRUD API (SWD-114).

Provides helpers for adding, updating, deleting, and listing user-defined
BlockTemplates on a Program.  Built-in templates (is_builtin=True) are never
touched by these helpers.

User templates are stored in ``Program.user_templates`` (dict keyed by
template_id) and round-tripped via the standard YAML schema.

Registration into TemplateLibrary
----------------------------------
Call ``register_user_templates(library, program)`` after loading a program so
that the runtime can resolve user blocks the same way built-ins are resolved
(via ``library.get``).  The runtime also falls back to
``program.user_templates`` directly, so registration is optional but
recommended for consistency.

No Home Assistant dependency; no hard-wired I/O.
"""

from __future__ import annotations

import copy
from typing import Any

from plcassistant.surface.model import (
    BlockTemplate,
    PinDirection,
    PinSpec,
    Program,
    TemplateLibrary,
)


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------


def add_user_template(program: Program, template: BlockTemplate) -> None:
    """Add or overwrite a user template in *program*.

    Raises ``ValueError`` if *template* is a built-in (``is_builtin=True``):
    built-in templates are stock and must remain in the global
    ``TemplateLibrary``; they must not be stored as user templates.

    The template is deep-copied before storage so that callers cannot
    accidentally mutate the stored entry.
    """
    if template.is_builtin:
        raise ValueError(
            f"template {template.template_id!r} is a built-in (is_builtin=True); "
            "built-in templates cannot be stored as user templates"
        )
    program.user_templates[template.template_id] = copy.deepcopy(template)


def remove_user_template(program: Program, template_id: str) -> None:
    """Remove a user template from *program*.

    Raises ``KeyError`` if *template_id* does not exist in
    ``program.user_templates``.  Does not affect placed instances referencing
    the removed template (those remain; the template is simply no longer in
    the library).
    """
    if template_id not in program.user_templates:
        raise KeyError(
            f"user template {template_id!r} not found in program.user_templates"
        )
    del program.user_templates[template_id]


def get_user_template(program: Program, template_id: str) -> BlockTemplate | None:
    """Return the user template for *template_id* or ``None`` if absent."""
    return program.user_templates.get(template_id)


def list_user_templates(program: Program) -> list[BlockTemplate]:
    """Return all user templates stored in *program* (in insertion order)."""
    return list(program.user_templates.values())


# ---------------------------------------------------------------------------
# Registration helper (optional: wires user templates into TemplateLibrary)
# ---------------------------------------------------------------------------


def register_user_templates(
    library: TemplateLibrary,
    program: Program,
) -> None:
    """Register all user templates from *program* into *library*.

    Calling this after ``program_from_dict`` ensures that the runtime can
    resolve user templates via ``library.get`` just like built-ins.  The
    runtime also falls back to ``program.user_templates`` directly, so this
    is not strictly required but is the recommended path for the App loader.

    Each template is registered with its declared ``library`` attribute and
    ``template_id`` as the key.
    """
    for tmpl in program.user_templates.values():
        library.register(tmpl)


# ---------------------------------------------------------------------------
# Convenience constructor
# ---------------------------------------------------------------------------


def make_user_template(
    template_id: str,
    body: str,
    *,
    library: str = "user",
    description: str = "",
    pins: list[dict[str, Any]] | None = None,
    params: dict[str, Any] | None = None,
) -> BlockTemplate:
    """Construct a user BlockTemplate from primitive inputs.

    ``pins`` (optional) is a list of dicts with keys ``name``, ``direction``
    (``"IN"`` or ``"OUT"``), optional ``data_type`` (default ``"float"``),
    and optional ``default``.

    Example::

        tmpl = make_user_template(
            "my_gain",
            body="out = x * gain",
            pins=[
                {"name": "x",   "direction": "IN",  "data_type": "float", "default": 0.0},
                {"name": "out", "direction": "OUT", "data_type": "float"},
            ],
            params={"gain": 1.0},
        )
    """
    pin_specs: list[PinSpec] = []
    for raw in pins or []:
        raw_dir = str(raw.get("direction", "IN")).upper()
        try:
            direction = PinDirection(raw_dir)
        except ValueError as exc:
            raise ValueError(
                f"pin {raw.get('name')!r} invalid direction {raw.get('direction')!r}"
            ) from exc
        pin_specs.append(
            PinSpec(
                name=str(raw["name"]),
                direction=direction,
                data_type=str(raw.get("data_type", "float")),
                default=raw.get("default"),
            )
        )
    return BlockTemplate(
        template_id=template_id,
        library=library,
        description=description,
        pins=pin_specs,
        params=copy.deepcopy(params or {}),
        body=body,
        is_builtin=False,
    )


__all__ = [
    "add_user_template",
    "get_user_template",
    "list_user_templates",
    "make_user_template",
    "register_user_templates",
    "remove_user_template",
]
