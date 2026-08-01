"""Leaf helper: declare default Soft-PLC packaging tags on an IoImage.

Kept separate from ``server`` / ``runtime`` so HTTP and scan code share one
constructor without an import cycle.
"""

from __future__ import annotations

from plcassistant.io.datablock import (
    default_program_datablock_access,
    default_tank_datablock_catalog,
    program_accessible_tags,
    union_program_access_ids,
)
from plcassistant.io.image import IoImage


def declare_default_image(image: IoImage | None = None) -> IoImage:
    """Declare tags from Programs' Datablock access (demo: tank → DB_Tank)."""
    if image is None:
        image = IoImage()
    catalog = default_tank_datablock_catalog()
    access_ids = union_program_access_ids(default_program_datablock_access())
    table = catalog.binding_table_for(access_ids)
    # Soft-PLC visibility = tags from accessible Datablocks only.
    allowed = program_accessible_tags(catalog, access_ids)
    for name, decl in table.tags.items():
        if name not in allowed:
            continue
        if name not in image.names():
            image.declare(name, default=decl.default)
    return image


__all__ = ["declare_default_image"]
