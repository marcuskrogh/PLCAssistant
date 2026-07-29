"""Skid preset — gravity-drained tank + reservoir (SWD-146).

Ports live physics from ``plcassistant.wedge.process.MockProcess`` into the
integration-owned dynamics core. Soft-PLC stays mock-unaware.
"""

from __future__ import annotations

from math import exp, sqrt
from typing import Mapping

from .core import InputDict, ModelSpec, ParamDict, StateDict

_DEFAULT_PARAMS: ParamDict = {
    "a_tank": 0.05,
    "a_res": 0.10,
    "h_tank_max": 0.40,
    "h_res_max": 0.30,
    "q_pump_max": 8.0,
    "k_drain": 5.0,
    "pump_tau": 0.5,
    "speed_fb_tau": 0.2,
    "lim_res_ll": 0.05,
}

_INITIAL: StateDict = {
    "h_tank": 0.15,
    "h_res": 0.20,
    "ft_inlet": 0.0,
    "sc_pump": 0.0,
}


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


def _limit_flows(
    *,
    q_in: float,
    q_drain: float,
    h_tank: float,
    h_res: float,
    params: ParamDict,
    dt: float,
) -> tuple[float, float]:
    if dt <= 0.0:
        return 0.0, 0.0
    q_in = max(0.0, q_in)
    q_drain = max(0.0, q_drain)
    q_in = min(
        q_in,
        _max_flow_lpm(_volume_l(h_res, params["a_res"]), dt),
        _max_flow_lpm(_volume_l(params["h_tank_max"] - h_tank, params["a_tank"]), dt),
    )
    q_drain = min(
        q_drain,
        _max_flow_lpm(_volume_l(h_tank, params["a_tank"]), dt),
        _max_flow_lpm(_volume_l(params["h_res_max"] - h_res, params["a_res"]), dt),
    )
    return q_in, q_drain


def skid_rhs(dt: float, state: StateDict, inputs: InputDict, params: ParamDict) -> StateDict:
    """Advance skid dynamics by ``dt`` (dt==0 records command only)."""
    if dt < 0:
        raise ValueError("dt must be non-negative")
    cmd = _clamp(float(inputs.get("cmd_speed", 0.0)), 0.0, 100.0)
    h_tank = float(state["h_tank"])
    h_res = float(state["h_res"])
    ft_inlet = float(state["ft_inlet"])
    sc_pump = float(state["sc_pump"])
    if dt == 0.0:
        return {
            "h_tank": h_tank,
            "h_res": h_res,
            "ft_inlet": ft_inlet,
            "sc_pump": sc_pump,
            "cmd_speed": cmd,
        }

    derate = _pump_derate(h_res, params["lim_res_ll"])
    target_q = params["q_pump_max"] * (cmd / 100.0) * derate
    if cmd <= 0.0 or h_res <= 0.0:
        target_q = 0.0
    tau = params["pump_tau"]
    if tau <= 0:
        q_in_cmd = target_q
    else:
        alpha = 1.0 - exp(-dt / tau)
        q_in_cmd = ft_inlet + alpha * (target_q - ft_inlet)
    q_drain_cmd = params["k_drain"] * sqrt(max(h_tank, 0.0))
    q_in, q_drain = _limit_flows(
        q_in=q_in_cmd,
        q_drain=q_drain_cmd,
        h_tank=h_tank,
        h_res=h_res,
        params=params,
        dt=dt,
    )
    to_tank = 1.0 / (params["a_tank"] * 1000.0 * 60.0)
    to_res = 1.0 / (params["a_res"] * 1000.0 * 60.0)
    h_tank = h_tank + (q_in - q_drain) * to_tank * dt
    h_res = h_res + (q_drain - q_in) * to_res * dt
    tau_s = params["speed_fb_tau"]
    if tau_s <= 0:
        sc_pump = cmd
    else:
        alpha_s = 1.0 - exp(-dt / tau_s)
        sc_pump = sc_pump + alpha_s * (cmd - sc_pump)
    return {
        "h_tank": h_tank,
        "h_res": h_res,
        "ft_inlet": q_in,
        "sc_pump": sc_pump,
        "cmd_speed": cmd,
    }


def skid_project(state: StateDict, params: ParamDict, dt: float) -> StateDict:
    del dt  # inventory limiting already applied in rhs
    return {
        "h_tank": _clamp(state["h_tank"], 0.0, params["h_tank_max"]),
        "h_res": _clamp(state["h_res"], 0.0, params["h_res_max"]),
        "ft_inlet": max(0.0, float(state["ft_inlet"])),
        "sc_pump": _clamp(float(state.get("sc_pump", 0.0)), 0.0, 100.0),
        "cmd_speed": _clamp(float(state.get("cmd_speed", 0.0)), 0.0, 100.0),
    }


SKID_SPEC = ModelSpec(
    name="skid",
    state_keys=("h_tank", "h_res", "ft_inlet", "sc_pump"),
    input_keys=("cmd_speed",),
    output_tags={
        "LT_TANK": "h_tank",
        "LT_RES": "h_res",
        "FT_INLET": "ft_inlet",
    },
    param_defaults=dict(_DEFAULT_PARAMS),
    initial_state=dict(_INITIAL),
    rhs=skid_rhs,
    project=skid_project,
)


class SkidModel:
    """Runnable skid preset implementing DynamicsModel."""

    def __init__(self, params: Mapping[str, float] | None = None) -> None:
        self._params: ParamDict = dict(_DEFAULT_PARAMS)
        if params:
            self._params.update({k: float(v) for k, v in params.items()})
        self._state: StateDict = {
            "h_tank": _clamp(
                float(self._params.get("initial_h_tank", _INITIAL["h_tank"])),
                0.0,
                self._params["h_tank_max"],
            ),
            "h_res": _clamp(
                float(self._params.get("initial_h_res", _INITIAL["h_res"])),
                0.0,
                self._params["h_res_max"],
            ),
            "ft_inlet": 0.0,
            "sc_pump": 0.0,
            "cmd_speed": 0.0,
        }
        self._inputs: InputDict = {"cmd_speed": 0.0}

    @property
    def spec(self) -> ModelSpec:
        return SKID_SPEC

    @property
    def state(self) -> Mapping[str, float]:
        return dict(self._state)

    @property
    def params(self) -> Mapping[str, float]:
        return dict(self._params)

    def set_input(self, name: str, value: float) -> None:
        if name not in SKID_SPEC.input_keys:
            raise KeyError(name)
        self._inputs[name] = float(value)

    def step(self, dt: float) -> Mapping[str, float]:
        tentative = SKID_SPEC.rhs(dt, self._state, self._inputs, self._params)
        self._state = SKID_SPEC.project(tentative, self._params, dt)
        return dict(self._state)

    def outputs(self) -> Mapping[str, float]:
        return {tag: float(self._state[key]) for tag, key in SKID_SPEC.output_tags.items()}

    def nudge(self, **deltas: float) -> None:
        if "h_tank" in deltas or "dh_tank" in deltas:
            delta = float(deltas.get("h_tank", deltas.get("dh_tank", 0.0)))
            self._state["h_tank"] = _clamp(
                self._state["h_tank"] + delta, 0.0, self._params["h_tank_max"]
            )
        if "h_res" in deltas or "dh_res" in deltas:
            delta = float(deltas.get("h_res", deltas.get("dh_res", 0.0)))
            self._state["h_res"] = _clamp(
                self._state["h_res"] + delta, 0.0, self._params["h_res_max"]
            )
        for key in ("ft_inlet", "sc_pump"):
            if key in deltas:
                self._state[key] = float(deltas[key])

    def set_levels(self, *, h_tank: float | None = None, h_res: float | None = None) -> None:
        if h_tank is not None:
            self._state["h_tank"] = _clamp(h_tank, 0.0, self._params["h_tank_max"])
        if h_res is not None:
            self._state["h_res"] = _clamp(h_res, 0.0, self._params["h_res_max"])

    def set_k_drain(self, value: float) -> None:
        self._params["k_drain"] = float(value)


PRESETS: dict[str, type[SkidModel]] = {
    "skid": SkidModel,
}


def get_preset(name: str = "skid", params: Mapping[str, float] | None = None) -> SkidModel:
    key = str(name or "skid").strip().lower() or "skid"
    cls = PRESETS.get(key)
    if cls is None:
        raise KeyError(f"unknown dynamics preset: {name!r}")
    return cls(params=params)


__all__ = ["PRESETS", "SKID_SPEC", "SkidModel", "get_preset", "skid_project", "skid_rhs"]
