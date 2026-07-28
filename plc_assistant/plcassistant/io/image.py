"""Scan-cycle I/O image with per-tag quality and last-good retention."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

from plcassistant.io.quality import QualityStatus, ReasonCode, TagQuality


@dataclass(frozen=True)
class TagSnapshot:
    """Immutable view of one tag for flush / diagnostics."""

    name: str
    value: Any
    quality: TagQuality
    last_good: Any | None
    """Last GOOD sample, or None before the first GOOD."""

    default: Any


@dataclass
class _TagSlot:
    name: str
    default: Any
    value: Any
    quality: TagQuality
    last_good: Any | None = None
    """Retained GOOD sample; None until the first GOOD apply_input."""

    is_output: bool = False
    """True after logic has written via set_output (eligible for OUT flush)."""


class IoImage:
    """In-memory Soft-PLC I/O image for one scan cycle.

    Typical scan use (bindings come later)::

        # setup
        image.declare("LT_TANK", default=0.0)
        image.declare("CMD_SPEED", default=0.0)

        # scan start — IN
        image.begin_inputs()
        image.apply_input("LT_TANK", 0.2, QualityStatus.GOOD)

        # scan body
        level = image.get_value("LT_TANK")
        image.set_output("CMD_SPEED", 40.0)

        # scan end — OUT
        flush = image.snapshot_outputs()
    """

    def __init__(self) -> None:
        self._tags: dict[str, _TagSlot] = {}

    def declare(self, name: str, *, default: Any) -> None:
        """Register a tag; initial value is default with BAD / unavailable."""
        if name in self._tags:
            raise ValueError(f"tag already declared: {name!r}")
        self._tags[name] = _TagSlot(
            name=name,
            default=default,
            value=default,
            quality=TagQuality(QualityStatus.BAD, ReasonCode.UNAVAILABLE),
            last_good=None,
        )

    def begin_inputs(self) -> None:
        """Mark scan-start IN phase (no-op seam for bindings / scanners)."""

    def apply_input(
        self,
        name: str,
        value: Any,
        status: QualityStatus,
        reason: ReasonCode | None = None,
    ) -> None:
        """Apply an IN sample at scan start per last-good / default rules."""
        slot = self._require(name)
        if status is QualityStatus.GOOD and isinstance(value, (int, float)):
            if not math.isfinite(float(value)):
                # Reject non-finite GOOD: demote to BAD / fault (keep last-good).
                status = QualityStatus.BAD
                reason = ReasonCode.FAULT
        quality = TagQuality(status, reason)
        if status is QualityStatus.GOOD:
            slot.value = value
            slot.last_good = value
            slot.quality = quality
            return
        # Non-GOOD: keep last good (or default if never GOOD); update quality only.
        if slot.last_good is not None:
            slot.value = slot.last_good
        else:
            slot.value = slot.default
        slot.quality = quality

    def get_value(self, name: str) -> Any:
        """Value presented to logic (last good or default when quality ≠ GOOD)."""
        return self._require(name).value

    def get_quality(self, name: str) -> TagQuality:
        return self._require(name).quality

    def get(self, name: str) -> tuple[Any, TagQuality]:
        slot = self._require(name)
        return slot.value, slot.quality

    def set_output(self, name: str, value: Any) -> None:
        """Logic write for OUT flush; marks the tag as an output with GOOD quality.

        Non-finite numeric values (nan/inf) are demoted to ``BAD`` / ``fault``
        (same as ``apply_input``): last-good or default is retained; the write
        is not published as GOOD.
        """
        slot = self._require(name)
        slot.is_output = True
        if isinstance(value, (int, float)) and not math.isfinite(float(value)):
            slot.quality = TagQuality(QualityStatus.BAD, ReasonCode.FAULT)
            if slot.last_good is not None:
                slot.value = slot.last_good
            else:
                slot.value = slot.default
            return
        slot.value = value
        slot.last_good = value
        slot.quality = TagQuality(QualityStatus.GOOD)

    def snapshot_outputs(self) -> dict[str, Any]:
        """Values for tags written as outputs this image lifetime (scan-end flush)."""
        return {name: slot.value for name, slot in self._tags.items() if slot.is_output}

    def snapshot(self) -> Mapping[str, TagSnapshot]:
        """Full image snapshot (diagnostics / tests)."""
        return {
            name: TagSnapshot(
                name=name,
                value=slot.value,
                quality=slot.quality,
                last_good=slot.last_good,
                default=slot.default,
            )
            for name, slot in self._tags.items()
        }

    def names(self) -> tuple[str, ...]:
        return tuple(self._tags)

    def _require(self, name: str) -> _TagSlot:
        try:
            return self._tags[name]
        except KeyError as exc:
            raise KeyError(f"unknown tag: {name!r}") from exc
