"""MQTT ↔ IoImage bridge for the HA App path (SWD-84 / SWD-125).

Uses an injectable bus so unit tests run with ``InMemoryMqttBus`` (no Mosquitto).
The HA App entry (``plcassistant.app.runtime``) wires a live bus when options/MQTT
are configured.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from threading import Lock
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
        self._pending_cmds: list[str] = []
        self._started = False
        self._cmd_handlers: dict[str, Callable[[], None]] = {}
        self._lock = Lock()

    @property
    def pending_inputs(self) -> dict[str, MqttTagPayload]:
        with self._lock:
            return dict(self._pending_in)

    @property
    def pending_commands(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._pending_cmds)

    def on_command(self, name: str, handler: Callable[[], None]) -> None:
        """Register a handler for ``cmd/{name}`` operator pulses."""
        self._cmd_handlers[name] = handler

    def start(self) -> None:
        """Subscribe to IN and cmd topics for this instance."""
        if self._started:
            return
        pattern = tag_in_topic(self.instance_id, "+")
        self._bus.subscribe(pattern, self._on_message)
        from plcassistant.io.mqtt_topics import cmd_topic

        self._bus.subscribe(cmd_topic(self.instance_id, "+"), self._on_cmd_message)
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
        with self._lock:
            self._pending_in[tag] = sample

    def _on_cmd_message(self, topic: str, payload: bytes) -> None:
        parts = topic.split("/")
        if len(parts) != 4 or parts[0] != "plcassistant":
            return
        if parts[1] != self.instance_id or parts[2] != "cmd":
            return
        name = parts[3]
        with self._lock:
            self._pending_cmds.append(name)
        # Do not invoke handlers here — apply on the scan thread via drain_commands
        # so IoImage / scanning mutations stay single-threaded.

    def apply_inputs(self, image: IoImage, *, clear: bool = True) -> tuple[str, ...]:
        """Apply buffered IN samples to ``image``; return tags applied.

        When ``clear`` is True (default), consumed samples are removed so a quiet
        publisher does not forever re-assert the last value without a fresh
        message (callers that need retain-until-stale can pass ``clear=False``).
        Undeclared tags are dropped when clearing so the buffer cannot grow unbound.
        """
        applied: list[str] = []
        image.begin_inputs()
        with self._lock:
            items = list(self._pending_in.items())
            if clear:
                self._pending_in.clear()
        known = set(image.names())
        for tag, sample in items:
            if tag not in known:
                continue
            image.apply_input(tag, sample.value, sample.status, sample.reason)
            applied.append(tag)
            if not clear:
                with self._lock:
                    self._pending_in[tag] = sample
        return tuple(applied)

    def enqueue_command(self, name: str) -> None:
        """Queue an operator command for the scan thread (same path as MQTT cmd/)."""
        cmd = str(name).lower().strip()
        if not cmd:
            return
        with self._lock:
            self._pending_cmds.append(cmd)

    def drain_commands(self) -> tuple[str, ...]:
        """Return and clear buffered operator command names."""
        with self._lock:
            cmds = tuple(self._pending_cmds)
            self._pending_cmds.clear()
        return cmds

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

        # HMI state tags are retained so HA hydrates after subscribe (SWD-137).
        retain_tags = frozenset({"MODE", "PERM_OK", "TRIP_ACTIVE"})
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
                retain=tag in retain_tags,
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
