"""Soft-PLC scan-cycle I/O image and per-tag quality (SWD-95 / SWD-86).

See docs/io/01-image-quality.md. No Home Assistant dependency.
"""

from plcassistant.io.image import IoImage, TagSnapshot
from plcassistant.io.quality import (
    QualityStatus,
    ReasonCode,
    TagQuality,
    collapse_quality,
    is_good,
)

__all__ = [
    "IoImage",
    "TagSnapshot",
    "QualityStatus",
    "ReasonCode",
    "TagQuality",
    "collapse_quality",
    "is_good",
]
