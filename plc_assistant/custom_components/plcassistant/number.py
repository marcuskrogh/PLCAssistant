"""Mock / binding number platforms — writable operator request tags only."""

from __future__ import annotations

import json

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_BINDINGS, CONF_INSTANCE_ID, CONF_MOCK_MODE, DOMAIN
from .mqtt_topics import tag_in_topic

# Friendly operator ranges for known request tags (SWD-133).
_TAG_META: dict[str, dict] = {
    "SP_LEVEL_REQ": {
        "name": "PLCAssistant Level setpoint",
        "min": 0.0,
        "max": 0.40,
        "step": 0.01,
        "unit": "m",
    },
}


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
        if direction not in ("IN", "INOUT"):
            continue
        scale = float(binding.get("scale", 1.0))
        offset = float(binding.get("offset", 0.0))
        tag = binding["tag"]
        entities.append(
            PlcAssistantRequestNumber(
                entry.entry_id,
                data[CONF_INSTANCE_ID],
                tag,
                scale,
                offset,
            )
        )
    async_add_entities(entities)


class PlcAssistantRequestNumber(NumberEntity):
    """Writable operator request: setting publishes Soft-PLC tag IN."""

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
        self._scale = scale if scale else 1.0
        self._offset = offset
        meta = _TAG_META.get(tag, {})
        self._attr_name = meta.get("name", f"PLCAssistant {tag}")
        self._attr_unique_id = f"{entry_id}_{tag}_req"
        self._attr_native_min_value = float(meta.get("min", -1.0e6))
        self._attr_native_max_value = float(meta.get("max", 1.0e6))
        self._attr_native_step = float(meta.get("step", 0.001))
        if "unit" in meta:
            self._attr_native_unit_of_measurement = meta["unit"]
        # Default level request matches Soft-PLC / wedge ref.
        self._attr_native_value = 0.20 if tag == "SP_LEVEL_REQ" else 0.0

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
