"""MQTT topic helpers for the thin integration (bundled copy of packaging map).

Keep in sync with ``plcassistant.io.mqtt_topics`` / docs/packaging/02-mqtt-topics.md.
"""

from __future__ import annotations

from .const import TOPIC_ROOT


def tag_in_topic(instance_id: str, tag: str) -> str:
    return f"{TOPIC_ROOT}/{instance_id}/tag/{tag}/in"


def tag_out_topic(instance_id: str, tag: str) -> str:
    return f"{TOPIC_ROOT}/{instance_id}/tag/{tag}/out"


def cmd_topic(instance_id: str, name: str) -> str:
    return f"{TOPIC_ROOT}/{instance_id}/cmd/{name}"


def status_topic(instance_id: str) -> str:
    return f"{TOPIC_ROOT}/{instance_id}/status"
