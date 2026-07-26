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
from plcassistant.wedge.process import MockProcess, ProcessConfig, ProcessState
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
class SkidConfig:
    process: ProcessConfig = field(default_factory=ProcessConfig)
    cascade: CascadeConfig = field(default_factory=CascadeConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    sp_level: float = 0.20
    """SP_LEVEL default (m)."""


@dataclass
class SkidSnapshot:
    """Full observable state after one scan — for HMI / tests / historian."""

    process: ProcessState
    safety: SafetyState
    cascade: CascadeOutputs
    sp_level: float
    """SP_LEVEL (m)."""

    sp_flow: float
    """SP_FLOW from level loop (L/min)."""

    cmd_speed: float
    """CMD_SPEED applied to the process this scan (%)."""

    lt_tank: float
    lt_res: float
    ft_inlet: float
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
        process: MockProcess | None = None,
        control: CascadeController | None = None,
        safety: SafetyLayer | None = None,
    ) -> None:
        self.config = config or SkidConfig()
        self.process = process or MockProcess(self.config.process)
        self.control = control or CascadeController(self.config.cascade)
        self.safety = safety or SafetyLayer(self.config.safety)
        self.sp_level = self.config.sp_level
        self._last: SkidSnapshot | None = None
        self._force_lt_tank_bad = False
        self._force_lt_res_bad = False
        self._force_ft_inlet_bad = False
        self._override_lt_tank: object = _UNSET
        self._override_lt_res: object = _UNSET
        self._override_ft_inlet: object = _UNSET

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

    def step(
        self,
        dt: float,
        command: OperatorCommand = OperatorCommand.NONE,
    ) -> SkidSnapshot:
        """Advance one scan by ``dt`` seconds under optional HMI command."""
        if dt < 0:
            raise ValueError("dt must be non-negative")

        live = self.process.state
        lt_tank = self._read(self._override_lt_tank, live.lt_tank)
        lt_res = self._read(self._override_lt_res, live.lt_res)
        ft_inlet = self._read(self._override_ft_inlet, live.ft_inlet)

        # BAD injectors: force quality bad (value may still be last live)
        tank_bad = self._force_lt_tank_bad or lt_tank is None
        res_bad = self._force_lt_res_bad or lt_res is None
        flow_bad = self._force_ft_inlet_bad or ft_inlet is None

        safety = self.safety.evaluate(
            lt_tank=None if tank_bad and lt_tank is None else lt_tank,
            lt_res=None if res_bad and lt_res is None else lt_res,
            ft_inlet=None if flow_bad and ft_inlet is None else ft_inlet,
            lt_tank_bad=tank_bad,
            lt_res_bad=res_bad,
            ft_inlet_bad=flow_bad,
            start=command is OperatorCommand.START,
            stop=command is OperatorCommand.STOP,
            reset=command is OperatorCommand.RESET,
        )

        running = safety.pump_permit
        cascade = self.control.step(
            dt,
            lt_tank=live.lt_tank,
            ft_inlet=live.ft_inlet,
            sp_level=self.sp_level,
            running=running,
        )

        cmd_speed = cascade.cmd_speed if running else 0.0
        process_state = self.process.step(dt, cmd_speed)

        snap = SkidSnapshot(
            process=process_state,
            safety=safety,
            cascade=cascade,
            sp_level=self.sp_level,
            sp_flow=cascade.sp_flow,
            cmd_speed=cmd_speed,
            lt_tank=process_state.lt_tank,
            lt_res=process_state.lt_res,
            ft_inlet=process_state.ft_inlet,
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
    "Skid",
    "SkidConfig",
    "SkidSnapshot",
    "Mode",
    "TripCode",
]
