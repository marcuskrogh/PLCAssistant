"""HA-independent dynamics engine (SWD-146)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, MutableMapping, Protocol


StateDict = dict[str, float]
ParamDict = dict[str, float]
InputDict = dict[str, float]


@dataclass(frozen=True)
class ModelSpec:
    """Contract for a plant preset (states + params + I/O + step helpers)."""

    name: str
    state_keys: tuple[str, ...]
    input_keys: tuple[str, ...]
    output_tags: Mapping[str, str]
    """Soft-PLC IN tag → state key (e.g. LT_TANK → h_tank)."""
    param_defaults: Mapping[str, float]
    initial_state: Mapping[str, float]
    rhs: Callable[[float, StateDict, InputDict, ParamDict], StateDict]
    """Return tentative next state from ``dt``, current state, inputs, params."""
    project: Callable[[StateDict, ParamDict, float], StateDict]
    """Post-step projection (inventory clamps, etc.)."""


class DynamicsModel(Protocol):
    """Runnable preset surface used by the plant simulator."""

    @property
    def spec(self) -> ModelSpec: ...

    @property
    def state(self) -> Mapping[str, float]: ...

    @property
    def params(self) -> Mapping[str, float]: ...

    def set_input(self, name: str, value: float) -> None: ...

    def step(self, dt: float) -> Mapping[str, float]: ...

    def outputs(self) -> Mapping[str, float]: ...

    def nudge(self, **deltas: float) -> None: ...


@dataclass
class FixedStepRunner:
    """Accumulate wall time and advance a model in fixed substeps ≤ max_dt."""

    model: DynamicsModel
    period_s: float = 0.1
    max_substep_s: float = 0.1
    max_catchup_s: float = 1.0
    _accum_s: float = field(default=0.0, init=False)

    def set_period(self, period_s: float) -> None:
        if period_s > 0 and period_s == period_s:  # finite positive
            self.period_s = float(period_s)

    def reset_timing(self) -> None:
        self._accum_s = 0.0

    def advance(self, wall_dt: float) -> Mapping[str, float]:
        if wall_dt < 0:
            raise ValueError("wall_dt must be non-negative")
        if wall_dt == 0:
            return dict(self.model.state)
        self._accum_s = min(self._accum_s + wall_dt, self.max_catchup_s)
        step = min(self.period_s, self.max_substep_s)
        if step <= 0:
            step = self.max_substep_s
        while self._accum_s + 1e-15 >= step:
            self.model.step(step)
            self._accum_s -= step
        return dict(self.model.state)


def parse_scan_period_s(payload: Any, *, default: float = 0.1) -> float:
    """Extract finite positive scan_period_s from a status JSON object/dict."""
    body: Any = payload
    if isinstance(payload, (bytes, bytearray)):
        import json

        try:
            body = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return default
    elif isinstance(payload, str):
        import json

        try:
            body = json.loads(payload or "{}")
        except (json.JSONDecodeError, ValueError):
            return default
    if not isinstance(body, Mapping):
        return default
    raw = body.get("scan_period_s", default)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    if value != value or value <= 0.0:  # NaN / non-positive
        return default
    return value


__all__ = [
    "DynamicsModel",
    "FixedStepRunner",
    "InputDict",
    "ModelSpec",
    "ParamDict",
    "StateDict",
    "parse_scan_period_s",
]
