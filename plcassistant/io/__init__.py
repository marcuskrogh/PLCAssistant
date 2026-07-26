"""Soft-PLC scan-cycle I/O image, quality, bindings, and thin-integration stub.

See docs/io/01-image-quality.md, docs/io/02-binding-model.md, and
docs/io/03-thin-integration-stub.md. No Home Assistant dependency.
"""

from plcassistant.io.binding import Binding, BindingTable, Direction, TagDecl
from plcassistant.io.image import IoImage, TagSnapshot
from plcassistant.io.integration import (
    EntitySample,
    MockEntityStore,
    ThinIntegrationStub,
)
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
    "EntitySample",
    "IoImage",
    "MockEntityStore",
    "TagDecl",
    "TagSnapshot",
    "ThinIntegrationStub",
    "QualityStatus",
    "ReasonCode",
    "TagQuality",
    "collapse_quality",
    "is_good",
]
