"""Soft-PLC scan-cycle I/O image, quality, and bindings (SWD-95 / SWD-98 / SWD-86).

See docs/io/01-image-quality.md and docs/io/02-binding-model.md.
No Home Assistant dependency.
"""

from plcassistant.io.binding import Binding, BindingTable, Direction, TagDecl
from plcassistant.io.image import IoImage, TagSnapshot
from plcassistant.io.quality import (
    QualityStatus,
    ReasonCode,
    TagQuality,
    collapse_quality,
    is_good,
)

__all__ = [
    "Binding",
    "BindingTable",
    "Direction",
    "IoImage",
    "TagDecl",
    "TagSnapshot",
    "QualityStatus",
    "ReasonCode",
    "TagQuality",
    "collapse_quality",
    "is_good",
]
