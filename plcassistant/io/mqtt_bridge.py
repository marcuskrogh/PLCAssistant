"""MQTT ↔ IoImage bridge for the HA App path (SWD-84 / SWD-125).

Uses an injectable bus so unit tests run with ``InMemoryMqttBus`` (no Mosquitto).
Live broker clients are out of scope for CI; wire a real client in the App entry.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol

from plcassistant.io.image import IoImage
from plcassistant.io.mqtt_topics import (
    DEFAULT_INSTANCE_ID,
    MQTT_QOS,
    MqttTagPayload,
    parse_tag_topic,
    status_topic,
    tag_in_topic,
    tag_out_topic,
)
from plcassistant.io.quality import QualityStatus, ReasonCode


class MqttBus(Protocol):
    """Minimal pub/sub surface used by ``MqttIoBridge``."""

    def publish(
        self,
        topic: str,
        payload: bytes,
        *,
        qos: int = MQTT_QOS,
        retain: bool = False,
    ) -> None: ...

    def subscribe(self, topic: str, callback: Callable[[str, bytes], None]) -> None: ...


@dataclass
class InMemoryMqttBus:
    """In-process MQTT stand-in for tests and non-HA CI."""

    _subs: dict[str, list[Callable[[str, bytes], None]]] = field(default_factory=dict)
    published: list[tuple[str, bytes, int, bool]] = field(default_factory=list)

    def publish(
        self,
        topic: str,
        payload: bytes,
        *,
        qos: int = MQTT_QOS,
        retain: bool = False,
    ) -> None:
        self.published.append((topic, payload, qos, retain))
        for pattern, callbacks in list(self._subs.items()):
            if _topic_matches(pattern, topic):
                for cb in list(callbacks):
                    cb(topic, payload)

    def subscribe(self, topic: str, callback: Callable[[str, bytes], None]) -> None:
        self._subs.setdefault(topic, []).append(callback)

    def clear(self) -> None:
        self._subs.clear()
        self.published.clear()


def _topic_matches(pattern: str, topic: str) -> bool:
    """Match MQTT-style ``+`` single-level and ``#`` multi-level wildcards."""
    if pattern == topic:
        return True
    p_parts = pattern.split("/")
    t_parts = topic.split("/")
    for i, part in enumerate(p_parts):
        if part == "#":
            return True
        if i >= len(t_parts):
            return False
        if part == "+":
            continue
        if part != t_parts[i]:
            return False
    return len(p_parts) == len(t_parts)


class MqttIoBridge:
    """Bridge Soft-PLC ``IoImage`` tags to MQTT IN/OUT topics.

    - Subscribes to ``…/tag/+/in`` for the instance and buffers latest samples.
    - ``apply_inputs(image)`` writes buffered IN samples into the image at scan start.
    - ``publish_outputs(image)`` publishes OUT samples for tags written this cycle
      (or an explicit tag list).
    """

    def __init__(
        self,
        bus: MqttBus,
        *,
        instance_id: str = DEFAULT_INSTANCE_ID,
        out_tags: Iterable[str] | None = None,
    ) -> None:
        self._bus = bus
        self.instance_id = instance_id
        self._out_tags = tuple(out_tags) if out_tags is not None else None
        self._pending_in: dict[str, MqttTagPayload] = {}
        self._started = False

    @property
    def pending_inputs(self) -> dict[str, MqttTagPayload]:
        return dict(self._pending_in)

    def start(self) -> None:
        """Subscribe to IN topics for this instance."""
        if self._started:
            return
        pattern = tag_in_topic(self.instance_id, "+")
        self._bus.subscribe(pattern, self._on_message)
        self._started = True

    def _on_message(self, topic: str, payload: bytes) -> None:
        parsed = parse_tag_topic(topic)
        if parsed is None:
            return
        instance_id, tag, direction = parsed
        if instance_id != self.instance_id or direction != "in":
            return
        try:
            sample = MqttTagPayload.decode(payload)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError):
            sample = MqttTagPayload(
                value=None,
                status=QualityStatus.BAD,
                reason=ReasonCode.FAULT,
            )
        self._pending_in[tag] = sample

    def apply_inputs(self, image: IoImage) -> tuple[str, ...]:
        """Apply buffered IN samples to ``image``; return tags applied.

        Missing / never-received tags are left untouched (bindings / declare
        still own defaults). Call at scan start after ``image.begin_inputs()``.
        """
        applied: list[str] = []
        image.begin_inputs()
        for tag, sample in list(self._pending_in.items()):
            if tag not in image.names():
                continue
            image.apply_input(tag, sample.value, sample.status, sample.reason)
            applied.append(tag)
        return tuple(applied)

    def publish_outputs(
        self,
        image: IoImage,
        tags: Iterable[str] | None = None,
    ) -> tuple[str, ...]:
        """Publish OUT payloads for written (or listed) tags; return tags published."""
        if tags is not None:
            names = tuple(tags)
        elif self._out_tags is not None:
            names = self._out_tags
        else:
            names = tuple(image.snapshot_outputs())

        published: list[str] = []
        for tag in names:
            if tag not in image.names():
                continue
            value, quality = image.get(tag)
            payload = MqttTagPayload.now(value, quality.status, quality.reason)
            self._bus.publish(
                tag_out_topic(self.instance_id, tag),
                payload.encode(),
                qos=MQTT_QOS,
                retain=False,
            )
            published.append(tag)
        return tuple(published)

    def publish_status(self, state: str, **extra: Any) -> None:
        """Publish optional App status JSON on the status topic."""
        body = {"state": state, **extra}
        self._bus.publish(
            status_topic(self.instance_id),
            json.dumps(body).encode("utf-8"),
            qos=MQTT_QOS,
            retain=True,
        )


__all__ = [
    "InMemoryMqttBus",
    "MqttBus",
    "MqttIoBridge",
]
