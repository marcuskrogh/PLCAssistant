"""Leaf helper: declare default Soft-PLC packaging tags on an IoImage.

Kept separate from ``server`` / ``runtime`` so HTTP and scan code share one
constructor without an import cycle.
"""

from __future__ import annotations

from plcassistant.io.image import IoImage
from plcassistant.io.mqtt_entity_bridge import default_wedge_binding_config


def declare_default_image(image: IoImage | None = None) -> IoImage:
    """Declare default packaging tags on an image."""
    if image is None:
        image = IoImage()
    cfg = default_wedge_binding_config()
    for name, meta in cfg["tags"].items():
        if name not in image.names():
            image.declare(name, default=meta.get("default", 0.0))
    return image


__all__ = ["declare_default_image"]
