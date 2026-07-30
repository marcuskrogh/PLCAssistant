"""Plant simulator runtime — HA-free (SWD-146).

Steps a dynamics preset, tracks Soft-PLC status/CMD_SPEED, and produces
MQTT IN payloads for plant PVs. The HA wrapper wires timers and publish.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .core import DynamicsModel, FixedStepRunner, parse_scan_period_s
from .registry import get_preset

PublishFn = Callable[[str, str], None]
"""publish(tag, json_payload)"""


@dataclass
class PlantSimulator:
    """Own plant MQTT IN publishing for one mock_mode config entry."""

    model: DynamicsModel
    publish: PublishFn
    period_s: float = 0.1
    cmd_watchdog_s: float = 2.0
    # Stay frozen until Soft-PLC status is running/stopped (SWD-146).
    frozen: bool = True
    status_state: str = "offline"
    _runner: FixedStepRunner = field(init=False)
    _last_cmd_mono: float | None = field(default=None, init=False)
    _quality: dict[str, tuple[str, str | None]] = field(default_factory=dict, init=False)
    _last_publish: dict[str, float] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._runner = FixedStepRunner(self.model, period_s=self.period_s)

    @classmethod
    def for_preset(
        cls,
        publish: PublishFn,
        *,
        preset: str = "skid",
        period_s: float = 0.1,
    ) -> PlantSimulator:
        return cls(model=get_preset(preset), publish=publish, period_s=period_s)

    @property
    def owned_tags(self) -> frozenset[str]:
        return frozenset(self.model.spec.output_tags.keys())

    def apply_status_payload(self, payload: Any) -> None:
        period = parse_scan_period_s(payload, default=self.period_s)
        self._runner.set_period(period)
        self.period_s = period
        state = "offline"
        body: Any = payload
        if isinstance(payload, (bytes, bytearray, str)):
            try:
                text = payload.decode("utf-8") if isinstance(payload, (bytes, bytearray)) else payload
                body = json.loads(text or "{}")
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                body = {}
        if isinstance(body, Mapping):
            raw = str(body.get("state") or "").strip().lower()
            if raw == "reset":
                raw = "stopped"
            if raw in {"running", "stopped", "fault", "offline"}:
                state = raw
        prev = self.status_state
        self.status_state = state
        if state in {"offline", "fault"}:
            self.frozen = True
            self._runner.reset_timing()
            self.model.set_input("cmd_speed", 0.0)
        else:
            if prev in {"offline", "fault"} and state in {"running", "stopped"}:
                self._runner.reset_timing()
            self.frozen = False

    def apply_cmd_speed(self, value: float, *, mono: float | None = None) -> None:
        now = time.monotonic() if mono is None else float(mono)
        self.model.set_input("cmd_speed", float(value))
        self._last_cmd_mono = now

    def force_quality(self, tag: str, status: str = "GOOD", reason: str | None = None) -> None:
        key = str(tag).upper()
        if status.upper() == "GOOD":
            self._quality.pop(key, None)
        else:
            self._quality[key] = (status.upper(), reason)

    def nudge(self, **deltas: float) -> None:
        self.model.nudge(**deltas)

    def set_output_tag(self, tag: str, value: float) -> None:
        """Absolute Number nudge for a plant IN tag; republish immediately."""
        key = str(tag).upper()
        state_key = self.model.spec.output_tags.get(key)
        if state_key is None:
            raise KeyError(tag)
        set_state = getattr(self.model, "set_state", None)
        if callable(set_state):
            set_state(state_key, float(value))
        else:
            current = float(self.model.state.get(state_key, 0.0))
            self.model.nudge(**{state_key: float(value) - current})
        self.publish_now()

    def tick(self, wall_dt: float, *, mono: float | None = None) -> Mapping[str, float]:
        now = time.monotonic() if mono is None else float(mono)
        if (
            self._last_cmd_mono is not None
            and (now - self._last_cmd_mono) > self.cmd_watchdog_s
        ):
            self.model.set_input("cmd_speed", 0.0)
        if self.frozen:
            return self.model.outputs()
        # Continue gravity drain while Soft-PLC is stopped (CMD may be 0).
        self._runner.advance(wall_dt)
        outs = self.model.outputs()
        self._publish_outputs(outs)
        return outs

    def publish_now(self) -> Mapping[str, float]:
        outs = self.model.outputs()
        self._publish_outputs(outs, force=True)
        return outs

    def _publish_outputs(self, outs: Mapping[str, float], *, force: bool = False) -> None:
        for tag, value in outs.items():
            status, reason = self._quality.get(tag, ("GOOD", None))
            # Coalesce: skip unchanged GOOD values unless forced.
            if (
                not force
                and status == "GOOD"
                and tag in self._last_publish
                and abs(self._last_publish[tag] - float(value)) < 1e-9
            ):
                continue
            payload = json.dumps(
                {"value": float(value), "status": status, "reason": reason, "ts": None}
            )
            self.publish(tag, payload)
            if status == "GOOD":
                self._last_publish[tag] = float(value)


__all__ = ["PlantSimulator", "PublishFn"]
