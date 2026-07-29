"""MQTT topic helpers for the thin integration (bundled copy of packaging map).

Keep in sync with ``plcassistant.io.mqtt_topics`` / docs/packaging/02-mqtt-topics.md.
"""

from __future__ import annotations

import json

from .const import TOPIC_ROOT

_STATUS_STATES = frozenset({"running", "stopped", "fault", "offline"})


def tag_in_topic(instance_id: str, tag: str) -> str:
    return f"{TOPIC_ROOT}/{instance_id}/tag/{tag}/in"


def tag_out_topic(instance_id: str, tag: str) -> str:
    return f"{TOPIC_ROOT}/{instance_id}/tag/{tag}/out"


def cmd_topic(instance_id: str, name: str) -> str:
    return f"{TOPIC_ROOT}/{instance_id}/cmd/{name}"


def status_topic(instance_id: str) -> str:
    return f"{TOPIC_ROOT}/{instance_id}/status"


def parse_app_status_payload(payload: str | bytes | None) -> str | None:
    """Normalize App status JSON to a chip state (SWD-136). Keep in sync with package."""
    if payload is None:
        return None
    try:
        if isinstance(payload, bytes):
            text = payload.decode("utf-8")
        else:
            text = str(payload)
        body = json.loads(text or "{}")
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(body, dict):
        return None
    state = str(body.get("state") or "").strip().lower()
    if not state:
        return None
    if state == "reset":
        return "stopped"
    if state not in _STATUS_STATES:
        return "fault"
    return state
