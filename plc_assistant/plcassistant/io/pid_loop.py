"""PID loop SP-source modes and faceplate helpers (SWD-183).

Industrial SP-source pattern (not classic CV Manual):
Manual / Automatic / Remote select which source writes the active SP tag.
Writing a Manual or Remote SP auto-flips mode; Automatic requires explicit mode.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class SpSourceMode(str, Enum):
    """Who owns the active setpoint while the PID still computes CV."""

    MANUAL = "manual"
    AUTOMATIC = "automatic"
    REMOTE = "remote"

    @classmethod
    def parse(cls, value: Any) -> SpSourceMode:
        if isinstance(value, cls):
            return value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            codes = {0: cls.MANUAL, 1: cls.AUTOMATIC, 2: cls.REMOTE}
            code = int(value)
            if code not in codes:
                raise ValueError(f"invalid SP source mode code: {value!r}")
            return codes[code]
        key = str(value or "").strip().lower()
        aliases = {
            "man": cls.MANUAL,
            "manual": cls.MANUAL,
            "auto": cls.AUTOMATIC,
            "automatic": cls.AUTOMATIC,
            "rem": cls.REMOTE,
            "remote": cls.REMOTE,
            "0": cls.MANUAL,
            "1": cls.AUTOMATIC,
            "2": cls.REMOTE,
        }
        if key not in aliases:
            raise ValueError(f"invalid SP source mode: {value!r}")
        return aliases[key]

    @property
    def code(self) -> int:
        return {self.MANUAL: 0, self.AUTOMATIC: 1, self.REMOTE: 2}[self]


@dataclass(frozen=True)
class PidLoopTags:
    """Datablock tag names for one PID faceplate / compound entity."""

    loop_id: str
    pv: str
    sp: str
    sp_man: str
    sp_auto: str
    sp_rem: str
    mode: str
    cv: str
    kp: str
    ki: str
    kd: str

    @property
    def entity_object_id(self) -> str:
        """HA object_id suffix, e.g. ``pid_level`` → ``sensor.plcassistant_pid_level``."""
        return f"pid_{self.loop_id}"


# Demo tank loops (stable ids for Lovelace + Soft-PLC).
LEVEL_LOOP = PidLoopTags(
    loop_id="level",
    pv="LT_TANK",
    sp="SP_LEVEL",
    sp_man="SP_LEVEL_MAN",
    sp_auto="SP_LEVEL_AUTO",
    sp_rem="SP_LEVEL_REM",
    mode="LEVEL_MODE",
    cv="SP_FLOW",  # level loop CV is flow SP (cascade)
    kp="LEVEL_KP",
    ki="LEVEL_KI",
    kd="LEVEL_KD",
)

FLOW_LOOP = PidLoopTags(
    loop_id="flow",
    pv="FT_INLET",
    sp="SP_FLOW",
    sp_man="SP_FLOW_MAN",
    sp_auto="SP_FLOW_AUTO",
    sp_rem="SP_FLOW_REM",
    mode="FLOW_MODE",
    cv="CMD_SPEED",
    kp="FLOW_KP",
    ki="FLOW_KI",
    kd="FLOW_KD",
)

DEMO_PID_LOOPS: tuple[PidLoopTags, ...] = (LEVEL_LOOP, FLOW_LOOP)


def select_active_sp(
    mode: SpSourceMode | str,
    *,
    sp_man: float,
    sp_auto: float,
    sp_rem: float,
) -> float:
    """Return the active SP for the given SP-source mode."""
    resolved = SpSourceMode.parse(mode)
    if resolved is SpSourceMode.MANUAL:
        return float(sp_man)
    if resolved is SpSourceMode.REMOTE:
        return float(sp_rem)
    return float(sp_auto)


def mode_after_sp_source_write(
    source: SpSourceMode | str,
    *,
    current_mode: SpSourceMode | str | None = None,
) -> SpSourceMode:
    """Mode after an HMI/entity write to a source SP tag.

    Manual or Remote writes auto-flip to that mode. Automatic SP writes do
    **not** change mode (Auto must be set explicitly).
    """
    del current_mode  # reserved for future bumpless / tracking rules
    resolved = SpSourceMode.parse(source)
    if resolved is SpSourceMode.AUTOMATIC:
        # Writing the AUTO source does not flip mode.
        raise ValueError("writing automatic SP does not change mode; set mode explicitly")
    return resolved


def apply_explicit_mode(mode: SpSourceMode | str) -> SpSourceMode:
    """Operator/system explicitly sets the faceplate mode."""
    return SpSourceMode.parse(mode)


def apply_sp_write(
    *,
    source: SpSourceMode | str,
    value: float,
    current_mode: SpSourceMode | str,
    sp_man: float,
    sp_auto: float,
    sp_rem: float,
) -> dict[str, Any]:
    """Apply a source-SP write; auto-flip mode for MAN/REM.

    Returns updated ``mode``, source SPs, and selected ``sp``.
    """
    src = SpSourceMode.parse(source)
    mode = SpSourceMode.parse(current_mode)
    man, auto, rem = float(sp_man), float(sp_auto), float(sp_rem)
    if src is SpSourceMode.MANUAL:
        man = float(value)
        mode = SpSourceMode.MANUAL
    elif src is SpSourceMode.REMOTE:
        rem = float(value)
        mode = SpSourceMode.REMOTE
    else:
        auto = float(value)
        # mode unchanged
    sp = select_active_sp(mode, sp_man=man, sp_auto=auto, sp_rem=rem)
    return {
        "mode": mode.value,
        "sp_man": man,
        "sp_auto": auto,
        "sp_rem": rem,
        "sp": sp,
    }


def faceplate_from_image_tags(
    tags: PidLoopTags,
    values: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a climate-like faceplate dict from a tag value map."""
    mode = SpSourceMode.parse(values.get(tags.mode, SpSourceMode.MANUAL))
    man = float(values.get(tags.sp_man, 0.0) or 0.0)
    auto = float(values.get(tags.sp_auto, 0.0) or 0.0)
    rem = float(values.get(tags.sp_rem, 0.0) or 0.0)
    sp = select_active_sp(mode, sp_man=man, sp_auto=auto, sp_rem=rem)
    return {
        "loop_id": tags.loop_id,
        "mode": mode.value,
        "pv": values.get(tags.pv),
        "sp": sp,
        "sp_man": man,
        "sp_auto": auto,
        "sp_rem": rem,
        "cv": values.get(tags.cv),
        "kp": values.get(tags.kp),
        "ki": values.get(tags.ki),
        "kd": values.get(tags.kd),
        "tags": {
            "pv": tags.pv,
            "sp": tags.sp,
            "sp_man": tags.sp_man,
            "sp_auto": tags.sp_auto,
            "sp_rem": tags.sp_rem,
            "mode": tags.mode,
            "cv": tags.cv,
        },
    }


__all__ = [
    "DEMO_PID_LOOPS",
    "FLOW_LOOP",
    "LEVEL_LOOP",
    "PidLoopTags",
    "SpSourceMode",
    "apply_explicit_mode",
    "apply_sp_write",
    "faceplate_from_image_tags",
    "mode_after_sp_source_write",
    "select_active_sp",
]
