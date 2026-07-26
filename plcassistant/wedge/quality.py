"""PV quality helpers bridging wedge runtime to ``plcassistant.io`` quality.

Numeric ``pv_ok`` remains for NaN / negative / None checks. Those failures are
mapped to ``TagQuality(BAD, …)`` so safety/HMI consume per-tag quality only —
no separate ``*_BAD`` tags (docs/io/01-image-quality.md, SWD-96).
"""

from __future__ import annotations

from typing import Optional

from plcassistant.io.quality import (
    QualityStatus,
    ReasonCode,
    TagQuality,
    is_good,
)


def pv_ok(value: Optional[float]) -> bool:
    """True when a PV is available and usable for trips / control.

    BAD when ``None``, non-finite (NaN / ±inf), or strictly negative.
    """
    if value is None:
        return False
    if value != value:  # NaN
        return False
    if value in (float("inf"), float("-inf")):
        return False
    return value >= 0.0


def quality_from_pv(value: Optional[float]) -> TagQuality:
    """Synthesize tag quality from a raw numeric sample."""
    if value is None:
        return TagQuality(QualityStatus.BAD, ReasonCode.UNAVAILABLE)
    if value != value or value in (float("inf"), float("-inf")):
        return TagQuality(QualityStatus.BAD, ReasonCode.FAULT)
    if value < 0.0:
        return TagQuality(QualityStatus.BAD, ReasonCode.FAULT)
    return TagQuality(QualityStatus.GOOD)


def coerce_tag_quality(quality: TagQuality | QualityStatus) -> TagQuality:
    """Normalize ``TagQuality`` or bare ``QualityStatus`` to ``TagQuality``."""
    if isinstance(quality, TagQuality):
        return quality
    if quality is QualityStatus.GOOD:
        return TagQuality(QualityStatus.GOOD)
    return TagQuality(quality, ReasonCode.FAULT)


def resolve_tag_quality(
    value: Optional[float],
    quality: TagQuality | QualityStatus | None = None,
) -> TagQuality:
    """Resolve effective quality: explicit non-GOOD wins; else synthesize from PV.

    Safety collapses with ``not is_good(...)``. A GOOD (or omitted) quality still
    demotes when ``pv_ok`` fails (None / NaN / negative).
    """
    if quality is not None:
        forced = coerce_tag_quality(quality)
        if not is_good(forced):
            return forced
    return quality_from_pv(value)


__all__ = [
    "QualityStatus",
    "ReasonCode",
    "TagQuality",
    "coerce_tag_quality",
    "is_good",
    "pv_ok",
    "quality_from_pv",
    "resolve_tag_quality",
]
