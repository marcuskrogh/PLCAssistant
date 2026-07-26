"""Illustrative safety layer for the tank skid (docs/wedge/04-safety-story.md).

Behaviors:
1. HH_TANK — high tank level → CMD_SPEED = 0, latched
2. LL_RES — low reservoir → CMD_SPEED = 0, latched
3. LOS_LT_TANK / LOS_LT_RES / LOS_FT_INLET — loss-of-signal, latched
4. Latched trip + HMI_RESET (conditions must be clear; no auto-start)
5. HMI_START only if PERM_OK; HMI_STOP always

Clear / restart policy
----------------------
After a trip, clearing the underlying condition alone does **not** restart.
Operator must: clear condition → HMI_RESET (MODE → STOP) → HMI_START.
Reset never auto-starts. Stop always forces pump off / idle.

Reset policy: clear **all** latched codes in one Reset **iff every** underlying
condition is clear; otherwise keep remaining latches (recommended in 04).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set


class Mode(str, Enum):
    STOP = "STOP"
    RUNNING = "RUNNING"
    TRIPPED = "TRIPPED"


class TripCode(str, Enum):
    HH_TANK = "HH_TANK"
    LL_RES = "LL_RES"
    LOS_LT_TANK = "LOS_LT_TANK"
    LOS_LT_RES = "LOS_LT_RES"
    LOS_FT_INLET = "LOS_FT_INLET"


# Alias for earlier sketches / PLAN wording
TripReason = TripCode


@dataclass
class SafetyConfig:
    """Trip thresholds (metres), matching LIM_LEVEL_HH / LIM_RES_LL."""

    lim_level_hh: float = 0.36
    lim_res_ll: float = 0.05


@dataclass
class SafetyState:
    """Observable safety / mode status after a scan."""

    mode: Mode
    trip_active: bool
    trip_codes: Set[TripCode] = field(default_factory=set)
    perm_ok: bool = False
    running: bool = False
    """True when MODE=RUNNING."""

    pump_permit: bool = False
    """True only when MODE=RUNNING — controllers may write CMD_SPEED."""

    @property
    def latched(self) -> bool:
        return self.trip_active

    @property
    def start_permissive(self) -> bool:
        return self.perm_ok

    @property
    def trip_reason(self) -> TripCode | None:
        """Primary latched code for simple displays; None if clear."""
        if not self.trip_codes:
            return None
        order = (
            TripCode.LOS_LT_TANK,
            TripCode.LOS_LT_RES,
            TripCode.LOS_FT_INLET,
            TripCode.HH_TANK,
            TripCode.LL_RES,
        )
        for code in order:
            if code in self.trip_codes:
                return code
        return next(iter(self.trip_codes))


class SafetyLayer:
    """Trips, latch, reset, start permissives, and stop-always semantics."""

    def __init__(self, config: SafetyConfig | None = None) -> None:
        self.config = config or SafetyConfig()
        self._trip_codes: Set[TripCode] = set()
        self._mode = Mode.STOP
        self._last_lt_tank: Optional[float] = None
        self._last_lt_res: Optional[float] = None
        self._last_tank_bad = False
        self._last_res_bad = False
        self._last_flow_bad = False

    @property
    def state(self) -> SafetyState:
        return self._build_state(perm_ok=self._perm_ok_now())

    def evaluate(
        self,
        *,
        lt_tank: Optional[float],
        lt_res: Optional[float],
        ft_inlet: Optional[float],
        lt_tank_bad: bool = False,
        lt_res_bad: bool = False,
        ft_inlet_bad: bool = False,
        start: bool = False,
        stop: bool = False,
        reset: bool = False,
    ) -> SafetyState:
        """Evaluate trips and operator commands for one scan.

        A PV is BAD if the corresponding ``*_bad`` flag is True, or if the
        value is ``None`` / non-finite (unavailable).
        """
        tank_bad = lt_tank_bad or not _pv_ok(lt_tank)
        res_bad = lt_res_bad or not _pv_ok(lt_res)
        flow_bad = ft_inlet_bad or not _pv_ok(ft_inlet)

        self._last_lt_tank = lt_tank
        self._last_lt_res = lt_res
        self._last_tank_bad = tank_bad
        self._last_res_bad = res_bad
        self._last_flow_bad = flow_bad

        active: Set[TripCode] = set()
        if tank_bad:
            active.add(TripCode.LOS_LT_TANK)
        if res_bad:
            active.add(TripCode.LOS_LT_RES)
        if flow_bad:
            active.add(TripCode.LOS_FT_INLET)
        # HH / LL only evaluated on good quality
        if not tank_bad and lt_tank is not None and lt_tank >= self.config.lim_level_hh:
            active.add(TripCode.HH_TANK)
        if not res_bad and lt_res is not None and lt_res <= self.config.lim_res_ll:
            active.add(TripCode.LL_RES)

        if active:
            self._trip_codes |= active
            self._mode = Mode.TRIPPED

        # Stop always — leaves RUNNING → STOP; does not clear latch
        if stop:
            if self._mode is Mode.RUNNING:
                self._mode = Mode.STOP
            elif self._mode is not Mode.TRIPPED:
                self._mode = Mode.STOP

        # Reset clears all latches iff every underlying condition is clear
        if reset and self._trip_codes and not active:
            self._trip_codes.clear()
            self._mode = Mode.STOP

        if self._trip_codes:
            self._mode = Mode.TRIPPED

        perm_ok = self._perm_ok_now()

        if start and perm_ok and not stop:
            self._mode = Mode.RUNNING

        return self._build_state(perm_ok=perm_ok if self._mode is Mode.STOP else False)

    def _perm_ok_now(self) -> bool:
        if self._trip_codes or self._mode is not Mode.STOP:
            return False
        if self._last_tank_bad or self._last_res_bad or self._last_flow_bad:
            return False
        if self._last_lt_tank is None or self._last_lt_res is None:
            return False
        return (
            self._last_lt_tank < self.config.lim_level_hh
            and self._last_lt_res > self.config.lim_res_ll
        )

    def _build_state(self, *, perm_ok: bool) -> SafetyState:
        running = self._mode is Mode.RUNNING
        return SafetyState(
            mode=self._mode,
            trip_active=bool(self._trip_codes),
            trip_codes=set(self._trip_codes),
            perm_ok=perm_ok,
            running=running,
            pump_permit=running,
        )


def _pv_ok(value: Optional[float]) -> bool:
    if value is None:
        return False
    if value != value:  # NaN
        return False
    if value in (float("inf"), float("-inf")):
        return False
    return value >= 0.0
