"""Map wedge ``Skid`` (cascade + MockProcess) onto the Soft-PLC ``IoImage``.

Used by the HA App scan loop so Start/Stop/Reset and ``SP_LEVEL_REQ`` drive a
real plant response — not the toy ``default_scan_logic`` mirror.
"""

from __future__ import annotations

from plcassistant.io.image import IoImage
from plcassistant.wedge.skid import Mode, OperatorCommand, Skid


class SkidImageLogic:
    """Callable scan body: read request SP from image, step Skid, write PVs/CVs."""

    def __init__(self, *, period_s: float = 0.1, skid: Skid | None = None) -> None:
        self.period_s = period_s
        self.skid = skid or Skid()
        self._pending: list[OperatorCommand] = []

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

    def __call__(self, image: IoImage) -> None:
        names = image.names()
        if "SP_LEVEL_REQ" in names:
            try:
                self.skid.sp_level = float(image.get_value("SP_LEVEL_REQ"))
            except (TypeError, ValueError):
                pass
        pending = self._pending
        self._pending = []
        snap = None
        if not pending:
            snap = self.skid.step(self.period_s, OperatorCommand.NONE)
        else:
            for i, cmd in enumerate(pending):
                # Burn dt on the last pulse so plant integrates once per scan.
                dt = self.period_s if i == len(pending) - 1 else 0.0
                snap = self.skid.step(dt, cmd)
        assert snap is not None
        _set = image.set_output
        if "SP_LEVEL" in names:
            _set("SP_LEVEL", float(snap.sp_level))
        if "SP_FLOW" in names:
            _set("SP_FLOW", float(snap.sp_flow))
        if "CMD_SPEED" in names:
            _set("CMD_SPEED", float(snap.cmd_speed))
        if "LT_TANK" in names and snap.lt_tank is not None:
            _set("LT_TANK", float(snap.lt_tank))
        if "LT_RES" in names and snap.lt_res is not None:
            _set("LT_RES", float(snap.lt_res))
        if "FT_INLET" in names and snap.ft_inlet is not None:
            _set("FT_INLET", float(snap.ft_inlet))


__all__ = ["SkidImageLogic"]
