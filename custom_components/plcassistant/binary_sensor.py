"""Diagnostic binary sensors."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PlcAssistantCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PlcAssistantCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [
            PlcBridgeConnectedSensor(coordinator, entry),
            PlcFailSafeActiveSensor(coordinator, entry),
        ]
    )


class PlcBridgeConnectedSensor(CoordinatorEntity[PlcAssistantCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Bridge connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: PlcAssistantCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_bridge_connected"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "PLCAssistant",
            "manufacturer": "PLCAssistant",
        }

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.bridge_connected)


class PlcFailSafeActiveSensor(CoordinatorEntity[PlcAssistantCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Fail-safe active"

    def __init__(self, coordinator: PlcAssistantCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_fail_safe_active"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "PLCAssistant",
            "manufacturer": "PLCAssistant",
        }

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.fail_safe_active)
