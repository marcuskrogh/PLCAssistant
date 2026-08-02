"""Compound PID loop sensors for Lovelace faceplates (SWD-183).

One climate-like sensor per demo loop: state is SP-source mode string;
attributes carry PV / SP sources / CV / tunings and related entity ids.
"""

from __future__ import annotations

import json
import math
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

# Soft-PLC tag map mirrored from plcassistant.io.pid_loop (no Soft-PLC import
# in the thin integration CI path).
_LEVEL = {
    "loop_id": "level",
    "pv": "LT_TANK",
    "sp": "SP_LEVEL",
    "sp_man": "SP_LEVEL_MAN",
    "sp_auto": "SP_LEVEL_REQ",
    "sp_rem": "SP_LEVEL_REM",
    "mode": "LEVEL_MODE",
    "cv": "SP_FLOW_AUTO",
    "kp": "LEVEL_KP",
    "ki": "LEVEL_KI",
    "kd": "LEVEL_KD",
    "pv_entity": "sensor.plcassistant_lt_tank_in",
    "sp_entity": "sensor.plcassistant_sp_level",
    "sp_man_entity": "number.plcassistant_sp_level_man",
    "sp_auto_entity": "number.plcassistant_sp_level_req",
    "sp_rem_entity": "number.plcassistant_sp_level_rem",
    "mode_entity": "number.plcassistant_level_mode",
    "cv_entity": "sensor.plcassistant_sp_flow_auto",
    "kp_entity": "number.plcassistant_level_kp",
    "ki_entity": "number.plcassistant_level_ki",
}

_FLOW = {
    "loop_id": "flow",
    "pv": "FT_INLET",
    "sp": "SP_FLOW",
    "sp_man": "SP_FLOW_MAN",
    "sp_auto": "SP_FLOW_AUTO",
    "sp_rem": "SP_FLOW_REM",
    "mode": "FLOW_MODE",
    "cv": "CMD_SPEED",
    "kp": "FLOW_KP",
    "ki": "FLOW_KI",
    "kd": "FLOW_KD",
    "pv_entity": "sensor.plcassistant_ft_inlet_in",
    "sp_entity": "sensor.plcassistant_sp_flow",
    "sp_man_entity": "number.plcassistant_sp_flow_man",
    "sp_auto_entity": "sensor.plcassistant_sp_flow_auto",
    "sp_rem_entity": "number.plcassistant_sp_flow_rem",
    "mode_entity": "number.plcassistant_flow_mode",
    "cv_entity": "sensor.plcassistant_cmd_speed",
    "kp_entity": "number.plcassistant_flow_kp",
    "ki_entity": "number.plcassistant_flow_ki",
}

DEMO_PID_LOOPS: tuple[dict[str, str], ...] = (_LEVEL, _FLOW)

_MODE_NAMES = {0: "manual", 1: "automatic", 2: "remote"}
_MODE_ALIASES = {
    "man": "manual",
    "manual": "manual",
    "auto": "automatic",
    "automatic": "automatic",
    "rem": "remote",
    "remote": "remote",
    "0": "manual",
    "1": "automatic",
    "2": "remote",
}


def _payload_value(payload: str | None) -> Any | None:
    if payload is None:
        return None
    try:
        body = json.loads(payload or "{}")
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(body, dict) or "value" not in body:
        return None
    return body.get("value")


def _cache_value(store: dict, tag: str) -> Any | None:
    key = str(tag).upper()
    for bucket in ("out_values", "in_values"):
        cached = (store.get(bucket) or {}).get(key)
        if cached is None and key != tag:
            cached = (store.get(bucket) or {}).get(tag)
        val = _payload_value(str(cached) if cached is not None else None)
        if val is not None:
            return val
    return None


def _parse_mode(raw: Any) -> str:
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        try:
            code = int(raw)
        except (TypeError, ValueError):
            return "manual"
        return _MODE_NAMES.get(code, "manual")
    key = str(raw or "").strip().lower()
    # Unknown aliases fall back to manual — Soft-PLC ``SpSourceMode.parse``
    # raises ValueError and skid_scan resolves to MANUAL the same way (SWD-220).
    return _MODE_ALIASES.get(key, "manual")


def _select_sp(mode: str, man: float, auto: float, rem: float) -> float:
    if mode == "manual":
        return man
    if mode == "remote":
        return rem
    return auto


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(num):
        return default
    return num


def _round_display(value: Any, digits: int = 2) -> float | None:
    """Round a numeric faceplate attribute to ``digits`` dp, or None if absent."""
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(num):
        return None
    return round(num, digits)


async def async_setup_pid_loop_sensors(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Register compound PID loop sensors for the mock demo."""
    data = hass.data[DOMAIN][entry.entry_id]
    entities = [
        PlcAssistantPidLoopSensor(entry.entry_id, data.get("instance_id") or "default", spec)
        for spec in DEMO_PID_LOOPS
    ]
    async_add_entities(entities)


class PlcAssistantPidLoopSensor(SensorEntity):
    """Climate-like PID faceplate: state = mode; attributes = loop fields."""

    _attr_should_poll = False
    _attr_icon = "mdi:gauge"

    def __init__(self, entry_id: str, instance_id: str, spec: dict[str, str]) -> None:
        self._entry_id = entry_id
        self._instance_id = instance_id
        self._spec = spec
        loop_id = spec["loop_id"]
        self._attr_name = f"PLCAssistant PID {loop_id}"
        self._attr_unique_id = f"{entry_id}_pid_{loop_id}"
        object_id = f"plcassistant_pid_{loop_id}"
        self._attr_suggested_object_id = object_id
        self.entity_id = f"sensor.{object_id}"
        # Cascade demo: level Manual, flow Automatic until store hydrate.
        self._attr_native_value = (
            "automatic" if loop_id == "flow" else "manual"
        )
        self._attr_extra_state_attributes = self._empty_attrs()
        self._watch_tags = frozenset(
            {
                spec["pv"],
                spec["sp"],
                spec["sp_man"],
                spec["sp_auto"],
                spec["sp_rem"],
                spec["mode"],
                spec["cv"],
                spec["kp"],
                spec["ki"],
                spec["kd"],
            }
        )

    def _empty_attrs(self) -> dict[str, Any]:
        spec = self._spec
        return {
            "loop_id": spec["loop_id"],
            "pv": None,
            "sp": None,
            "sp_man": None,
            "sp_auto": None,
            "sp_rem": None,
            "cv": None,
            "kp": None,
            "ki": None,
            "kd": None,
            "pv_entity": spec["pv_entity"],
            "sp_entity": spec["sp_entity"],
            "sp_man_entity": spec["sp_man_entity"],
            "sp_auto_entity": spec["sp_auto_entity"],
            "sp_rem_entity": spec["sp_rem_entity"],
            "mode_entity": spec["mode_entity"],
            "cv_entity": spec["cv_entity"],
            "kp_entity": spec["kp_entity"],
            "ki_entity": spec["ki_entity"],
        }

    def _refresh_from_store(self) -> bool:
        store = self.hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
        spec = self._spec
        mode = _parse_mode(_cache_value(store, spec["mode"]))
        man = _round_display(_cache_value(store, spec["sp_man"])) or 0.0
        auto = _round_display(_cache_value(store, spec["sp_auto"])) or 0.0
        rem = _round_display(_cache_value(store, spec["sp_rem"])) or 0.0
        # Always mux from mode + sources — never prefer stale Soft-PLC SP_* OUT
        # (that made faceplate Set look broken when OUT lagged) (SWD-222).
        sp = _round_display(_select_sp(mode, man, auto, rem)) or 0.0
        attrs = self._empty_attrs()
        attrs.update(
            {
                "pv": _round_display(_cache_value(store, spec["pv"])),
                "sp": sp,
                "sp_man": man,
                "sp_auto": auto,
                "sp_rem": rem,
                "cv": _round_display(_cache_value(store, spec["cv"])),
                "kp": _round_display(_cache_value(store, spec["kp"])),
                "ki": _round_display(_cache_value(store, spec["ki"])),
                "kd": _round_display(_cache_value(store, spec["kd"])),
            }
        )
        changed = mode != self._attr_native_value or attrs != self._attr_extra_state_attributes
        self._attr_native_value = mode
        self._attr_extra_state_attributes = attrs
        return changed

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self._refresh_from_store():
            self.async_write_ha_state()
        else:
            self.async_write_ha_state()

        async def _on_tag(event: Event) -> None:
            if event.data.get("entry_id") != self._entry_id:
                return
            tag = str(event.data.get("tag") or "").upper()
            if tag not in self._watch_tags:
                return
            if self._refresh_from_store():
                self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_tag_out", _on_tag)
        )
        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_plant_in", _on_tag)
        )
        # IN operator tags (mode / SP sources / tunings) arrive on status/file path;
        # also listen for a dedicated IN bus if present, else re-hydrate on any out.
        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_tag_in", _on_tag)
        )


__all__ = [
    "DEMO_PID_LOOPS",
    "PlcAssistantPidLoopSensor",
    "async_setup_pid_loop_sensors",
    "_round_display",
]
