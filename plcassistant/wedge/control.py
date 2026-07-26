"""Cascade control: SP_LEVEL → SP_FLOW → CMD_SPEED (docs/wedge/03-control-story.md).

When MODE = RUNNING:
1. Level loop (LT_TANK vs SP_LEVEL) produces SP_FLOW (L/min).
2. Flow loop (FT_INLET vs SP_FLOW) produces CMD_SPEED (0–100 %).

Simple PI controllers; gains injectable. Inactive when not running.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CascadeConfig:
    """Cascade tuning. Level m; flow L/min; speed 0–100 %."""

    level_kp: float = 40.0
    """Level P gain → SP_FLOW (L/min per m error)."""

    level_ki: float = 5.0
    """Level I gain."""

    flow_kp: float = 12.0
    """Flow P gain → CMD_SPEED (% per L/min error)."""

    flow_ki: float = 2.0
    """Flow I gain."""

    sp_flow_min: float = 0.0
    sp_flow_max: float = 6.0
    """SP_FLOW_MAX clamp (L/min)."""

    cmd_speed_min: float = 0.0
    cmd_speed_max: float = 100.0
    """CMD_SPEED_MAX clamp (%)."""


@dataclass
class CascadeOutputs:
    """Internal cascade outputs for one scan."""

    sp_flow: float
    """SP_FLOW — flow setpoint from the level loop (L/min)."""

    cmd_speed: float
    """CMD_SPEED — speed command from the flow loop (0–100 %)."""

    level_error: float
    flow_error: float

    @property
    def flow_sp(self) -> float:
        """Alias used by older call sites."""
        return self.sp_flow


class CascadeController:
    """Level → flow SP → speed cascade with optional integral action."""

    def __init__(self, config: CascadeConfig | None = None) -> None:
        self.config = config or CascadeConfig()
        self._level_i = 0.0
        self._flow_i = 0.0
        self._last = CascadeOutputs(
            sp_flow=0.0, cmd_speed=0.0, level_error=0.0, flow_error=0.0
        )

    @property
    def last(self) -> CascadeOutputs:
        return self._last

    def reset_integrators(self) -> None:
        """Clear integral state (call on trip / stop / mode change)."""
        self._level_i = 0.0
        self._flow_i = 0.0

    def step(
        self,
        dt: float,
        *,
        lt_tank: float,
        ft_inlet: float,
        sp_level: float,
        running: bool,
    ) -> CascadeOutputs:
        """Compute cascade outputs for one scan.

        When ``running`` is False, integrators are cleared and CMD_SPEED is 0.
        """
        if dt < 0:
            raise ValueError("dt must be non-negative")
        cfg = self.config

        if not running:
            self.reset_integrators()
            self._last = CascadeOutputs(
                sp_flow=0.0, cmd_speed=0.0, level_error=0.0, flow_error=0.0
            )
            return self._last

        level_error = sp_level - lt_tank
        self._level_i += level_error * dt
        raw_flow = cfg.level_kp * level_error + cfg.level_ki * self._level_i
        sp_flow = _clamp(raw_flow, cfg.sp_flow_min, cfg.sp_flow_max)
        if raw_flow > cfg.sp_flow_max and level_error > 0:
            self._level_i -= level_error * dt
        elif raw_flow < cfg.sp_flow_min and level_error < 0:
            self._level_i -= level_error * dt

        flow_error = sp_flow - ft_inlet
        self._flow_i += flow_error * dt
        raw_speed = cfg.flow_kp * flow_error + cfg.flow_ki * self._flow_i
        cmd_speed = _clamp(raw_speed, cfg.cmd_speed_min, cfg.cmd_speed_max)
        if raw_speed > cfg.cmd_speed_max and flow_error > 0:
            self._flow_i -= flow_error * dt
        elif raw_speed < cfg.cmd_speed_min and flow_error < 0:
            self._flow_i -= flow_error * dt

        self._last = CascadeOutputs(
            sp_flow=sp_flow,
            cmd_speed=cmd_speed,
            level_error=level_error,
            flow_error=flow_error,
        )
        return self._last


def _clamp(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return float(value)
