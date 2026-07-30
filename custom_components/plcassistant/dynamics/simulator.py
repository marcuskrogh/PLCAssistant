"""Home Assistant plant simulator — MQTT I/O around :class:`PlantSimulator`.

Unit tests must not import this module (requires ``homeassistant``).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Mapping

from homeassistant.core import HomeAssistant

from ..const import DOMAIN
from ..mqtt_topics import tag_in_topic
from .plant import PlantSimulator

_LOGGER = logging.getLogger(__name__)

_POLL_S = 0.05


class HassPlantSimulator:
    """One plant dynamics task per config entry (selected preset)."""

    def __init__(
        self,
        hass: HomeAssistant,
        instance_id: str,
        *,
        entry_id: str | None = None,
        preset: str = "skid",
        params: Mapping[str, float] | None = None,
    ) -> None:
        self.hass = hass
        self._instance_id = instance_id
        self._entry_id = entry_id
        self._preset = str(preset or "skid").strip().lower() or "skid"
        self._params = dict(params or {})
        self._pending: dict[str, str] = {}
        self._plant = PlantSimulator.for_preset(
            self._queue_publish, preset=self._preset, params=self._params
        )
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()
        self._last_mono: float | None = None

    @property
    def preset(self) -> str:
        return self._preset

    @property
    def params(self) -> Mapping[str, float]:
        return dict(self._params)

    @property
    def plant(self) -> PlantSimulator:
        return self._plant

    def owns_plant_tag(self, name: str) -> bool:
        return str(name).upper() in self._plant.owned_tags

    def set_tag(self, name: str, value: float) -> None:
        """Absolute operator nudge into plant state; simulator republishes IN."""
        self._plant.set_output_tag(name, value)

    def apply_status(self, payload: Any) -> None:
        self._plant.apply_status_payload(payload)

    def apply_cmd_from_payload(self, payload: Any) -> None:
        value = _parse_tag_value(payload)
        if value is None:
            return
        self._plant.apply_cmd_speed(value)

    def _queue_publish(self, tag: str, payload: str) -> None:
        self._pending[str(tag).upper()] = payload

    async def async_start(self) -> None:
        self._stop.clear()
        self._last_mono = time.monotonic()
        # Publish preset defaults immediately so Soft-PLC sees plant IN before Start.
        self._plant.publish_now()
        await self._flush()
        try:
            self._task = self.hass.async_create_background_task(
                self._run(),
                name=f"plcassistant_plant_sim_{self._instance_id}",
            )
        except AttributeError:
            self._task = self.hass.async_create_task(self._run())
        _LOGGER.info(
            "Plant simulator started (preset=%s) for instance_id=%s",
            self._preset,
            self._instance_id,
        )

    async def async_stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._pending.clear()
        _LOGGER.info("Plant simulator stopped (instance_id=%s)", self._instance_id)

    async def _flush(self) -> None:
        if not self._pending:
            return
        pending = dict(self._pending)
        self._pending.clear()
        for tag, payload in pending.items():
            # SWD-169/170: HMI plant sensors/Numbers hydrate from this bus
            # (same-process); MQTT remains the Soft-PLC transport.
            # Cache before fire so entities that register later can hydrate.
            tag_key = str(tag).upper()
            if self._entry_id is not None:
                store = self.hass.data.get(DOMAIN, {}).get(self._entry_id)
                if isinstance(store, dict):
                    store.setdefault("in_values", {})[tag_key] = payload
                self.hass.bus.async_fire(
                    f"{DOMAIN}_plant_in",
                    {
                        "entry_id": self._entry_id,
                        "tag": tag_key,
                        "payload": payload,
                    },
                )
            await self.hass.services.async_call(
                "mqtt",
                "publish",
                {
                    "topic": tag_in_topic(self._instance_id, tag),
                    "payload": payload,
                    "qos": 0,
                    "retain": True,
                },
                blocking=False,
            )

    async def _run(self) -> None:
        try:
            while not self._stop.is_set():
                now = time.monotonic()
                last = self._last_mono if self._last_mono is not None else now
                dt = max(0.0, now - last)
                self._last_mono = now
                self._plant.tick(dt, mono=now)
                await self._flush()
                sleep_s = min(_POLL_S, max(0.01, self._plant.period_s / 2.0))
                await asyncio.sleep(sleep_s)
        except asyncio.CancelledError:
            raise


def _parse_tag_value(payload: Any) -> float | None:
    try:
        if isinstance(payload, (bytes, bytearray)):
            text = payload.decode("utf-8")
        else:
            text = str(payload)
        body = json.loads(text or "{}")
        if isinstance(body, dict) and "value" in body:
            return float(body["value"])
        return float(text)
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None


__all__ = ["HassPlantSimulator"]
