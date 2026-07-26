"""Mock process physics for the one-tank + reservoir recycled loop.

First-class simulation surface (see docs/wedge/05-mock-process.md) — not a
test-only stub. Publishes/consumes the tag contract in 02-io-hmi-contract.md:

- LT_TANK, LT_RES — levels in metres
- FT_INLET — inlet volumetric flow in L/min
- CMD_SPEED — pump speed command 0–100 %
- SC_PUMP — optional speed feedback (tracks CMD_SPEED with lag)
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt


@dataclass
class ProcessConfig:
    """Tunable mock plant parameters (injectable for tests)."""

    a_tank: float = 0.05
    """Tank cross-section A_TANK (m²)."""

    a_res: float = 0.10
    """Reservoir cross-section A_RES (m²)."""

    h_tank_max: float = 0.40
    """H_TANK_MAX (m)."""

    h_res_max: float = 0.30
    """H_RES_MAX (m)."""

    q_pump_max: float = 8.0
    """Q_PUMP_MAX at CMD_SPEED = 100 % (L/min)."""

    k_drain: float = 5.0
    """K_DRAIN: q_drain = K_DRAIN * sqrt(h_tank) (L/min)."""

    pump_tau: float = 0.5
    """First-order lag τ for FT_INLET toward q_in (s)."""

    speed_fb_tau: float = 0.2
    """Lag for optional SC_PUMP feedback (s)."""

    lim_res_ll: float = 0.05
    """Used only for soft pump derate near LL (trip owned by safety)."""

    initial_h_tank: float = 0.15
    initial_h_res: float = 0.20


@dataclass
class ProcessState:
    """Observable process measurements and applied command."""

    lt_tank: float
    """LT_TANK (m)."""

    lt_res: float
    """LT_RES (m)."""

    ft_inlet: float
    """FT_INLET (L/min)."""

    cmd_speed: float
    """CMD_SPEED applied this step (0–100 %)."""

    sc_pump: float
    """SC_PUMP feedback (%); tracks CMD_SPEED with lag."""


class MockProcess:
    """Simulated reservoir ↔ tank loop with pump and gravity drain.

    Mass balance (L/min with areas in m²; 1000 L = 1 m³)::

        q_in    = Q_PUMP_MAX * (CMD_SPEED/100) * derate(h_res)
        q_drain = K_DRAIN * sqrt(max(h_tank, 0))
        dh_tank/dt = (q_in - q_drain) / (A_TANK * 1000) / 60   # m per second
        dh_res/dt  = (q_drain - q_in) / (A_RES * 1000) / 60
    """

    def __init__(self, config: ProcessConfig | None = None) -> None:
        self.config = config or ProcessConfig()
        self._h_tank = _clamp(self.config.initial_h_tank, 0.0, self.config.h_tank_max)
        self._h_res = _clamp(self.config.initial_h_res, 0.0, self.config.h_res_max)
        self._ft_inlet = 0.0
        self._cmd_speed = 0.0
        self._sc_pump = 0.0

    @property
    def k_drain(self) -> float:
        return self.config.k_drain

    @k_drain.setter
    def k_drain(self, value: float) -> None:
        """Disturbance knob (set_K_DRAIN) for cascade demos."""
        self.config.k_drain = float(value)

    @property
    def state(self) -> ProcessState:
        return ProcessState(
            lt_tank=self._h_tank,
            lt_res=self._h_res,
            ft_inlet=self._ft_inlet,
            cmd_speed=self._cmd_speed,
            sc_pump=self._sc_pump,
        )

    def set_levels(self, *, lt_tank: float | None = None, lt_res: float | None = None) -> None:
        """Direct level override (nudge_h_tank / nudge_h_res)."""
        cfg = self.config
        if lt_tank is not None:
            self._h_tank = _clamp(lt_tank, 0.0, cfg.h_tank_max)
        if lt_res is not None:
            self._h_res = _clamp(lt_res, 0.0, cfg.h_res_max)

    def nudge(self, *, dh_tank: float = 0.0, dh_res: float = 0.0) -> None:
        """Add deltas to tank / reservoir levels (clamped)."""
        self.set_levels(
            lt_tank=self._h_tank + dh_tank if dh_tank else None,
            lt_res=self._h_res + dh_res if dh_res else None,
        )

    def step(self, dt: float, cmd_speed: float) -> ProcessState:
        """Advance the mock plant by ``dt`` seconds under ``CMD_SPEED`` (0–100)."""
        if dt < 0:
            raise ValueError("dt must be non-negative")
        cfg = self.config
        self._cmd_speed = _clamp(cmd_speed, 0.0, 100.0)

        derate = _pump_derate(self._h_res, cfg.lim_res_ll)
        target_q = cfg.q_pump_max * (self._cmd_speed / 100.0) * derate
        if self._cmd_speed <= 0.0 or self._h_res <= 0.0:
            target_q = 0.0

        if cfg.pump_tau <= 0 or dt == 0:
            self._ft_inlet = target_q
        else:
            alpha = 1.0 - exp(-dt / cfg.pump_tau)
            self._ft_inlet += alpha * (target_q - self._ft_inlet)

        q_drain = cfg.k_drain * sqrt(max(self._h_tank, 0.0))

        # L/min → m/s level change: (L/min) / (A_m2 * 1000 L/m3) / 60 s/min
        to_m_per_s_tank = 1.0 / (cfg.a_tank * 1000.0 * 60.0)
        to_m_per_s_res = 1.0 / (cfg.a_res * 1000.0 * 60.0)
        self._h_tank = _clamp(
            self._h_tank + (self._ft_inlet - q_drain) * to_m_per_s_tank * dt,
            0.0,
            cfg.h_tank_max,
        )
        self._h_res = _clamp(
            self._h_res + (q_drain - self._ft_inlet) * to_m_per_s_res * dt,
            0.0,
            cfg.h_res_max,
        )

        if cfg.speed_fb_tau <= 0 or dt == 0:
            self._sc_pump = self._cmd_speed
        else:
            alpha_s = 1.0 - exp(-dt / cfg.speed_fb_tau)
            self._sc_pump += alpha_s * (self._cmd_speed - self._sc_pump)

        return self.state


def _pump_derate(h_res: float, lim_ll: float) -> float:
    """Soft derate as reservoir approaches LL (trip still owns hard stop)."""
    if h_res <= 0.0:
        return 0.0
    if lim_ll <= 0.0 or h_res >= lim_ll * 2.0:
        return 1.0
    return _clamp(h_res / (lim_ll * 2.0), 0.0, 1.0)


def _clamp(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return float(value)
