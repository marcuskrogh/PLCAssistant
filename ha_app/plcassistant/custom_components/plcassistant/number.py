"""Mock / binding number platforms — IN publish + OUT sink over MQTT."""

from __future__ import annotations

import json

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_BINDINGS, CONF_INSTANCE_ID, CONF_MOCK_MODE, DOMAIN
from .mqtt_topics import tag_in_topic


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    if not data.get(CONF_MOCK_MODE, True):
        return
    entities: list[NumberEntity] = []
    for binding in data.get(CONF_BINDINGS) or []:
        direction = str(binding.get("direction", "")).upper()
        scale = float(binding.get("scale", 1.0))
        offset = float(binding.get("offset", 0.0))
        tag = binding["tag"]
        if direction in ("IN", "INOUT"):
            entities.append(
                PlcAssistantMockInNumber(
                    entry.entry_id,
                    data[CONF_INSTANCE_ID],
                    tag,
                    scale,
                    offset,
                )
            )
        if direction in ("OUT", "INOUT"):
            entities.append(
                PlcAssistantMockOutNumber(
                    entry.entry_id,
                    data[CONF_INSTANCE_ID],
                    tag,
                    scale,
                    offset,
                )
            )
    async_add_entities(entities)


class PlcAssistantMockInNumber(NumberEntity):
    """Writable mock IN: setting the number publishes Soft-PLC tag IN."""

    _attr_should_poll = False
    _attr_native_min_value = -1.0e6
    _attr_native_max_value = 1.0e6
    _attr_native_step = 0.001

    def __init__(
        self,
        entry_id: str,
        instance_id: str,
        tag: str,
        scale: float,
        offset: float,
    ) -> None:
        self._entry_id = entry_id
        self._instance_id = instance_id
        self._tag = tag
        self._scale = scale if scale else 1.0
        self._offset = offset
        self._attr_name = f"PLCAssistant {tag} IN"
        self._attr_unique_id = f"{entry_id}_{tag}_in"
        self._attr_native_value = 0.0

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        eng = (float(value) * self._scale) + self._offset
        payload = json.dumps(
            {"value": eng, "status": "GOOD", "reason": None, "ts": None}
        )
        await self.hass.services.async_call(
            "mqtt",
            "publish",
            {
                "topic": tag_in_topic(self._instance_id, self._tag),
                "payload": payload,
                "qos": 1,
                "retain": False,
            },
            blocking=False,
        )
        self.async_write_ha_state()


class PlcAssistantMockOutNumber(NumberEntity):
    """Mock OUT entity updated from Soft-PLC tag OUT MQTT messages."""

    _attr_should_poll = False
    _attr_native_min_value = -1.0e6
    _attr_native_max_value = 1.0e6
    _attr_native_step = 0.1

    def __init__(
        self,
        entry_id: str,
        instance_id: str,
        tag: str,
        scale: float,
        offset: float,
    ) -> None:
        self._entry_id = entry_id
        self._instance_id = instance_id
        self._tag = tag
        self._scale = scale if scale else 1.0
        self._offset = offset
        self._attr_name = f"PLCAssistant {tag} OUT"
        self._attr_unique_id = f"{entry_id}_{tag}_out"
        self._attr_native_value = 0.0

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        async def _on_out(event: Event) -> None:
            if event.data.get("entry_id") != self._entry_id:
                return
            if event.data.get("tag") != self._tag:
                return
            try:
                body = json.loads(event.data.get("payload") or "{}")
                eng = float(body.get("value", 0.0))
                raw = (eng - self._offset) / self._scale
            except (TypeError, ValueError, ZeroDivisionError, UnicodeDecodeError):
                return
            self._attr_native_value = raw
            self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_tag_out", _on_out)
        )
