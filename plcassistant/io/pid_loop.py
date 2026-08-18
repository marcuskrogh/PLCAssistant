"""PID loop controller modes and faceplate helpers (SWD-183 / SWD-369).

DCS analog-controller modes (ISA-101 chrome, ISA-TR5.9 names):

- Manual — output Manual. Operator writes CO (Bauer ``uman``); PID ``auto`` is false.
- Automatic — local SP. Operator writes SP; PID computes CO.
- Remote — cascade/remote SP. PID computes CO; operator does not write SP or CO
  from the faceplate.

Legacy Man/Auto/Rem *SP source* tags remain on the Datablock. Manual no longer
means “a third SP while the PID still computes CO”.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Mapping


class SpSourceMode(str, Enum):
    """Controller mode: output Manual / local Auto / remote-cascade."""

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
            "cas": cls.REMOTE,
            "cascade": cls.REMOTE,
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


WriteTarget = Literal["co", "sp"]


def is_output_manual(mode: SpSourceMode | str) -> bool:
    """True when the operator supplies CO (Bauer auto=false)."""
    return SpSourceMode.parse(mode) is SpSourceMode.MANUAL


def operator_write_target(mode: SpSourceMode | str) -> WriteTarget | None:
    """Which analog the operator may set on the faceplate, or None (REM)."""
    resolved = SpSourceMode.parse(mode)
    if resolved is SpSourceMode.MANUAL:
        return "co"
    if resolved is SpSourceMode.AUTOMATIC:
        return "sp"
    return None


# Standardised PID params operators may set from the faceplate settings gear.
# Skip unused Parallel leftovers ``td`` / ``gamma``. ``form`` is display-only.
PID_OPERATOR_PARAM_KEYS: tuple[str, ...] = (
    "kp",
    "ki",
    "kd",
    "u0",
    "beta",
    "direct_acting",
    "cv_min",
    "cv_max",
    "hold_when_stopped",
    "ts",
    "tf_ts",
)
# Faceplate SP-path (not a PID equation param). 0 = instant.
PID_FACEPLATE_EXTRA_KEYS: tuple[str, ...] = ("sp_ramp_max",)
PID_FACEPLATE_PARAM_KEYS: tuple[str, ...] = (
    *PID_OPERATOR_PARAM_KEYS,
    *PID_FACEPLATE_EXTRA_KEYS,
)
PID_BOOL_PARAM_KEYS = frozenset({"direct_acting", "hold_when_stopped"})


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
    co_man: str
    kp: str
    ki: str
    kd: str
    u0: str
    beta: str
    direct_acting: str
    cv_min: str
    cv_max: str
    hold_when_stopped: str
    ts: str
    tf_ts: str
    sp_ramp_max: str

    @property
    def entity_object_id(self) -> str:
        """HA object_id suffix, e.g. ``pid_level`` → ``sensor.plcassistant_pid_level``."""
        return f"pid_{self.loop_id}"

    def operator_param_tags(self) -> dict[str, str]:
        """Map faceplate-operator param name → Datablock IN tag."""
        return {key: getattr(self, key) for key in PID_FACEPLATE_PARAM_KEYS}


# Demo tank loops (stable ids for Lovelace + Soft-PLC).
LEVEL_LOOP = PidLoopTags(
    loop_id="level",
    pv="LT_TANK",
    sp="SP_LEVEL",
    sp_man="SP_LEVEL_MAN",
    sp_auto="SP_LEVEL_REQ",
    sp_rem="SP_LEVEL_REM",
    mode="LEVEL_MODE",
    cv="SP_FLOW_AUTO",  # true level CV (not muxed active SP_FLOW) (SWD-223)
    co_man="CO_LEVEL_MAN",
    kp="LEVEL_KP",
    ki="LEVEL_KI",
    kd="LEVEL_KD",
    u0="LEVEL_U0",
    beta="LEVEL_BETA",
    direct_acting="LEVEL_DIRECT_ACTING",
    cv_min="LEVEL_CV_MIN",
    cv_max="LEVEL_CV_MAX",
    hold_when_stopped="LEVEL_HOLD_WHEN_STOPPED",
    ts="LEVEL_TS",
    tf_ts="LEVEL_TF_TS",
    sp_ramp_max="LEVEL_SP_RAMP_MAX",
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
    co_man="CO_FLOW_MAN",
    kp="FLOW_KP",
    ki="FLOW_KI",
    kd="FLOW_KD",
    u0="FLOW_U0",
    beta="FLOW_BETA",
    direct_acting="FLOW_DIRECT_ACTING",
    cv_min="FLOW_CV_MIN",
    cv_max="FLOW_CV_MAX",
    hold_when_stopped="FLOW_HOLD_WHEN_STOPPED",
    ts="FLOW_TS",
    tf_ts="FLOW_TF_TS",
    sp_ramp_max="FLOW_SP_RAMP_MAX",
)

DEMO_PID_LOOPS: tuple[PidLoopTags, ...] = (LEVEL_LOOP, FLOW_LOOP)


def all_operator_param_tag_names() -> frozenset[str]:
    """Every faceplate PID parameter IN tag on the demo loops."""
    names: set[str] = set()
    for loop in DEMO_PID_LOOPS:
        names.update(loop.operator_param_tags().values())
    return frozenset(names)


def select_active_sp(
    mode: SpSourceMode | str,
    *,
    sp_man: float,
    sp_auto: float,
    sp_rem: float,
) -> float:
    """Return the displayed / closed-loop SP for the mode.

    Manual still reports ``sp_man`` for faceplate history; the PID does not use
    it while output Manual is active.
    """
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

    Writing Auto / Rem SP auto-flips to that mode (SWD-183 / SWD-222).
    Writing the legacy Manual SP tag still flips to Manual (lab back-compat)
    but the live MAN write target is CO.
    """
    del current_mode  # reserved for future bumpless / tracking rules
    return SpSourceMode.parse(source)


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
    """Apply a source-SP write; auto-flip mode for Man/Auto/Rem (SWD-222).

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
        mode = SpSourceMode.AUTOMATIC
    sp = select_active_sp(mode, sp_man=man, sp_auto=auto, sp_rem=rem)
    return {
        "mode": mode.value,
        "sp_man": man,
        "sp_auto": auto,
        "sp_rem": rem,
        "sp": sp,
    }


def apply_co_write(
    *,
    value: float,
    current_cv: float = 0.0,
) -> dict[str, Any]:
    """Apply an output-Manual CO write (DCS MAN / Bauer ``uman``)."""
    del current_cv
    return {
        "mode": SpSourceMode.MANUAL.value,
        "cv": float(value),
        "write_target": "co",
    }


def faceplate_from_image_tags(
    tags: PidLoopTags,
    values: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a climate-like faceplate dict from a tag value map."""
    mode = SpSourceMode.parse(values.get(tags.mode, SpSourceMode.AUTOMATIC))
    man = float(values.get(tags.sp_man, 0.0) or 0.0)
    auto = float(values.get(tags.sp_auto, 0.0) or 0.0)
    rem = float(values.get(tags.sp_rem, 0.0) or 0.0)
    sp = select_active_sp(mode, sp_man=man, sp_auto=auto, sp_rem=rem)
    co_man = float(values.get(tags.co_man, 0.0) or 0.0)
    return {
        "loop_id": tags.loop_id,
        "mode": mode.value,
        "write_target": operator_write_target(mode),
        "pv": values.get(tags.pv),
        "sp": sp,
        "sp_man": man,
        "sp_auto": auto,
        "sp_rem": rem,
        "cv": values.get(tags.cv),
        "co_man": co_man,
        "kp": values.get(tags.kp),
        "ki": values.get(tags.ki),
        "kd": values.get(tags.kd),
        "u0": values.get(tags.u0),
        "beta": values.get(tags.beta),
        "direct_acting": values.get(tags.direct_acting),
        "cv_min": values.get(tags.cv_min),
        "cv_max": values.get(tags.cv_max),
        "hold_when_stopped": values.get(tags.hold_when_stopped),
        "ts": values.get(tags.ts),
        "tf_ts": values.get(tags.tf_ts),
        "sp_ramp_max": values.get(tags.sp_ramp_max),
        "sp_target": sp,
        "tags": {
            "pv": tags.pv,
            "sp": tags.sp,
            "sp_man": tags.sp_man,
            "sp_auto": tags.sp_auto,
            "sp_rem": tags.sp_rem,
            "mode": tags.mode,
            "cv": tags.cv,
            "co_man": tags.co_man,
        },
    }


__all__ = [
    "DEMO_PID_LOOPS",
    "FLOW_LOOP",
    "LEVEL_LOOP",
    "PID_BOOL_PARAM_KEYS",
    "PID_FACEPLATE_EXTRA_KEYS",
    "PID_FACEPLATE_PARAM_KEYS",
    "PID_OPERATOR_PARAM_KEYS",
    "PidLoopTags",
    "all_operator_param_tag_names",
    "SpSourceMode",
    "apply_co_write",
    "apply_explicit_mode",
    "apply_sp_write",
    "faceplate_from_image_tags",
    "is_output_manual",
    "mode_after_sp_source_write",
    "operator_write_target",
    "select_active_sp",
]
