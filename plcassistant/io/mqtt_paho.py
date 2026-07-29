"""Optional paho-mqtt bus adapter for the HA App (not required in CI)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from plcassistant.io.mqtt_topics import MQTT_QOS

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover - optional at runtime
    mqtt = None  # type: ignore[assignment]


class PahoMqttBus:
    """``MqttBus`` backed by paho-mqtt (App container installs paho-mqtt)."""

    def __init__(
        self,
        host: str = "core-mosquitto",
        port: int = 1883,
        *,
        username: str | None = None,
        password: str | None = None,
        client_id: str = "plcassistant-app",
        will_topic: str | None = None,
        will_payload: bytes | None = None,
    ) -> None:
        if mqtt is None:
            raise ImportError(
                "paho-mqtt is required for the live App MQTT bus; "
                "pip install paho-mqtt (App image already does)"
            )
        self._client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        if username:
            self._client.username_pw_set(username, password or None)
        # Soft-PLC disconnect → retained offline on the HMI status topic (SWD-136).
        if will_topic and will_payload is not None:
            self._client.will_set(will_topic, will_payload, qos=MQTT_QOS, retain=True)
        self._subs: dict[str, list[Callable[[str, bytes], None]]] = {}
        self._client.on_message = self._on_message
        self._client.connect(host, port, keepalive=60)
        self._client.loop_start()

    def _on_message(self, client: Any, userdata: Any, msg: Any) -> None:
        topic = str(msg.topic)
        payload = bytes(msg.payload)
        for pattern, callbacks in list(self._subs.items()):
            if _topic_matches(pattern, topic):
                for cb in list(callbacks):
                    cb(topic, payload)

    def publish(
        self,
        topic: str,
        payload: bytes,
        *,
        qos: int = MQTT_QOS,
        retain: bool = False,
    ) -> None:
        self._client.publish(topic, payload, qos=qos, retain=retain)

    def subscribe(self, topic: str, callback: Callable[[str, bytes], None]) -> None:
        self._subs.setdefault(topic, []).append(callback)
        self._client.subscribe(topic, qos=MQTT_QOS)

    def close(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()


def _topic_matches(pattern: str, topic: str) -> bool:
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


__all__ = ["PahoMqttBus"]
