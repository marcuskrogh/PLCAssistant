"""Per-tag quality for the Soft-PLC I/O image (docs/io/01-image-quality.md)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class QualityStatus(str, Enum):
    """OPC-style quality trio carried on every image tag."""

    GOOD = "GOOD"
    UNCERTAIN = "UNCERTAIN"
    BAD = "BAD"


class ReasonCode(str, Enum):
    """Minimal reason set when status is not GOOD."""

    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
    STALE = "stale"
    FAULT = "fault"


@dataclass(frozen=True)
class TagQuality:
    """Status + optional reason for one tag on the I/O image."""

    status: QualityStatus
    reason: ReasonCode | None = None

    def __post_init__(self) -> None:
        if self.status is QualityStatus.GOOD:
            if self.reason is not None:
                raise ValueError("GOOD quality must not carry a reason code")
        elif self.reason is None:
            raise ValueError(f"{self.status.value} quality requires a reason code")


def is_good(quality: TagQuality | QualityStatus) -> bool:
    """True only when status is GOOD (safety default collapse)."""
    if isinstance(quality, TagQuality):
        return quality.status is QualityStatus.GOOD
    return quality is QualityStatus.GOOD


def collapse_quality(quality: TagQuality | QualityStatus) -> bool:
    """Collapse quality to good/bad for safety: True iff GOOD."""
    return is_good(quality)
