"""Composable skid: mock process + cascade control + safety (one scan/step).

Pure ``step(dt)`` API with injectable clock/dt — no Home Assistant imports.
Tag names align with docs/wedge/02-io-hmi-contract.md.

Clear / restart policy
----------------------
After a trip, clearing the condition alone does **not** restart. Operator must
HMI_RESET (to clear the latch, MODE→STOP) then HMI_START. Reset never
auto-starts. Stop always forces CMD_SPEED = 0 / idle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from plcassistant.wedge.control import CascadeConfig, CascadeController, CascadeOutputs
from plcassistant.wedge.process import MockProcess, ProcessConfig, ProcessPort, ProcessState
from plcassistant.wedge.safety import (
    Mode,
    SafetyConfig,
    SafetyLayer,
    SafetyState,
    TripCode,
)


class OperatorCommand(str, Enum):
    """Maps to HMI_START / HMI_STOP / HMI_RESET."""

    NONE = "none"
    START = "start"  # HMI_START
    STOP = "stop"  # HMI_STOP
    RESET = "reset"  # HMI_RESET


class _UnsetType:
    __slots__ = ()

    def __repr__(self) -> str:
        return "<UNSET>"


_UNSET = _UnsetType()


@dataclass
class LimitConfig:
    """Single owner for HH / LL thresholds (process derate + safety trip)."""

    lim_level_hh: float = 0.36
    """LIM_LEVEL_HH (m) — tank high trip."""

    lim_res_ll: float = 0.05
    """LIM_RES_LL (m) — reservoir low trip and soft pump derate."""


@dataclass
class SkidConfig:
    process: ProcessConfig = field(default_factory=ProcessConfig)
    cascade: CascadeConfig = field(default_factory=CascadeConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    limits: LimitConfig = field(default_factory=LimitConfig)
    """Canonical lim_level_hh / lim_res_ll — synced into process + safety."""

    sp_level: float = 0.20
    """SP_LEVEL default (m)."""


@dataclass(frozen=True)
class MeasurementView:
    """One-scan resolved PVs + BAD flags (overrides / injectors applied)."""

    lt_tank: Optional[float]
    lt_res: Optional[float]
    ft_inlet: Optional[float]
    lt_tank_bad: bool
    lt_res_bad: bool
    ft_inlet_bad: bool


@dataclass
class SkidSnapshot:
    """Full observable state after one scan — for HMI / tests / historian."""

    process: ProcessState
    safety: SafetyState
    cascade: CascadeOutputs
    measurement: MeasurementView
    sp_level: float
    """SP_LEVEL (m)."""

    sp_flow: float
    """SP_FLOW from level loop (L/min); held when not running."""

    cmd_speed: float
    """CMD_SPEED applied to the process this scan (%)."""

    lt_tank: Optional[float]
    """Safety-view LT_TANK (None when BAD / LOS)."""

    lt_res: Optional[float]
    """Safety-view LT_RES (None when BAD / LOS)."""

    ft_inlet: Optional[float]
    """Safety-view FT_INLET (None when BAD / LOS)."""

    lt_tank_bad: bool
    lt_res_bad: bool
    ft_inlet_bad: bool

    sc_pump: float
    mode: Mode
    perm_ok: bool
    trip_active: bool
    trip_codes: frozenset

    # Convenience aliases
    @property
    def level_sp(self) -> float:
        return self.sp_level

    @property
    def flow_sp(self) -> float:
        return self.sp_flow


class Skid:
    """One-tank + reservoir skid scan engine.

    Typical use::

        skid = Skid()
        skid.sp_level = 0.22
        snap = skid.step(0.1, command=OperatorCommand.START)
        snap = skid.step(0.1)

    After a trip: clear condition → Reset → Start (reset does not auto-start).
    """

    def __init__(
        self,
        config: SkidConfig | None = None,
        *,
        process: ProcessPort | None = None,
        control: CascadeController | None = None,
        safety: SafetyLayer | None = None,
    ) -> None:
        self.config = config or SkidConfig()
        self._apply_limits()
        self.process: ProcessPort = process or MockProcess(self.config.process)
        self.control = control or CascadeController(self.config.cascade)
        self.safety = safety or SafetyLayer(self.config.safety)
        # Re-sync in case injected process/safety carried stale thresholds
        self._apply_limits()
        self.sp_level = self.config.sp_level
        self._last: SkidSnapshot | None = None
        self._force_lt_tank_bad = False
        self._force_lt_res_bad = False
        self._force_ft_inlet_bad = False
        self._override_lt_tank: object = _UNSET
        self._override_lt_res: object = _UNSET
        self._override_ft_inlet: object = _UNSET

    def _apply_limits(self) -> None:
        """Push LimitConfig into process derate + safety trip thresholds."""
        lim = self.config.limits
        self.config.process.lim_res_ll = lim.lim_res_ll
        self.config.safety.lim_level_hh = lim.lim_level_hh
        self.config.safety.lim_res_ll = lim.lim_res_ll
        process = getattr(self, "process", None)
        if process is not None and hasattr(process, "config"):
            process.config.lim_res_ll = lim.lim_res_ll  # type: ignore[attr-defined]
        safety = getattr(self, "safety", None)
        if safety is not None:
            safety.config.lim_level_hh = lim.lim_level_hh
            safety.config.lim_res_ll = lim.lim_res_ll

    @property
    def level_sp(self) -> float:
        """Alias for SP_LEVEL."""
        return self.sp_level

    @level_sp.setter
    def level_sp(self, value: float) -> None:
        self.sp_level = value

    @property
    def last(self) -> SkidSnapshot | None:
        return self._last

    def clear_faults(self) -> None:
        """Clear all BAD injectors and PV overrides."""
        self._force_lt_tank_bad = False
        self._force_lt_res_bad = False
        self._force_ft_inlet_bad = False
        self._override_lt_tank = _UNSET
        self._override_lt_res = _UNSET
        self._override_ft_inlet = _UNSET

    def force_lt_tank_bad(self, bad: bool = True) -> None:
        """force_LT_TANK_BAD injector."""
        self._force_lt_tank_bad = bad

    def force_lt_res_bad(self, bad: bool = True) -> None:
        """force_LT_RES_BAD injector."""
        self._force_lt_res_bad = bad

    def force_ft_inlet_bad(self, bad: bool = True) -> None:
        """force_FT_INLET_BAD injector."""
        self._force_ft_inlet_bad = bad

    def set_signal_override(
        self,
        *,
        lt_tank: object = _UNSET,
        lt_res: object = _UNSET,
        ft_inlet: object = _UNSET,
    ) -> None:
        """Override process measurements (``None`` = unavailable / LOS)."""
        if lt_tank is not _UNSET:
            self._override_lt_tank = lt_tank
        if lt_res is not _UNSET:
            self._override_lt_res = lt_res
        if ft_inlet is not _UNSET:
            self._override_ft_inlet = ft_inlet

    def clear_signal_overrides(self) -> None:
        self._override_lt_tank = _UNSET
        self._override_lt_res = _UNSET
        self._override_ft_inlet = _UNSET

    def _measurement_view(self, live: ProcessState) -> MeasurementView:
        """Resolve one measurement view for this scan (shared by safety + control)."""
        lt_tank = self._read(self._override_lt_tank, live.lt_tank)
        lt_res = self._read(self._override_lt_res, live.lt_res)
        ft_inlet = self._read(self._override_ft_inlet, live.ft_inlet)

        tank_bad = self._force_lt_tank_bad or lt_tank is None
        res_bad = self._force_lt_res_bad or lt_res is None
        flow_bad = self._force_ft_inlet_bad or ft_inlet is None

        return MeasurementView(
            lt_tank=None if tank_bad else lt_tank,
            lt_res=None if res_bad else lt_res,
            ft_inlet=None if flow_bad else ft_inlet,
            lt_tank_bad=tank_bad,
            lt_res_bad=res_bad,
            ft_inlet_bad=flow_bad,
        )

    def step(
        self,
        dt: float,
        command: OperatorCommand = OperatorCommand.NONE,
    ) -> SkidSnapshot:
        """Advance one scan by ``dt`` seconds under optional HMI command."""
        if dt < 0:
            raise ValueError("dt must be non-negative")

        live = self.process.state
        mv = self._measurement_view(live)

        safety = self.safety.evaluate(
            lt_tank=mv.lt_tank,
            lt_res=mv.lt_res,
            ft_inlet=mv.ft_inlet,
            lt_tank_bad=mv.lt_tank_bad,
            lt_res_bad=mv.lt_res_bad,
            ft_inlet_bad=mv.ft_inlet_bad,
            start=command is OperatorCommand.START,
            stop=command is OperatorCommand.STOP,
            reset=command is OperatorCommand.RESET,
        )

        running = safety.pump_permit
        cascade = self.control.step(
            dt,
            lt_tank=mv.lt_tank,
            ft_inlet=mv.ft_inlet,
            sp_level=self.sp_level,
            running=running,
        )

        cmd_speed = cascade.cmd_speed if running else 0.0
        process_state = self.process.step(dt, cmd_speed)

        snap = SkidSnapshot(
            process=process_state,
            safety=safety,
            cascade=cascade,
            measurement=mv,
            sp_level=self.sp_level,
            sp_flow=cascade.sp_flow,
            cmd_speed=cmd_speed,
            lt_tank=mv.lt_tank,
            lt_res=mv.lt_res,
            ft_inlet=mv.ft_inlet,
            lt_tank_bad=mv.lt_tank_bad,
            lt_res_bad=mv.lt_res_bad,
            ft_inlet_bad=mv.ft_inlet_bad,
            sc_pump=process_state.sc_pump,
            mode=safety.mode,
            perm_ok=safety.perm_ok,
            trip_active=safety.trip_active,
            trip_codes=frozenset(safety.trip_codes),
        )
        self._last = snap
        return snap

    @staticmethod
    def _read(override: object, live: float) -> Optional[float]:
        if override is _UNSET:
            return live
        return override  # type: ignore[return-value]


__all__ = [
    "OperatorCommand",
    "LimitConfig",
    "MeasurementView",
    "Skid",
    "SkidConfig",
    "SkidSnapshot",
    "Mode",
    "TripCode",
]
