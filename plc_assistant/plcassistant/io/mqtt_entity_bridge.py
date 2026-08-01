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
    """Demo process I/O bindings from Programs' Datablock access (SWD-184).

    Prefer ``default_tank_datablock_catalog`` for Datablock-aware callers.
    This helper remains for BindingTable consumers and returns the merged
    flat tags+bindings view for the demo Program access map.
    """
    from plcassistant.io.datablock import (
        binding_rows_from_table,
        default_program_datablock_access,
        default_tank_datablock_catalog,
        union_program_access_ids,
    )

    catalog = default_tank_datablock_catalog()
    table = catalog.binding_table_for(
        union_program_access_ids(default_program_datablock_access())
    )
    return {
        "tags": {
            name: {"default": decl.default, "unit": decl.unit}
            for name, decl in table.tags.items()
        },
        "bindings": binding_rows_from_table(table),
    }


__all__ = [
    "MqttEntityBridge",
    "default_wedge_binding_config",
]
