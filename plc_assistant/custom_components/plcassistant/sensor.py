"""Read-only Soft-PLC OUT tags as sensors (PVs, active SPs, CMD_SPEED)."""

from __future__ import annotations

import json

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_BINDINGS, CONF_INSTANCE_ID, CONF_MOCK_MODE, DOMAIN

_TAG_META: dict[str, dict] = {
    "LT_TANK": {
        "name": "PLCAssistant Tank level",
        "unit": "m",
        "object_id": "plcassistant_lt_tank",
    },
    "LT_RES": {
        "name": "PLCAssistant Reservoir level",
        "unit": "m",
        "object_id": "plcassistant_lt_res",
    },
    "FT_INLET": {
        "name": "PLCAssistant Inlet flow",
        "unit": "L/min",
        "object_id": "plcassistant_ft_inlet",
    },
    "CMD_SPEED": {
        "name": "PLCAssistant Pump speed command",
        "unit": "%",
        "object_id": "plcassistant_cmd_speed",
    },
    "SP_LEVEL": {
        "name": "PLCAssistant Active level setpoint",
        "unit": "m",
        "object_id": "plcassistant_sp_level",
    },
    "SP_FLOW": {
        "name": "PLCAssistant Active flow setpoint",
        "unit": "L/min",
        "object_id": "plcassistant_sp_flow",
    },
}


def _object_id_from_entity(entity: str, fallback: str) -> str:
    text = str(entity or "").strip()
    if "." in text:
        return text.split(".", 1)[1] or fallback
    return text or fallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    if not data.get(CONF_MOCK_MODE, True):
        return
    entities: list[SensorEntity] = []
    for binding in data.get(CONF_BINDINGS) or []:
        direction = str(binding.get("direction", "")).upper()
        if direction not in ("OUT", "INOUT"):
            continue
        scale = float(binding.get("scale", 1.0))
        offset = float(binding.get("offset", 0.0))
        tag = binding["tag"]
        entities.append(
            PlcAssistantOutSensor(
                entry.entry_id,
                data[CONF_INSTANCE_ID],
                tag,
                scale,
                offset,
                entity_id=str(binding.get("entity") or ""),
            )
        )
    async_add_entities(entities)


class PlcAssistantOutSensor(SensorEntity):
    """Soft-PLC OUT sink — updated from MQTT tag OUT (not operator-writable)."""

    _attr_should_poll = False

    def __init__(
        self,
        entry_id: str,
        instance_id: str,
        tag: str,
        scale: float,
        offset: float,
        *,
        entity_id: str = "",
    ) -> None:
        self._entry_id = entry_id
        self._instance_id = instance_id
        self._tag = tag
        self._scale = scale if scale else 1.0
        self._offset = offset
        meta = _TAG_META.get(tag, {})
        self._attr_name = meta.get("name", f"PLCAssistant {tag}")
        self._attr_unique_id = f"{entry_id}_{tag}_out"
        object_id = meta.get("object_id") or _object_id_from_entity(
            entity_id, f"plcassistant_{tag.lower()}"
        )
        self._attr_suggested_object_id = object_id
        self.entity_id = f"sensor.{object_id}"
        if "unit" in meta:
            self._attr_native_unit_of_measurement = meta["unit"]
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
