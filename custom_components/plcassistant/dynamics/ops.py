"""Unit-op catalog for plant dynamics composition (SWD-144)."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt
from typing import Any, Callable, Mapping, Protocol

from .core import ParamDict, StateDict
from .expr import ExpressionError, compile_expr

Ctx = dict[str, float]


def _clamp(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return float(value)


def _volume_l(h_m: float, area_m2: float) -> float:
    return h_m * area_m2 * 1000.0


def _max_flow_lpm(volume_l: float, dt: float) -> float:
    if dt <= 0.0 or volume_l <= 0.0:
        return 0.0
    return volume_l * 60.0 / dt


def _pump_derate(h_res: float, lim_ll: float) -> float:
    if h_res <= 0.0:
        return 0.0
    if lim_ll <= 0.0 or h_res >= lim_ll * 2.0:
        return 1.0
    return _clamp(h_res / (lim_ll * 2.0), 0.0, 1.0)


def limit_flows(
    *,
    q_in: float,
    q_drain: float,
    h_tank: float,
    h_res: float,
    a_tank: float,
    a_res: float,
    h_tank_max: float,
    h_res_max: float,
    dt: float,
) -> tuple[float, float]:
    """Shared inventory limiter (same math as skid / MockProcess)."""
    if dt <= 0.0:
        return 0.0, 0.0
    q_in = max(0.0, q_in)
    q_drain = max(0.0, q_drain)
    q_in = min(
        q_in,
        _max_flow_lpm(_volume_l(h_res, a_res), dt),
        _max_flow_lpm(_volume_l(h_tank_max - h_tank, a_tank), dt),
    )
    q_drain = min(
        q_drain,
        _max_flow_lpm(_volume_l(h_tank, a_tank), dt),
        _max_flow_lpm(_volume_l(h_res_max - h_res, a_res), dt),
    )
    return q_in, q_drain


@dataclass(frozen=True)
class OpDecl:
    """What an op instance contributes to the compiled model."""

    state_keys: tuple[str, ...] = ()
    param_defaults: Mapping[str, float] | None = None
    intermediate_keys: tuple[str, ...] = ()
    """Algebraic names written each step (not integrated state)."""


class UnitOp(Protocol):
    name: str

    def declare(self, bind: Mapping[str, str], params: Mapping[str, Any]) -> OpDecl: ...

    def contribute(
        self,
        *,
        dt: float,
        ctx: Ctx,
        bind: Mapping[str, str],
        params: Mapping[str, float],
    ) -> None:
        """Mutate ``ctx`` with this op's contributions for one substep."""


def _resolve_param(raw: Any, params: Mapping[str, float], default: float) -> float:
    if raw is None:
        return float(default)
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw)
    key = str(raw)
    if key in params:
        return float(params[key])
    try:
        return float(key)
    except ValueError as err:
        raise ExpressionError(f"unknown param reference: {raw!r}") from err


def _need(bind: Mapping[str, str], *keys: str) -> None:
    missing = [k for k in keys if k not in bind]
    if missing:
        raise ExpressionError(f"op bind missing keys: {missing}")


class TankOp:
    name = "tank"

    def declare(self, bind: Mapping[str, str], params: Mapping[str, Any]) -> OpDecl:
        _need(bind, "h", "q_in", "q_out")
        return OpDecl(state_keys=(bind["h"],))

    def contribute(
        self,
        *,
        dt: float,
        ctx: Ctx,
        bind: Mapping[str, str],
        params: Mapping[str, float],
    ) -> None:
        # Tank integration is applied by the compiler after inventory coupling.
        # Here we only stamp area/h_max aliases used by inventory_couple.
        del dt, ctx, bind, params


class PumpOp:
    name = "pump"

    def declare(self, bind: Mapping[str, str], params: Mapping[str, Any]) -> OpDecl:
        _need(bind, "cmd", "h_source", "q")
        return OpDecl(state_keys=(bind["q"],))

    def contribute(
        self,
        *,
        dt: float,
        ctx: Ctx,
        bind: Mapping[str, str],
        params: Mapping[str, float],
    ) -> None:
        q_max = _resolve_param(params.get("q_max", params.get("q_pump_max")), params, 8.0)
        tau = _resolve_param(params.get("tau", params.get("pump_tau")), params, 0.5)
        lim_ll = _resolve_param(params.get("lim_ll", params.get("lim_res_ll")), params, 0.05)
        cmd = _clamp(float(ctx.get(bind["cmd"], 0.0)), 0.0, 100.0)
        h_res = float(ctx.get(bind["h_source"], 0.0))
        ft = float(ctx.get(bind["q"], 0.0))
        derate = _pump_derate(h_res, lim_ll)
        target_q = q_max * (cmd / 100.0) * derate
        if cmd <= 0.0 or h_res <= 0.0:
            target_q = 0.0
        if dt <= 0.0:
            ctx[bind["q"] + "__cmd"] = ft
            return
        if tau <= 0:
            q_cmd = target_q
        else:
            alpha = 1.0 - exp(-dt / tau)
            q_cmd = ft + alpha * (target_q - ft)
        ctx[bind["q"] + "__cmd"] = q_cmd


class OrificeOp:
    name = "orifice"

    def declare(self, bind: Mapping[str, str], params: Mapping[str, Any]) -> OpDecl:
        _need(bind, "h", "q")
        return OpDecl(intermediate_keys=(bind["q"],))

    def contribute(
        self,
        *,
        dt: float,
        ctx: Ctx,
        bind: Mapping[str, str],
        params: Mapping[str, float],
    ) -> None:
        del dt
        k = _resolve_param(params.get("k", params.get("k_drain")), params, 5.0)
        h = float(ctx.get(bind["h"], 0.0))
        ctx[bind["q"]] = k * sqrt(max(h, 0.0))
        ctx[bind["q"] + "__cmd"] = ctx[bind["q"]]


class LagOp:
    name = "lag"

    def declare(self, bind: Mapping[str, str], params: Mapping[str, Any]) -> OpDecl:
        _need(bind, "u", "y")
        return OpDecl(state_keys=(bind["y"],))

    def contribute(
        self,
        *,
        dt: float,
        ctx: Ctx,
        bind: Mapping[str, str],
        params: Mapping[str, float],
    ) -> None:
        tau = _resolve_param(params.get("tau"), params, 0.2)
        u = float(ctx.get(bind["u"], 0.0))
        y = float(ctx.get(bind["y"], 0.0))
        if dt <= 0.0:
            return
        if tau <= 0:
            ctx[bind["y"]] = u
        else:
            alpha = 1.0 - exp(-dt / tau)
            ctx[bind["y"]] = y + alpha * (u - y)


class CustomOdeOp:
    name = "custom_ode"

    def declare(self, bind: Mapping[str, str], params: Mapping[str, Any]) -> OpDecl:
        derivatives = params.get("derivatives") or {}
        if not isinstance(derivatives, Mapping) or not derivatives:
            raise ExpressionError("custom_ode requires non-empty derivatives map")
        # Validate expressions at declare/load time.
        for key, expr in derivatives.items():
            compile_expr(str(expr))
            del key
        states = tuple(str(k) for k in derivatives.keys())
        return OpDecl(state_keys=states)

    def contribute(
        self,
        *,
        dt: float,
        ctx: Ctx,
        bind: Mapping[str, str],
        params: Mapping[str, float],
    ) -> None:
        del bind
        derivatives = params.get("derivatives") or {}
        if dt <= 0.0:
            return
        # Snapshot before updates so simultaneous derivatives see prior state.
        prior = dict(ctx)
        for key, expr in derivatives.items():
            deriv = compile_expr(str(expr))(prior)
            ctx[str(key)] = float(prior.get(str(key), 0.0)) + float(deriv) * dt


OP_CATALOG: dict[str, UnitOp] = {
    "tank": TankOp(),
    "pump": PumpOp(),
    "orifice": OrificeOp(),
    "lag": LagOp(),
    "custom_ode": CustomOdeOp(),
}


def get_op(type_name: str) -> UnitOp:
    key = str(type_name or "").strip().lower()
    op = OP_CATALOG.get(key)
    if op is None:
        raise ExpressionError(f"unknown unit-op type: {type_name!r}")
    return op


__all__ = [
    "OP_CATALOG",
    "OpDecl",
    "UnitOp",
    "get_op",
    "limit_flows",
]
