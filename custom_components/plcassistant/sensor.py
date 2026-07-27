"""Mock / binding sensor platform — publishes tag IN over MQTT."""

from __future__ import annotations

import json

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
    entities = []
    for binding in data.get(CONF_BINDINGS) or []:
        if str(binding.get("direction", "")).upper() not in ("IN", "INOUT"):
            continue
        entities.append(
            PlcAssistantMockSensor(
                entry.entry_id,
                data[CONF_INSTANCE_ID],
                binding["tag"],
                float(binding.get("scale", 1.0)),
                float(binding.get("offset", 0.0)),
            )
        )
    async_add_entities(entities)


class PlcAssistantMockSensor(SensorEntity):
    """Mock IN entity: writing native_value publishes Soft-PLC tag IN."""

    _attr_should_poll = False

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
        self._scale = scale
        self._offset = offset
        self._attr_name = f"PLCAssistant {tag}"
        self._attr_unique_id = f"{entry_id}_{tag}_in"
        self._attr_native_value = 0.0

    async def async_set_native_value(self, value: float) -> None:
        """Allow services/tests to push a mock sample toward the App."""
        self._attr_native_value = value
        # Engineering on the wire (Soft-PLC image units).
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
