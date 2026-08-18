"""Cascade control: SP_LEVEL → SP_FLOW → CMD_SPEED (docs/control/02-fb-pid.md).

When MODE = RUNNING (pump permit):
1. Level loop (LT_TANK vs SP_LEVEL) produces SP_FLOW (L/min).
2. Flow loop (FT_INLET vs SP_FLOW) produces CMD_SPEED (0–100 %).

PI controllers; sample time = injectable ``dt``. D terms reserved (Td=0).
Conditional anti-windup on clamp. Bumpless Start via ``prepare_bumpless``.
Inactive when not running — hold last SP_FLOW, force CMD_SPEED = 0.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class CascadeConfig:
    """Cascade tuning. Level m; flow L/min; speed 0–100 %."""

    level_kp: float = 40.0
    """Level P gain → SP_FLOW (L/min per m error)."""

    level_ki: float = 5.0
    """Level I gain (1/s · error → SP_FLOW contribution)."""

    flow_kp: float = 12.0
    """Flow P gain → CMD_SPEED (% per L/min error)."""

    flow_ki: float = 2.0
    """Flow I gain."""

    sp_flow_min: float = 0.0
    sp_flow_max: float = 8.0
    """SP_FLOW_MAX clamp (L/min); default matches plant ``q_pump_max``."""

    cmd_speed_min: float = 0.0
    cmd_speed_max: float = 100.0
    """CMD_SPEED_MAX clamp (%)."""

    level_td: float = 0.0
    """Level D time stub — reserved; v1 ignores (must stay 0). Appended to keep positional kwargs stable."""

    flow_td: float = 0.0
    """Flow D time stub — reserved; v1 ignores (must stay 0)."""

    level_kd: float = 0.0
    flow_kd: float = 0.0
    level_u0: float = 0.0
    flow_u0: float = 0.0
    level_beta: float = 1.0
    flow_beta: float = 1.0
    level_direct_acting: bool = False
    flow_direct_acting: bool = False
    level_hold_when_stopped: bool = True
    flow_hold_when_stopped: bool = False
    level_ts: float = 0.1
    flow_ts: float = 0.1
    level_tf_ts: float = 0.0
    flow_tf_ts: float = 0.0
    level_sp_ramp_max: float = 0.0
    """Level SP rate limit (m/s). 0 = instant. Not copied into PID instance params."""
    flow_sp_ramp_max: float = 0.0
    """Flow SP rate limit (L/min/s). 0 = instant. Not copied into PID instance params."""

    def instance_operator_params(self, instance_id: str) -> dict[str, float | bool]:
        """Standardised PID params for a cascade PI copy, from faceplate tags."""
        if instance_id == "level_pi":
            return {
                "kp": float(self.level_kp),
                "ki": float(self.level_ki),
                "kd": float(self.level_kd),
                "u0": float(self.level_u0),
                "beta": float(self.level_beta),
                "direct_acting": bool(self.level_direct_acting),
                "cv_min": float(self.sp_flow_min),
                "cv_max": float(self.sp_flow_max),
                "hold_when_stopped": bool(self.level_hold_when_stopped),
                "ts": float(self.level_ts),
                "tf_ts": float(self.level_tf_ts),
            }
        if instance_id == "flow_pi":
            return {
                "kp": float(self.flow_kp),
                "ki": float(self.flow_ki),
                "kd": float(self.flow_kd),
                "u0": float(self.flow_u0),
                "beta": float(self.flow_beta),
                "direct_acting": bool(self.flow_direct_acting),
                "cv_min": float(self.cmd_speed_min),
                "cv_max": float(self.cmd_speed_max),
                "hold_when_stopped": bool(self.flow_hold_when_stopped),
                "ts": float(self.flow_ts),
                "tf_ts": float(self.flow_tf_ts),
            }
        return {}


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
    """Level → flow SP → speed cascade with PI + conditional anti-windup."""

    def __init__(self, config: CascadeConfig | None = None) -> None:
        self.config = config or CascadeConfig()
        self._level_i = 0.0
        self._flow_i = 0.0
        self._bumpless_pending = False
        self._last = CascadeOutputs(
            sp_flow=0.0, cmd_speed=0.0, level_error=0.0, flow_error=0.0
        )

    @property
    def last(self) -> CascadeOutputs:
        return self._last

    @property
    def level_integral(self) -> float:
        return self._level_i

    @property
    def flow_integral(self) -> float:
        return self._flow_i

    def reset_integrators(self) -> None:
        """Clear integral state (call on trip / stop when freezing to idle)."""
        self._level_i = 0.0
        self._flow_i = 0.0
        self._bumpless_pending = False

    def prepare_bumpless(
        self,
        *,
        lt_tank: float,
        ft_inlet: float,
        sp_level: float,
        target_sp_flow: float | None = None,
        target_cmd_speed: float = 0.0,
    ) -> None:
        """Initialize integrals so the next RUNNING step matches targets.

        Used on Start rising-edge: keep held ``SP_FLOW`` (default) and start
        ``CMD_SPEED`` at ``target_cmd_speed`` (normally 0 after Stop/trip) so
        the first scan does not jump unboundedly from empty integrators.
        """
        cfg = self.config
        sp_flow = (
            self._last.sp_flow if target_sp_flow is None else float(target_sp_flow)
        )
        sp_flow = _clamp(sp_flow, cfg.sp_flow_min, cfg.sp_flow_max)
        cmd = _clamp(target_cmd_speed, cfg.cmd_speed_min, cfg.cmd_speed_max)

        level_error = sp_level - lt_tank
        if cfg.level_ki != 0.0:
            # Prefit I so kp*e + ki*I equals target on the *next* step with
            # `_bumpless_pending` (that first RUNNING scan skips I += error*dt).
            self._level_i = (sp_flow - cfg.level_kp * level_error) / cfg.level_ki
        else:
            self._level_i = 0.0

        flow_error = sp_flow - ft_inlet
        if cfg.flow_ki != 0.0:
            self._flow_i = (cmd - cfg.flow_kp * flow_error) / cfg.flow_ki
        else:
            self._flow_i = 0.0

        self._bumpless_pending = True
        self._last = CascadeOutputs(
            sp_flow=sp_flow,
            cmd_speed=cmd,
            level_error=level_error,
            flow_error=flow_error,
        )

    def step(
        self,
        dt: float,
        *,
        lt_tank: Optional[float],
        ft_inlet: Optional[float],
        sp_level: float,
        running: bool,
    ) -> CascadeOutputs:
        """Compute cascade outputs for one scan.

        When ``running`` is False: clear integrators, hold last ``SP_FLOW``,
        force ``CMD_SPEED = 0`` (docs/wedge/03 STOP — hold last SPs).
        Sample time is ``dt`` (Ts); D terms are stubs (Td=0).
        """
        if dt < 0:
            raise ValueError("dt must be non-negative")
        cfg = self.config
        # D stubs reserved — v1 must not apply derivative action.
        _ = cfg.level_td, cfg.flow_td

        if not running:
            self.reset_integrators()
            self._last = CascadeOutputs(
                sp_flow=self._last.sp_flow,
                cmd_speed=0.0,
                level_error=self._last.level_error,
                flow_error=self._last.flow_error,
            )
            return self._last

        # Defensive: LOS should have tripped pump_permit; treat as idle.
        if lt_tank is None or ft_inlet is None:
            self.reset_integrators()
            self._last = CascadeOutputs(
                sp_flow=self._last.sp_flow,
                cmd_speed=0.0,
                level_error=self._last.level_error,
                flow_error=self._last.flow_error,
            )
            return self._last

        level_error = sp_level - lt_tank
        # Conditional integration: accumulate only when not pushing further
        # into saturation (anti-windup). After prepare_bumpless, skip the first
        # I advance so the prepared bias is the first RUNNING output.
        raw_flow_p = cfg.level_kp * level_error
        if self._bumpless_pending:
            tentative_i = self._level_i
        else:
            tentative_i = self._level_i + level_error * dt
        raw_flow = raw_flow_p + cfg.level_ki * tentative_i
        sp_flow = _clamp(raw_flow, cfg.sp_flow_min, cfg.sp_flow_max)
        if sp_flow == raw_flow or (
            (raw_flow > cfg.sp_flow_max and level_error <= 0)
            or (raw_flow < cfg.sp_flow_min and level_error >= 0)
        ):
            self._level_i = tentative_i
        # else: freeze I (already saturated in the error direction)

        flow_error = sp_flow - ft_inlet
        raw_speed_p = cfg.flow_kp * flow_error
        if self._bumpless_pending:
            tentative_fi = self._flow_i
        else:
            tentative_fi = self._flow_i + flow_error * dt
        raw_speed = raw_speed_p + cfg.flow_ki * tentative_fi
        cmd_speed = _clamp(raw_speed, cfg.cmd_speed_min, cfg.cmd_speed_max)
        if cmd_speed == raw_speed or (
            (raw_speed > cfg.cmd_speed_max and flow_error <= 0)
            or (raw_speed < cfg.cmd_speed_min and flow_error >= 0)
        ):
            self._flow_i = tentative_fi

        self._bumpless_pending = False

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
