"""Mock / binding number platforms — writable operator request + plant nudges."""

from __future__ import annotations

import json
import math
from pathlib import Path

from homeassistant.components.mqtt import async_subscribe
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_BINDINGS, CONF_INSTANCE_ID, CONF_MOCK_MODE, DOMAIN
from .entity_cleanup import expected_plant_number_unique_id
from .ha_config_bridge import write_input_tag
from .mqtt_topics import tag_in_topic

# Friendly operator ranges for known IN tags (request SP + plant nudges).
_TAG_META: dict[str, dict] = {
    "SP_LEVEL_REQ": {
        "name": "PLCAssistant Level setpoint",
        "min": 0.0,
        "max": 0.40,
        "step": 0.01,
        "unit": "m",
        "object_id": "plcassistant_sp_level_req",
        "default": 0.20,
    },
    "LT_TANK": {
        "name": "PLCAssistant Tank level (IN)",
        "min": 0.0,
        "max": 0.40,
        "step": 0.01,
        "unit": "m",
        "object_id": "plcassistant_lt_tank_in",
        "default": 0.15,
    },
    "LT_RES": {
        "name": "PLCAssistant Reservoir level (IN)",
        "min": 0.0,
        "max": 0.30,
        "step": 0.01,
        "unit": "m",
        "object_id": "plcassistant_lt_res_in",
        "default": 0.20,
    },
    "FT_INLET": {
        "name": "PLCAssistant Inlet flow (IN)",
        "min": 0.0,
        "max": 20.0,
        "step": 0.1,
        "unit": "L/min",
        "object_id": "plcassistant_ft_inlet_in",
        "default": 0.0,
    },
}

_PLANT_IN_TAGS = frozenset({"LT_TANK", "LT_RES", "FT_INLET"})


def _object_id_from_entity(entity: str, fallback: str) -> str:
    """``number.plcassistant_sp_level_req`` → ``plcassistant_sp_level_req``."""
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
                entity_id=str(binding.get("entity") or ""),
            )
        )
    async_add_entities(entities)


class PlcAssistantRequestNumber(NumberEntity):
    """Writable operator request / plant nudge Number."""

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
        self._unsub = None
        meta = _TAG_META.get(tag, {})
        self._attr_name = meta.get("name", f"PLCAssistant {tag}")
        # SWD-170: plant Numbers use stable instance+tag unique_ids.
        # Request SP keeps `_req` suffix (and entry_id) so Lovelace Level setpoint
        # does not orphan after reload (unique_id churn → entity_id_2).
        if tag in _PLANT_IN_TAGS:
            self._attr_unique_id = expected_plant_number_unique_id(instance_id, tag)
        else:
            self._attr_unique_id = f"{entry_id}_{tag}_req"
        object_id = meta.get("object_id") or _object_id_from_entity(
            entity_id, f"plcassistant_{tag.lower()}"
        )
        # Pin entity_id to binding / Lovelace contract (SWD-133).
        self._attr_suggested_object_id = object_id
        self.entity_id = f"number.{object_id}"
        self._attr_native_min_value = float(meta.get("min", -1.0e6))
        self._attr_native_max_value = float(meta.get("max", 1.0e6))
        self._attr_native_step = float(meta.get("step", 0.001))
        if "unit" in meta:
            self._attr_native_unit_of_measurement = meta["unit"]
        if "default" in meta:
            self._attr_native_value = float(meta["default"])
        else:
            self._attr_native_value = 0.0
        # SWD-169: box mode for readable nudge values (Process display is sensors).
        self._attr_mode = NumberMode.BOX

    def _plant_simulator(self):
        store = self.hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
        return store.get("plant_simulator")

    def _simulator_owns(self) -> bool:
        if self._tag not in _PLANT_IN_TAGS:
            return False
        sim = self._plant_simulator()
        return sim is not None and sim.owns_plant_tag(self._tag)

    def _apply_eng_value(self, eng: float) -> bool:
        """Update display from engineering units; True when state should be written."""
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

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        eng = (float(value) * self._scale) + self._offset
        # SWD-146: plant Numbers nudge the simulator — do not compete on MQTT IN.
        if self._simulator_owns():
            self._plant_simulator().set_tag(self._tag, eng)
            self.async_write_ha_state()
            return
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
        # Shared-config fallback when MQTT never reaches Soft-PLC (SWD-141).
        # Operator request tags only — plant process↔PLC stays MQTT (SWD-145).
        if self._tag == "SP_LEVEL_REQ":
            store = self.hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
            root = store.get("config_root")
            if isinstance(root, Path):
                await self.hass.async_add_executor_job(
                    write_input_tag,
                    self._tag,
                    eng,
                    "GOOD",
                    None,
                    root,
                )
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Publish operator request, or hydrate/subscribe for simulator plant IN."""
        await super().async_added_to_hass()
        if self._simulator_owns():
            # SWD-169/170: hydrate from in_values cache, then live plant outputs.
            store = self.hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
            cached = (store.get("in_values") or {}).get(str(self._tag).upper())
            hydrated = False
            if cached and self._apply_payload(str(cached)):
                self.async_write_ha_state()
                hydrated = True
            if not hydrated:
                sim = self._plant_simulator()
                try:
                    outs = sim.plant.model.outputs()
                    tag_key = str(self._tag).upper()
                    eng = outs.get(tag_key, outs.get(self._tag))
                    if eng is not None and self._apply_eng_value(float(eng)):
                        self.async_write_ha_state()
                        hydrated = True
                except Exception:  # noqa: BLE001 — never abort entity add on bad model
                    pass
            if not hydrated and self._attr_native_value is not None:
                self.async_write_ha_state()

            async def _on_plant_bus(event: Event) -> None:
                if event.data.get("entry_id") != self._entry_id:
                    return
                if str(event.data.get("tag") or "").upper() != str(self._tag).upper():
                    return
                if self._apply_payload(str(event.data.get("payload") or "")):
                    self.async_write_ha_state()

            self.async_on_remove(
                self.hass.bus.async_listen(f"{DOMAIN}_plant_in", _on_plant_bus)
            )

            async def _on_plant_mqtt(msg) -> None:
                try:
                    raw = msg.payload
                    text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
                except UnicodeDecodeError:
                    return
                if self._apply_payload(text):
                    self.async_write_ha_state()

            # Secondary: MQTT IN (Soft-PLC / external) still refreshes HMI.
            self._unsub = await async_subscribe(
                self.hass,
                tag_in_topic(self._instance_id, self._tag),
                _on_plant_mqtt,
                qos=0,
            )
            return
        if self._attr_native_value is not None:
            await self.async_set_native_value(float(self._attr_native_value))

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        await super().async_will_remove_from_hass()
