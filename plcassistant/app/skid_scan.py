"""Map wedge ``Skid`` (cascade + MockProcess) onto the Soft-PLC ``IoImage``.

Used by the HA App scan loop so Start/Stop/Reset and ``SP_LEVEL_REQ`` drive a
real plant response — not the toy ``default_scan_logic`` mirror.
"""

from __future__ import annotations

from plcassistant.io.image import IoImage
from plcassistant.wedge.skid import OperatorCommand, Skid


class SkidImageLogic:
    """Callable scan body: read request SP from image, step Skid, write PVs/CVs."""

    def __init__(self, *, period_s: float = 0.1, skid: Skid | None = None) -> None:
        self.period_s = period_s
        self.skid = skid or Skid()
        self._pending = OperatorCommand.NONE

    def enqueue_operator(self, name: str) -> None:
        key = str(name).lower().strip()
        if key == "start":
            self._pending = OperatorCommand.START
        elif key == "stop":
            self._pending = OperatorCommand.STOP
        elif key == "reset":
            self._pending = OperatorCommand.RESET

    def __call__(self, image: IoImage) -> None:
        names = image.names()
        if "SP_LEVEL_REQ" in names:
            try:
                self.skid.sp_level = float(image.get_value("SP_LEVEL_REQ"))
            except (TypeError, ValueError):
                pass
        cmd = self._pending
        self._pending = OperatorCommand.NONE
        snap = self.skid.step(self.period_s, cmd)
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
