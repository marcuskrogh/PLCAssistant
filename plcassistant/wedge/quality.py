"""Shared process-variable quality checks for safety and measurement views."""

from __future__ import annotations

from typing import Optional


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
