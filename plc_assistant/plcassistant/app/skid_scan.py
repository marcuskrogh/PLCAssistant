"""Map wedge ``Skid`` onto the Soft-PLC ``IoImage`` (SWD-145).

Live App path is **mock-unaware**: plant PVs arrive as MQTT IN, control/safety
still run on ``Skid``, and Soft-PLC publishes CVs/status as OUT. Plant physics
live in the thin integration simulator (SWD-146 skid preset). ``MockProcess``
remains for offline / unit tests only — not constructed here.
"""

from __future__ import annotations

from plcassistant.io.image import IoImage
from plcassistant.io.quality import QualityStatus, ReasonCode
from plcassistant.wedge.process import HeldProcess
from plcassistant.wedge.skid import Mode, OperatorCommand, Skid

_PLANT_TAGS = (
    ("LT_TANK", "lt_tank"),
    ("LT_RES", "lt_res"),
    ("FT_INLET", "ft_inlet"),
)


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
            # last_good — keep HeldProcess healthy hold so Start works before
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
        if "SP_LEVEL_REQ" in names:
            try:
                self.skid.sp_level = float(image.get_value("SP_LEVEL_REQ"))
            except (TypeError, ValueError):
                pass
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
        _set = image.set_output
        if "SP_LEVEL" in names:
            _set("SP_LEVEL", float(snap.sp_level))
        if "SP_FLOW" in names:
            _set("SP_FLOW", float(snap.sp_flow))
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
