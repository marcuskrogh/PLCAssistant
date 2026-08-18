"""Compound PID loop sensors for Lovelace faceplates (SWD-183).

One climate-like sensor per demo loop: state is SP-source mode string;
attributes carry PV / SP sources / CV / tunings and related entity ids.
"""

from __future__ import annotations

import json
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, round_display

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
    "co_man": "CO_LEVEL_MAN",
    "kp": "LEVEL_KP",
    "ki": "LEVEL_KI",
    "kd": "LEVEL_KD",
    "u0": "LEVEL_U0",
    "beta": "LEVEL_BETA",
    "direct_acting": "LEVEL_DIRECT_ACTING",
    "cv_min": "LEVEL_CV_MIN",
    "cv_max": "LEVEL_CV_MAX",
    "hold_when_stopped": "LEVEL_HOLD_WHEN_STOPPED",
    "ts": "LEVEL_TS",
    "tf_ts": "LEVEL_TF_TS",
    "sp_ramp_max": "LEVEL_SP_RAMP_MAX",
    "pv_entity": "sensor.plcassistant_lt_tank_in",
    "sp_entity": "sensor.plcassistant_sp_level",
    "sp_man_entity": "number.plcassistant_sp_level_man",
    "sp_auto_entity": "number.plcassistant_sp_level_req",
    "sp_rem_entity": "number.plcassistant_sp_level_rem",
    "mode_entity": "number.plcassistant_level_mode",
    "cv_entity": "sensor.plcassistant_sp_flow_auto",
    "cv_man_entity": "number.plcassistant_co_level_man",
    "kp_entity": "number.plcassistant_level_kp",
    "ki_entity": "number.plcassistant_level_ki",
    "kd_entity": "number.plcassistant_level_kd",
    "u0_entity": "number.plcassistant_level_u0",
    "beta_entity": "number.plcassistant_level_beta",
    "direct_acting_entity": "number.plcassistant_level_direct_acting",
    "cv_min_entity": "number.plcassistant_level_cv_min",
    "cv_max_entity": "number.plcassistant_level_cv_max",
    "hold_when_stopped_entity": "number.plcassistant_level_hold_when_stopped",
    "ts_entity": "number.plcassistant_level_ts",
    "tf_ts_entity": "number.plcassistant_level_tf_ts",
    "sp_ramp_max_entity": "number.plcassistant_level_sp_ramp_max",
}

_FLOW = {
    "loop_id": "flow",
    "pv": "FT_INLET",
    "sp": "SP_FLOW",
    "sp_man": "SP_FLOW_MAN",
    "sp_auto": "SP_FLOW_REQ",
    "sp_rem": "SP_FLOW_AUTO",
    "mode": "FLOW_MODE",
    "cv": "CMD_SPEED",
    "co_man": "CO_FLOW_MAN",
    "kp": "FLOW_KP",
    "ki": "FLOW_KI",
    "kd": "FLOW_KD",
    "u0": "FLOW_U0",
    "beta": "FLOW_BETA",
    "direct_acting": "FLOW_DIRECT_ACTING",
    "cv_min": "FLOW_CV_MIN",
    "cv_max": "FLOW_CV_MAX",
    "hold_when_stopped": "FLOW_HOLD_WHEN_STOPPED",
    "ts": "FLOW_TS",
    "tf_ts": "FLOW_TF_TS",
    "sp_ramp_max": "FLOW_SP_RAMP_MAX",
    "pv_entity": "sensor.plcassistant_ft_inlet_in",
    "sp_entity": "sensor.plcassistant_sp_flow",
    "sp_man_entity": "number.plcassistant_sp_flow_man",
    "sp_auto_entity": "number.plcassistant_sp_flow_req",
    "sp_rem_entity": "sensor.plcassistant_sp_flow_auto",
    "mode_entity": "number.plcassistant_flow_mode",
    "cv_entity": "sensor.plcassistant_cmd_speed",
    "cv_man_entity": "number.plcassistant_co_flow_man",
    "kp_entity": "number.plcassistant_flow_kp",
    "ki_entity": "number.plcassistant_flow_ki",
    "kd_entity": "number.plcassistant_flow_kd",
    "u0_entity": "number.plcassistant_flow_u0",
    "beta_entity": "number.plcassistant_flow_beta",
    "direct_acting_entity": "number.plcassistant_flow_direct_acting",
    "cv_min_entity": "number.plcassistant_flow_cv_min",
    "cv_max_entity": "number.plcassistant_flow_cv_max",
    "hold_when_stopped_entity": "number.plcassistant_flow_hold_when_stopped",
    "ts_entity": "number.plcassistant_flow_ts",
    "tf_ts_entity": "number.plcassistant_flow_tf_ts",
    "sp_ramp_max_entity": "number.plcassistant_flow_sp_ramp_max",
}

DEMO_PID_LOOPS: tuple[dict[str, str], ...] = (_LEVEL, _FLOW)

_PID_PARAM_KEYS = (
    "kp",
    "ki",
    "kd",
    "u0",
    "beta",
    "direct_acting",
    "cv_min",
    "cv_max",
    "hold_when_stopped",
    "ts",
    "tf_ts",
    "sp_ramp_max",
)

_MODE_NAMES = {0: "manual", 1: "automatic", 2: "remote"}
_MODE_ALIASES = {
    "man": "manual",
    "manual": "manual",
    "auto": "automatic",
    "automatic": "automatic",
    "rem": "remote",
    "remote": "remote",
    "cas": "remote",
    "cascade": "remote",
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
            return "automatic"
        return _MODE_NAMES.get(code, "automatic")
    key = str(raw or "").strip().lower()
    # Unknown aliases fall back to automatic — same as Soft-PLC skid_scan (SWD-369).
    return _MODE_ALIASES.get(key, "automatic")


def _write_target(mode: str, *, sp_auto_entity: str) -> str | None:
    """Which analog the operator may set: CO in MAN, SP in AUTO (if writable)."""
    if mode == "manual":
        return "co"
    if mode == "automatic" and not str(sp_auto_entity).startswith("sensor."):
        return "sp"
    return None


def _select_sp(mode: str, man: float, auto: float, rem: float) -> float:
    if mode == "manual":
        return man
    if mode == "remote":
        return rem
    return auto


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
        # Demo defaults until store hydrate: Level Automatic, Flow Remote.
        self._attr_native_value = "remote" if loop_id == "flow" else "automatic"
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
                spec["co_man"],
                *[spec[key] for key in _PID_PARAM_KEYS],
            }
        )

    def _empty_attrs(self) -> dict[str, Any]:
        spec = self._spec
        return {
            "loop_id": spec["loop_id"],
            "pv": None,
            "sp": None,
            "sp_target": None,
            "sp_man": None,
            "sp_auto": None,
            "sp_rem": None,
            "cv": None,
            "co_man": None,
            **{key: None for key in _PID_PARAM_KEYS},
            "pv_entity": spec["pv_entity"],
            "sp_entity": spec["sp_entity"],
            "sp_man_entity": spec["sp_man_entity"],
            "sp_auto_entity": spec["sp_auto_entity"],
            "sp_rem_entity": spec["sp_rem_entity"],
            "mode_entity": spec["mode_entity"],
            "cv_entity": spec["cv_entity"],
            "cv_man_entity": spec["cv_man_entity"],
            "kp_entity": spec["kp_entity"],
            "ki_entity": spec["ki_entity"],
            "kd_entity": spec["kd_entity"],
            "u0_entity": spec["u0_entity"],
            "beta_entity": spec["beta_entity"],
            "direct_acting_entity": spec["direct_acting_entity"],
            "cv_min_entity": spec["cv_min_entity"],
            "cv_max_entity": spec["cv_max_entity"],
            "hold_when_stopped_entity": spec["hold_when_stopped_entity"],
            "ts_entity": spec["ts_entity"],
            "tf_ts_entity": spec["tf_ts_entity"],
            "sp_ramp_max_entity": spec["sp_ramp_max_entity"],
            "write_target": None,
        }

    def _refresh_from_store(self) -> bool:
        store = self.hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
        spec = self._spec
        mode = _parse_mode(_cache_value(store, spec["mode"]))
        man = round_display(_cache_value(store, spec["sp_man"])) or 0.0
        auto = round_display(_cache_value(store, spec["sp_auto"])) or 0.0
        rem = round_display(_cache_value(store, spec["sp_rem"])) or 0.0
        # Mux is the operator/cascade request (target). When ramp rate is 0,
        # keep mux as ``sp`` so Set does not lag (SWD-222). When ramping,
        # ``sp`` is the Soft-PLC OUT (ramped) and ``sp_target`` stays the mux.
        sp_target = round_display(_select_sp(mode, man, auto, rem)) or 0.0
        ramp_max = round_display(_cache_value(store, spec["sp_ramp_max"])) or 0.0
        if ramp_max > 0:
            out = round_display(_cache_value(store, spec["sp"]))
            sp = out if out is not None else sp_target
        else:
            sp = sp_target
        attrs = self._empty_attrs()
        attrs.update(
            {
                "pv": round_display(_cache_value(store, spec["pv"])),
                "sp": sp,
                "sp_target": sp_target,
                "sp_man": man,
                "sp_auto": auto,
                "sp_rem": rem,
                "cv": round_display(_cache_value(store, spec["cv"])),
                "co_man": round_display(_cache_value(store, spec["co_man"])) or 0.0,
                "write_target": _write_target(
                    mode, sp_auto_entity=spec["sp_auto_entity"]
                ),
                **{
                    key: round_display(_cache_value(store, spec[key]))
                    for key in _PID_PARAM_KEYS
                },
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
]
