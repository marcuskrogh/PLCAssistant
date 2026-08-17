"""Map wedge ``Skid`` onto the Soft-PLC ``IoImage`` (SWD-145 / SWD-183).

Live App path is **mock-unaware**: plant PVs arrive as MQTT IN, control/safety
still run on ``Skid``, and Soft-PLC publishes CVs/status as OUT. Plant physics
live in the thin integration simulator (SWD-146 skid preset). ``MockProcess``
remains for offline / unit tests only — not constructed here.

SWD-183: SP-source mode mux selects Manual / Automatic / Remote into active SP.
"""

from __future__ import annotations

from plcassistant.io.image import IoImage
from plcassistant.io.pid_loop import (
    FLOW_LOOP,
    LEVEL_LOOP,
    SpSourceMode,
    is_output_manual,
    select_active_sp,
)
from plcassistant.io.quality import QualityStatus, ReasonCode
from plcassistant.wedge.process import HeldProcess
from plcassistant.wedge.skid import Mode, OperatorCommand, Skid

_PLANT_TAGS = (
    ("LT_TANK", "lt_tank"),
    ("LT_RES", "lt_res"),
    ("FT_INLET", "ft_inlet"),
)


def _tag_float(image: IoImage, name: str, default: float = 0.0) -> float:
    names = image.names()
    if name not in names:
        return default
    try:
        return float(image.get_value(name))
    except (TypeError, ValueError):
        return default


def _resolve_level_sp(image: IoImage) -> float:
    """Select active level SP from SP-source mode (SWD-183).

    ``SP_LEVEL_REQ`` is the Automatic writer when declared (SWD-141). When REQ
    is absent, fall back to ``SP_LEVEL_AUTO`` (never prefer AUTO over REQ
    merely because AUTO has ``last_good``).
    """
    names = image.names()
    if "SP_LEVEL_REQ" in names:
        auto = _tag_float(image, "SP_LEVEL_REQ", 0.20)
    elif LEVEL_LOOP.sp_auto in names:
        auto = _tag_float(image, LEVEL_LOOP.sp_auto, 0.20)
    else:
        auto = 0.20
    man = _tag_float(image, LEVEL_LOOP.sp_man, auto)
    rem = _tag_float(image, LEVEL_LOOP.sp_rem, auto)
    mode_raw = image.get_value(LEVEL_LOOP.mode) if LEVEL_LOOP.mode in names else 1
    try:
        mode = SpSourceMode.parse(mode_raw)
    except ValueError:
        mode = SpSourceMode.AUTOMATIC
    return select_active_sp(mode, sp_man=man, sp_auto=auto, sp_rem=rem)


def _resolve_flow_mode(image: IoImage) -> SpSourceMode:
    names = image.names()
    mode_raw = image.get_value(FLOW_LOOP.mode) if FLOW_LOOP.mode in names else 1
    try:
        return SpSourceMode.parse(mode_raw)
    except ValueError:
        return SpSourceMode.AUTOMATIC


def _resolve_flow_sp(image: IoImage, *, cascade_auto: float) -> float:
    """Select active flow SP; Automatic source is the cascade (level CV)."""
    names = image.names()
    auto = cascade_auto
    man = _tag_float(image, FLOW_LOOP.sp_man, auto)
    rem = _tag_float(image, FLOW_LOOP.sp_rem, auto)
    mode = _resolve_flow_mode(image)
    return select_active_sp(mode, sp_man=man, sp_auto=auto, sp_rem=rem)


def _flow_sp_override_from_image(image: IoImage) -> float | None:
    """Remote flow SP for the flow PI this scan; None keeps cascade wire.

    Automatic keeps the level-CO cascade. Manual is output Manual (CO), not an
    SP override. Remote still supplies ``SP_FLOW_REM``.
    """
    mode = _resolve_flow_mode(image)
    if mode is SpSourceMode.AUTOMATIC or mode is SpSourceMode.MANUAL:
        return None
    rem = _tag_float(image, FLOW_LOOP.sp_rem, 0.0)
    return float(rem)


def _uman_from_image(image: IoImage, *, loop) -> float | None:
    """Operator CO when the loop is in output Manual; else None."""
    names = image.names()
    mode_raw = image.get_value(loop.mode) if loop.mode in names else 1
    try:
        mode = SpSourceMode.parse(mode_raw)
    except ValueError:
        mode = SpSourceMode.AUTOMATIC
    if not is_output_manual(mode):
        return None
    if loop.co_man in names:
        return _tag_float(image, loop.co_man, _tag_float(image, loop.cv, 0.0))
    return _tag_float(image, loop.cv, 0.0)


class SkidImageLogic:
    """Callable scan body: plant IN → Skid → control/status OUT."""

    def __init__(self, *, period_s: float = 0.1, skid: Skid | None = None) -> None:
        self.period_s = period_s
        self.skid = skid or Skid(process=HeldProcess())
        self.skid.apply_scan_period_s(period_s)
        self._pending: list[OperatorCommand] = []

    def set_scan_period_s(self, period_s: float) -> None:
        """Align tick ``dt`` with Soft-PLC project ``scan_period_s``."""
        if period_s <= 0:
            raise ValueError("scan_period_s must be positive")
        self.period_s = period_s
        self.skid.apply_scan_period_s(period_s)

    def _scan_dt(self) -> float:
        """Sample time for this scan — follows active project on the skid loader."""
        return float(self.skid.config.scan.scan_period_s)

    def enqueue_operator(self, name: str) -> None:
        key = str(name).lower().strip()
        if key == "start":
            self._pending.append(OperatorCommand.START)
        elif key == "stop":
            self._pending.append(OperatorCommand.STOP)
        elif key == "reset":
            # HMI_RESET clears latches → STOP when trips clear; does not stop a
            # healthy RUNNING skid (use Stop for that). Queue RESET only.
            self._pending.append(OperatorCommand.RESET)

    @property
    def mode(self) -> Mode | None:
        last = self.skid.last
        return last.mode if last is not None else None

    @property
    def is_running(self) -> bool:
        return self.mode is Mode.RUNNING

    def _feed_plant_from_image(self, image: IoImage) -> None:
        """Drive Skid measurements from Soft-PLC plant IN (MQTT ≡ field)."""
        names = image.names()
        snaps = image.snapshot()
        kwargs: dict[str, object] = {}
        for tag, key in _PLANT_TAGS:
            if tag not in names:
                continue
            value, quality = image.get(tag)
            slot = snaps[tag]
            # Declared-but-never-sampled tags are BAD/unavailable with no
            # last-good — keep HeldProcess healthy hold so Start works before
            # plant MQTT arrives. After any sample, propagate quality so real
            # LOS (BAD/unavailable) trips correctly.
            if (
                slot.last_good is None
                and quality.status is QualityStatus.BAD
                and quality.reason is ReasonCode.UNAVAILABLE
            ):
                self.skid.force_quality(tag, QualityStatus.GOOD)
                continue
            kwargs[key] = value
            self.skid.force_quality(tag, quality.status, quality.reason)
        if kwargs:
            self.skid.set_signal_override(**kwargs)

    def __call__(self, image: IoImage) -> None:
        names = image.names()
        cascade = self.skid.config.cascade
        if LEVEL_LOOP.kp in names:
            cascade.level_kp = _tag_float(image, LEVEL_LOOP.kp, cascade.level_kp)
        if LEVEL_LOOP.ki in names:
            cascade.level_ki = _tag_float(image, LEVEL_LOOP.ki, cascade.level_ki)
        if FLOW_LOOP.kp in names:
            cascade.flow_kp = _tag_float(image, FLOW_LOOP.kp, cascade.flow_kp)
        if FLOW_LOOP.ki in names:
            cascade.flow_ki = _tag_float(image, FLOW_LOOP.ki, cascade.flow_ki)
        self.skid.sp_level = _resolve_level_sp(image)
        # Remote flow SP overrides cascade; Manual is output Manual (SWD-369).
        self.skid.sp_flow_override = _flow_sp_override_from_image(image)
        self.skid.level_uman = _uman_from_image(image, loop=LEVEL_LOOP)
        self.skid.flow_uman = _uman_from_image(image, loop=FLOW_LOOP)
        self._feed_plant_from_image(image)
        pending = self._pending
        self._pending = []
        snap = None
        dt = self._scan_dt()
        if not pending:
            snap = self.skid.step(dt, OperatorCommand.NONE)
        else:
            for i, cmd in enumerate(pending):
                # Burn dt on the last pulse so control integrates once per scan.
                step_dt = dt if i == len(pending) - 1 else 0.0
                snap = self.skid.step(step_dt, cmd)
        assert snap is not None
        # Cascade: level CV is SP_FLOW_AUTO; mux → published active SP_FLOW.
        flow_sp = _resolve_flow_sp(image, cascade_auto=float(snap.sp_flow))
        _set = image.set_output
        if "SP_LEVEL" in names:
            _set("SP_LEVEL", float(snap.sp_level))
        if "SP_FLOW" in names:
            _set("SP_FLOW", float(flow_sp))
        if FLOW_LOOP.sp_auto in names:
            _set(FLOW_LOOP.sp_auto, float(snap.sp_flow))
        if "CMD_SPEED" in names:
            _set("CMD_SPEED", float(snap.cmd_speed))
        # Plant PVs are Soft-PLC IN only (SWD-145) — never synthesize as OUT.
        # HMI status tags (docs/wedge/02-io-hmi-contract.md) — string / bool OUT.
        if "MODE" in names:
            _set("MODE", snap.mode.value if snap.mode is not None else Mode.STOP.value)
        if "PERM_OK" in names:
            _set("PERM_OK", bool(snap.perm_ok))
        if "TRIP_ACTIVE" in names:
            _set("TRIP_ACTIVE", bool(snap.trip_active))


__all__ = ["SkidImageLogic"]
