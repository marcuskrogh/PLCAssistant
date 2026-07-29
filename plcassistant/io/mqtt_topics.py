"""MQTT topic helpers and JSON payload codec (SWD-84 / SWD-125).

Locked map: docs/packaging/02-mqtt-topics.md
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Literal, Mapping

from plcassistant.io.quality import QualityStatus, ReasonCode, TagQuality

DEFAULT_INSTANCE_ID = "default"
TOPIC_ROOT = "plcassistant"
MQTT_QOS = 1

Direction = Literal["in", "out"]


def tag_in_topic(instance_id: str, tag: str) -> str:
    """Entity → Soft-PLC (scan IN)."""
    return f"{TOPIC_ROOT}/{instance_id}/tag/{tag}/in"


def tag_out_topic(instance_id: str, tag: str) -> str:
    """Soft-PLC → Entity (scan OUT)."""
    return f"{TOPIC_ROOT}/{instance_id}/tag/{tag}/out"


def cmd_topic(instance_id: str, name: str) -> str:
    """Optional operator pulse command topic."""
    return f"{TOPIC_ROOT}/{instance_id}/cmd/{name}"


def status_topic(instance_id: str) -> str:
    """Optional App status topic."""
    return f"{TOPIC_ROOT}/{instance_id}/status"


_STATUS_STATES = frozenset({"running", "stopped", "fault", "offline"})


def parse_app_status_payload(payload: str | bytes | None) -> str | None:
    """Normalize App status JSON to a chip state, or None if unusable.

    Vocabulary: ``running`` / ``stopped`` / ``fault`` / ``offline``.
    Legacy sticky ``reset`` pulses map to ``stopped`` (SWD-135 / SWD-136).
    """
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


def parse_tag_topic(topic: str) -> tuple[str, str, Direction] | None:
    """Parse ``plcassistant/{id}/tag/{tag}/in|out`` → (instance_id, tag, direction)."""
    parts = topic.split("/")
    if len(parts) != 5:
        return None
    root, instance_id, kind, tag, direction = parts
    if root != TOPIC_ROOT or kind != "tag" or direction not in ("in", "out"):
        return None
    if not instance_id or not tag:
        return None
    return instance_id, tag, direction  # type: ignore[return-value]


@dataclass(frozen=True)
class MqttTagPayload:
    """JSON payload on tag IN/OUT topics."""

    value: Any
    status: QualityStatus = QualityStatus.GOOD
    reason: ReasonCode | None = None
    ts: float | None = None

    def __post_init__(self) -> None:
        TagQuality(self.status, self.reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "status": self.status.value,
            "reason": None if self.reason is None else self.reason.value,
            "ts": self.ts,
        }

    def encode(self) -> bytes:
        return json.dumps(self.to_dict(), separators=(",", ":")).encode("utf-8")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MqttTagPayload:
        if not isinstance(data, dict):
            raise TypeError("MQTT tag payload must be a JSON object")
        status_raw = data.get("status", "GOOD")
        status = QualityStatus(str(status_raw))
        reason_raw = data.get("reason")
        reason: ReasonCode | None
        if reason_raw is None or reason_raw == "":
            reason = None
        else:
            reason = ReasonCode(str(reason_raw))
        ts = data.get("ts")
        ts_f: float | None
        if ts is None:
            ts_f = None
        else:
            try:
                ts_f = float(ts)
            except (TypeError, ValueError):
                ts_f = None

        if "value" not in data:
            if status is QualityStatus.GOOD:
                status = QualityStatus.BAD
                reason = ReasonCode.UNAVAILABLE
            return cls(value=None, status=status, reason=reason, ts=ts_f)

        value = data.get("value")
        if status is QualityStatus.GOOD and value is None:
            status = QualityStatus.BAD
            reason = ReasonCode.UNAVAILABLE
            return cls(value=None, status=status, reason=reason, ts=ts_f)

        return cls(value=value, status=status, reason=reason, ts=ts_f)

    @classmethod
    def decode(cls, raw: bytes | str) -> MqttTagPayload:
        if isinstance(raw, bytes):
            text = raw.decode("utf-8")
        else:
            text = raw
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise TypeError("MQTT tag payload must be a JSON object")
        return cls.from_dict(parsed)

    @classmethod
    def now(
        cls,
        value: Any,
        status: QualityStatus = QualityStatus.GOOD,
        reason: ReasonCode | None = None,
    ) -> MqttTagPayload:
        return cls(value=value, status=status, reason=reason, ts=time.time())


__all__ = [
    "DEFAULT_INSTANCE_ID",
    "MQTT_QOS",
    "TOPIC_ROOT",
    "MqttTagPayload",
    "cmd_topic",
    "parse_app_status_payload",
    "parse_tag_topic",
    "status_topic",
    "tag_in_topic",
    "tag_out_topic",
]
