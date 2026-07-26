"""Diagnostic sensors from addon GetStatus."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PlcAssistantCoordinator

_NUMBER_KEYS = (
    ("scan_period_ms", "Scan period", "ms"),
    ("last_cycle_ms", "Last cycle", "ms"),
    ("overrun_count", "Overrun count", None),
    ("bridge_lag_ms", "Bridge lag", "ms"),
    ("stale_binding_count", "Stale bindings", None),
    ("binding_error_count", "Binding errors", None),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PlcAssistantCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[SensorEntity] = [
        PlcDiagNumberSensor(coordinator, entry, key, name, unit)
        for key, name, unit in _NUMBER_KEYS
    ]
    entities.append(PlcRuntimeStateSensor(coordinator, entry))
    async_add_entities(entities)


class PlcDiagNumberSensor(CoordinatorEntity[PlcAssistantCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PlcAssistantCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        unit: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "PLCAssistant",
            "manufacturer": "PLCAssistant",
        }

    @property
    def native_value(self):
        return getattr(self.coordinator.data, self._key)


class PlcRuntimeStateSensor(CoordinatorEntity[PlcAssistantCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Runtime state"

    def __init__(self, coordinator: PlcAssistantCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_runtime_state"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "PLCAssistant",
            "manufacturer": "PLCAssistant",
        }

    @property
    def native_value(self):
        return self.coordinator.data.runtime_state
