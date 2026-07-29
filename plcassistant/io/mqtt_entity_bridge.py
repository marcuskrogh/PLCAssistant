"""Integration-side MQTT adapter (testable without Home Assistant).

Publishes entity samples on tag IN topics and consumes tag OUT into an entity
store — the mirror of ``MqttIoBridge`` on the Soft-PLC App side.
"""

from __future__ import annotations

import json
from typing import Any

from plcassistant.io.binding import BindingTable
from plcassistant.io.integration import MockEntityStore
from plcassistant.io.mqtt_bridge import MqttBus
from plcassistant.io.mqtt_topics import (
    DEFAULT_INSTANCE_ID,
    MQTT_QOS,
    MqttTagPayload,
    parse_tag_topic,
    tag_in_topic,
    tag_out_topic,
)
from plcassistant.io.quality import QualityStatus, ReasonCode


class MqttEntityBridge:
    """Thin-integration MQTT client toward the Soft-PLC App."""

    def __init__(
        self,
        bus: MqttBus,
        table: BindingTable,
        entities: MockEntityStore,
        *,
        instance_id: str = DEFAULT_INSTANCE_ID,
    ) -> None:
        self._bus = bus
        self._table = table
        self._entities = entities
        self.instance_id = instance_id
        self._pending_out: dict[str, MqttTagPayload] = {}
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._bus.subscribe(tag_out_topic(self.instance_id, "+"), self._on_out)
        self._started = True

    def _on_out(self, topic: str, payload: bytes) -> None:
        parsed = parse_tag_topic(topic)
        if parsed is None:
            return
        instance_id, tag, direction = parsed
        if instance_id != self.instance_id or direction != "out":
            return
        try:
            sample = MqttTagPayload.decode(payload)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError):
            sample = MqttTagPayload(
                value=None,
                status=QualityStatus.BAD,
                reason=ReasonCode.FAULT,
            )
        self._pending_out[tag] = sample

    def publish_inputs(self) -> tuple[str, ...]:
        """Publish IN samples for bindings that read entities → Soft-PLC."""
        published: list[str] = []
        for binding in self._table.bindings:
            if not binding.direction.reads:
                continue
            sample = self._entities.get(binding.entity)
            # Entity raw → engineering for Soft-PLC wire (bindings own units).
            try:
                eng = binding.to_engineering(float(sample.value))
            except (TypeError, ValueError):
                eng = sample.value
            payload = MqttTagPayload.now(eng, sample.status, sample.reason)
            self._bus.publish(
                tag_in_topic(self.instance_id, binding.tag),
                payload.encode(),
                qos=MQTT_QOS,
                retain=False,
            )
            published.append(binding.tag)
        return tuple(published)

    def apply_outputs(self, *, clear: bool = True) -> tuple[str, ...]:
        """Apply buffered OUT samples into the entity store (engineering → raw)."""
        applied: list[str] = []
        by_tag = {b.tag: b for b in self._table.bindings if b.direction.writes}
        for tag, sample in list(self._pending_out.items()):
            binding = by_tag.get(tag)
            if binding is None:
                continue
            try:
                raw = binding.to_raw(float(sample.value))
            except (TypeError, ValueError):
                raw = sample.value
            self._entities.set(binding.entity, raw, sample.status, sample.reason)
            applied.append(tag)
            if clear:
                self._pending_out.pop(tag, None)
        return tuple(applied)

    def publish_command(self, name: str, payload: str = "1") -> None:
        from plcassistant.io.mqtt_topics import cmd_topic

        self._bus.publish(
            cmd_topic(self.instance_id, name),
            payload.encode("utf-8"),
            qos=MQTT_QOS,
            retain=False,
        )


def default_wedge_binding_config() -> dict[str, Any]:
    """Wedge process I/O bindings for packaging demos (SWD-145).

    Plant PVs (``LT_*``, ``FT_INLET``) are Soft-PLC **IN** (MQTT ≡ field);
    the thin integration owns the stand-alone simulator (SWD-146). Operator
    writable request is ``SP_LEVEL_REQ`` IN. Active SPs and ``CMD_SPEED`` are
    Soft-PLC OUT. Aligned with ``docs/wedge/02-io-hmi-contract.md``.
    """
    return {
        "tags": {
            "LT_TANK": {"default": 0.15, "unit": "m"},
            "LT_RES": {"default": 0.20, "unit": "m"},
            "FT_INLET": {"default": 0.0, "unit": "L/min"},
            "SP_LEVEL_REQ": {"default": 0.20, "unit": "m"},
            "SP_LEVEL": {"default": 0.20, "unit": "m"},
            "SP_FLOW": {"default": 0.0, "unit": "L/min"},
            "CMD_SPEED": {"default": 0.0, "unit": "pct"},
            "MODE": {"default": "STOP", "unit": None},
            "PERM_OK": {"default": False, "unit": None},
            "TRIP_ACTIVE": {"default": False, "unit": None},
        },
        "bindings": [
            {
                "tag": "SP_LEVEL_REQ",
                "entity": "number.plcassistant_sp_level_req",
                "direction": "IN",
                "scale": 1.0,
                "offset": 0.0,
            },
            {
                "tag": "LT_TANK",
                "entity": "number.plcassistant_lt_tank_in",
                "direction": "IN",
                "scale": 1.0,
                "offset": 0.0,
            },
            {
                "tag": "LT_RES",
                "entity": "number.plcassistant_lt_res_in",
                "direction": "IN",
                "scale": 1.0,
                "offset": 0.0,
            },
            {
                "tag": "FT_INLET",
                "entity": "number.plcassistant_ft_inlet_in",
                "direction": "IN",
                "scale": 1.0,
                "offset": 0.0,
            },
            {
                "tag": "CMD_SPEED",
                "entity": "sensor.plcassistant_cmd_speed",
                "direction": "OUT",
                "scale": 1.0,
                "offset": 0.0,
            },
            {
                "tag": "SP_LEVEL",
                "entity": "sensor.plcassistant_sp_level",
                "direction": "OUT",
                "scale": 1.0,
                "offset": 0.0,
            },
            {
                "tag": "SP_FLOW",
                "entity": "sensor.plcassistant_sp_flow",
                "direction": "OUT",
                "scale": 1.0,
                "offset": 0.0,
            },
            {
                "tag": "MODE",
                "entity": "sensor.plcassistant_mode",
                "direction": "OUT",
                "scale": 1.0,
                "offset": 0.0,
            },
            {
                "tag": "PERM_OK",
                "entity": "sensor.plcassistant_perm_ok",
                "direction": "OUT",
                "scale": 1.0,
                "offset": 0.0,
            },
            {
                "tag": "TRIP_ACTIVE",
                "entity": "sensor.plcassistant_trip_active",
                "direction": "OUT",
                "scale": 1.0,
                "offset": 0.0,
            },
        ],
    }


__all__ = [
    "MqttEntityBridge",
    "default_wedge_binding_config",
]
