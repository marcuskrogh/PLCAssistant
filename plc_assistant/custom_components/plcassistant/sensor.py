"""Read-only Soft-PLC OUT tags + App status as sensors."""

from __future__ import annotations

import json
import math

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_BINDINGS,
    CONF_DYNAMICS_PARAMS,
    CONF_DYNAMICS_PRESET,
    CONF_INSTANCE_ID,
    CONF_MOCK_MODE,
    DOMAIN,
)
from .entity_cleanup import expected_plant_sensor_unique_id
from .mqtt_topics import parse_app_status_payload

_TAG_META: dict[str, dict] = {
    "CMD_SPEED": {
        "name": "PLCAssistant Pump speed command",
        "unit": "%",
        "object_id": "plcassistant_cmd_speed",
        "kind": "number",
    },
    "SP_LEVEL": {
        "name": "PLCAssistant Active level setpoint",
        "unit": "m",
        "object_id": "plcassistant_sp_level",
        "kind": "number",
    },
    "SP_FLOW": {
        "name": "PLCAssistant Active flow setpoint",
        "unit": "L/min",
        "object_id": "plcassistant_sp_flow",
        "kind": "number",
    },
    "MODE": {
        "name": "PLCAssistant Mode",
        "object_id": "plcassistant_mode",
        "kind": "text",
    },
    "PERM_OK": {
        "name": "PLCAssistant Start ready",
        "object_id": "plcassistant_perm_ok",
        "kind": "bool",
    },
    "TRIP_ACTIVE": {
        "name": "PLCAssistant Trip active",
        "object_id": "plcassistant_trip_active",
        "kind": "bool",
    },
}

# SWD-170: plant PVs as Sensors for Operate HMI (Numbers remain for nudges).
_PLANT_IN_META: dict[str, dict] = {
    "LT_TANK": {
        "name": "PLCAssistant Tank level",
        "unit": "m",
        "object_id": "plcassistant_lt_tank_in",
        "default": 0.15,
        "icon": "mdi:gauge",
    },
    "LT_RES": {
        "name": "PLCAssistant Reservoir level",
        "unit": "m",
        "object_id": "plcassistant_lt_res_in",
        "default": 0.20,
        "icon": "mdi:water",
    },
    "FT_INLET": {
        "name": "PLCAssistant Inlet flow",
        "unit": "L/min",
        "object_id": "plcassistant_ft_inlet_in",
        "default": 0.0,
        "icon": "mdi:pipe",
    },
}


def _object_id_from_entity(entity: str, fallback: str) -> str:
    text = str(entity or "").strip()
    if "." in text:
        return text.split(".", 1)[1] or fallback
    return text or fallback


def _payload_value(body: dict):
    return body.get("value")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        PlcAssistantStatusSensor(entry.entry_id, data[CONF_INSTANCE_ID])
    ]
    if data.get(CONF_MOCK_MODE, True):
        entities.append(
            PlcAssistantDynamicsPresetSensor(entry.entry_id, data[CONF_INSTANCE_ID])
        )
    if not data.get(CONF_MOCK_MODE, True):
        async_add_entities(entities)
        return
    for binding in data.get(CONF_BINDINGS) or []:
        direction = str(binding.get("direction", "")).upper()
        if direction not in ("OUT", "INOUT"):
            continue
        scale = float(binding.get("scale", 1.0))
        offset = float(binding.get("offset", 0.0))
        tag = binding["tag"]
        meta = _TAG_META.get(tag, {})
        kind = meta.get("kind", "number")
        entity_id = str(binding.get("entity") or "")
        if kind == "text":
            entities.append(
                PlcAssistantTextOutSensor(
                    entry.entry_id,
                    data[CONF_INSTANCE_ID],
                    tag,
                    entity_id=entity_id,
                )
            )
        elif kind == "bool":
            entities.append(
                PlcAssistantBoolOutSensor(
                    entry.entry_id,
                    data[CONF_INSTANCE_ID],
                    tag,
                    entity_id=entity_id,
                )
            )
        else:
            entities.append(
                PlcAssistantOutSensor(
                    entry.entry_id,
                    data[CONF_INSTANCE_ID],
                    tag,
                    scale,
                    offset,
                    entity_id=entity_id,
                )
            )
    # SWD-170: plant IN display Sensors (Operate Process card).
    for binding in data.get(CONF_BINDINGS) or []:
        direction = str(binding.get("direction", "")).upper()
        if direction not in ("IN", "INOUT"):
            continue
        tag = str(binding.get("tag") or "").upper()
        if tag not in _PLANT_IN_META:
            continue
        scale = float(binding.get("scale", 1.0))
        offset = float(binding.get("offset", 0.0))
        entities.append(
            PlcAssistantPlantInSensor(
                entry.entry_id,
                data[CONF_INSTANCE_ID],
                tag,
                scale,
                offset,
            )
        )
    async_add_entities(entities)


class PlcAssistantStatusSensor(SensorEntity):
    """App scan status from ``plcassistant/{id}/status`` (running/stopped/fault)."""

    _attr_should_poll = False

    def __init__(self, entry_id: str, instance_id: str) -> None:
        self._entry_id = entry_id
        self._instance_id = instance_id
        self._attr_name = "PLCAssistant Status"
        self._attr_unique_id = f"{entry_id}_status"
        self._attr_suggested_object_id = "plcassistant_status"
        self.entity_id = "sensor.plcassistant_status"
        self._attr_native_value = "offline"
        self._attr_icon = "mdi:lan-pending"

    def _apply_status_payload(self, payload: str) -> bool:
        """Parse status JSON and update attributes. True only when state changed."""
        state = parse_app_status_payload(payload)
        if state is None:
            return False
        icons = {
            "running": "mdi:play-circle",
            "stopped": "mdi:stop-circle",
            "fault": "mdi:alert-circle",
            "offline": "mdi:lan-disconnect",
        }
        icon = icons.get(state, "mdi:lan-pending")
        if state == self._attr_native_value and icon == self._attr_icon:
            return False
        self._attr_native_value = state
        self._attr_icon = icon
        return True

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        # Hydrate from cache filled by retained MQTT before this listener existed.
        store = self.hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
        cached = store.get("status_payload")
        if cached and self._apply_status_payload(str(cached)):
            self.async_write_ha_state()

        async def _on_status(event: Event) -> None:
            if event.data.get("entry_id") != self._entry_id:
                return
            if self._apply_status_payload(str(event.data.get("payload") or "")):
                self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_status", _on_status)
        )


class PlcAssistantDynamicsPresetSensor(SensorEntity):
    """Active plant dynamics preset (SWD-143)."""

    _attr_should_poll = False
    _attr_icon = "mdi:graph"

    def __init__(self, entry_id: str, instance_id: str) -> None:
        self._entry_id = entry_id
        self._instance_id = instance_id
        self._attr_name = "PLCAssistant Dynamics preset"
        self._attr_unique_id = f"{entry_id}_dynamics_preset"
        self._attr_suggested_object_id = "plcassistant_dynamics_preset"
        self.entity_id = "sensor.plcassistant_dynamics_preset"
        self._attr_native_value = "skid"
        self._attr_extra_state_attributes: dict = {"params": {}}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._refresh_from_store()
        self.async_write_ha_state()

    def _refresh_from_store(self) -> None:
        store = self.hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
        preset = store.get(CONF_DYNAMICS_PRESET)
        sim = store.get("plant_simulator")
        if sim is not None and getattr(sim, "preset", None):
            preset = sim.preset
        if not preset:
            preset = "skid"
        params = store.get(CONF_DYNAMICS_PARAMS)
        if sim is not None and getattr(sim, "params", None) is not None:
            params = dict(sim.params)
        if not isinstance(params, dict):
            params = {}
        self._attr_native_value = str(preset)
        self._attr_extra_state_attributes = {"params": dict(params)}


class PlcAssistantOutSensor(SensorEntity):
    """Soft-PLC OUT sink — numeric PVs / active SPs / CMD_SPEED."""

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
        if "unit" in meta and meta["unit"]:
            self._attr_native_unit_of_measurement = meta["unit"]
        self._attr_native_value = 0.0

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        def _apply_payload(payload: str) -> bool:
            try:
                body = json.loads(payload or "{}")
                eng = float(_payload_value(body) or 0.0)
                if not math.isfinite(eng):
                    return False
                raw = (eng - self._offset) / self._scale
            except (TypeError, ValueError, ZeroDivisionError, UnicodeDecodeError):
                return False
            self._attr_native_value = raw
            return True

        store = self.hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
        cached = (store.get("out_values") or {}).get(self._tag)
        if cached and _apply_payload(str(cached)):
            self.async_write_ha_state()

        async def _on_out(event: Event) -> None:
            if event.data.get("entry_id") != self._entry_id:
                return
            if event.data.get("tag") != self._tag:
                return
            if _apply_payload(str(event.data.get("payload") or "")):
                self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_tag_out", _on_out)
        )


class PlcAssistantPlantInSensor(SensorEntity):
    """Plant PV display Sensor — hydrate from simulator cache / plant_in bus."""

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
        self._tag = str(tag).upper()
        self._scale = scale if scale else 1.0
        self._offset = offset
        meta = _PLANT_IN_META.get(self._tag, {})
        self._attr_name = meta.get("name", f"PLCAssistant {self._tag}")
        self._attr_unique_id = expected_plant_sensor_unique_id(instance_id, self._tag)
        object_id = meta.get("object_id") or f"plcassistant_{self._tag.lower()}_in"
        self._attr_suggested_object_id = object_id
        self.entity_id = f"sensor.{object_id}"
        if meta.get("unit"):
            self._attr_native_unit_of_measurement = meta["unit"]
        if meta.get("icon"):
            self._attr_icon = meta["icon"]
        self._attr_native_value = float(meta.get("default", 0.0))

    def _plant_simulator(self):
        store = self.hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
        return store.get("plant_simulator")

    def _apply_eng_value(self, eng: float) -> bool:
        try:
            value = float(eng)
        except (TypeError, ValueError):
            return False
        if not math.isfinite(value):
            return False
        display = (value - self._offset) / self._scale if self._scale else value
        if self._attr_native_value is not None and abs(
            float(self._attr_native_value) - display
        ) < 1e-12:
            return False
        self._attr_native_value = display
        return True

    def _apply_payload(self, payload: str) -> bool:
        try:
            body = json.loads(payload or "{}")
            if not isinstance(body, dict) or "value" not in body:
                return False
            return self._apply_eng_value(float(body["value"]))
        except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        store = self.hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
        cached = (store.get("in_values") or {}).get(self._tag)
        hydrated = False
        if cached and self._apply_payload(str(cached)):
            self.async_write_ha_state()
            hydrated = True
        if not hydrated:
            sim = self._plant_simulator()
            if sim is not None:
                try:
                    outs = sim.plant.model.outputs()
                    eng = outs.get(self._tag)
                    if eng is not None and self._apply_eng_value(float(eng)):
                        self.async_write_ha_state()
                        hydrated = True
                except Exception:  # noqa: BLE001
                    pass
        if not hydrated and self._attr_native_value is not None:
            self.async_write_ha_state()

        async def _on_plant_bus(event: Event) -> None:
            if event.data.get("entry_id") != self._entry_id:
                return
            if str(event.data.get("tag") or "").upper() != self._tag:
                return
            if self._apply_payload(str(event.data.get("payload") or "")):
                self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_plant_in", _on_plant_bus)
        )


class PlcAssistantTextOutSensor(SensorEntity):
    """Soft-PLC OUT string tag (e.g. MODE)."""

    _attr_should_poll = False

    def __init__(
        self,
        entry_id: str,
        instance_id: str,
        tag: str,
        *,
        entity_id: str = "",
    ) -> None:
        self._entry_id = entry_id
        self._instance_id = instance_id
        self._tag = tag
        meta = _TAG_META.get(tag, {})
        self._attr_name = meta.get("name", f"PLCAssistant {tag}")
        self._attr_unique_id = f"{entry_id}_{tag}_out"
        object_id = meta.get("object_id") or _object_id_from_entity(
            entity_id, f"plcassistant_{tag.lower()}"
        )
        self._attr_suggested_object_id = object_id
        self.entity_id = f"sensor.{object_id}"
        self._attr_native_value = "STOP" if tag == "MODE" else "unknown"
        self._attr_icon = "mdi:state-machine"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        def _apply_payload(payload: str) -> bool:
            try:
                body = json.loads(payload or "{}")
                value = _payload_value(body)
            except (TypeError, ValueError, UnicodeDecodeError):
                return False
            if value is None:
                return False
            text = str(value).strip().upper()
            if not text:
                return False
            self._attr_native_value = text
            if self._tag == "MODE":
                icons = {
                    "STOP": "mdi:stop-circle-outline",
                    "RUNNING": "mdi:play-circle-outline",
                    "TRIPPED": "mdi:alert-octagon",
                }
                self._attr_icon = icons.get(text, "mdi:state-machine")
            return True

        store = self.hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
        cached = (store.get("out_values") or {}).get(self._tag)
        if cached and _apply_payload(str(cached)):
            self.async_write_ha_state()

        async def _on_out(event: Event) -> None:
            if event.data.get("entry_id") != self._entry_id:
                return
            if event.data.get("tag") != self._tag:
                return
            if _apply_payload(str(event.data.get("payload") or "")):
                self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_tag_out", _on_out)
        )


class PlcAssistantBoolOutSensor(SensorEntity):
    """Soft-PLC OUT bool tag as on/off text (PERM_OK, TRIP_ACTIVE)."""

    _attr_should_poll = False

    def __init__(
        self,
        entry_id: str,
        instance_id: str,
        tag: str,
        *,
        entity_id: str = "",
    ) -> None:
        self._entry_id = entry_id
        self._instance_id = instance_id
        self._tag = tag
        meta = _TAG_META.get(tag, {})
        self._attr_name = meta.get("name", f"PLCAssistant {tag}")
        self._attr_unique_id = f"{entry_id}_{tag}_out"
        object_id = meta.get("object_id") or _object_id_from_entity(
            entity_id, f"plcassistant_{tag.lower()}"
        )
        self._attr_suggested_object_id = object_id
        self.entity_id = f"sensor.{object_id}"
        self._attr_native_value = "off"
        self._attr_icon = "mdi:checkbox-blank-circle-outline"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        def _apply_payload(payload: str) -> bool:
            try:
                body = json.loads(payload or "{}")
                value = _payload_value(body)
            except (TypeError, ValueError, UnicodeDecodeError):
                return False
            truthy = value in (True, 1, 1.0, "1", "true", "True", "on", "ON")
            self._attr_native_value = "on" if truthy else "off"
            if self._tag == "PERM_OK":
                self._attr_icon = (
                    "mdi:check-circle" if truthy else "mdi:close-circle"
                )
            elif self._tag == "TRIP_ACTIVE":
                self._attr_icon = (
                    "mdi:alert-circle" if truthy else "mdi:shield-check"
                )
            return True

        store = self.hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
        cached = (store.get("out_values") or {}).get(self._tag)
        if cached and _apply_payload(str(cached)):
            self.async_write_ha_state()

        async def _on_out(event: Event) -> None:
            if event.data.get("entry_id") != self._entry_id:
                return
            if event.data.get("tag") != self._tag:
                return
            if _apply_payload(str(event.data.get("payload") or "")):
                self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_tag_out", _on_out)
        )
