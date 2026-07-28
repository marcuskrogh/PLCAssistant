"""PLCAssistant thin Home Assistant integration (SWD-126).

Owns tag declarations / entity↔tag bindings, mock entities, and operator
services. Talks to the Soft-PLC App over MQTT (Mosquitto required).

Unit tests in this repo do not import this module (no ``homeassistant`` in CI).
Testable MQTT mapping lives in ``plcassistant.io.mqtt_entity_bridge``.
"""

from __future__ import annotations

from homeassistant.components.mqtt import async_subscribe
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_BINDINGS,
    CONF_INSTANCE_ID,
    CONF_MOCK_MODE,
    DEFAULT_INSTANCE_ID,
    DOMAIN,
    SERVICE_RESET,
    SERVICE_START,
    SERVICE_STOP,
)
from .mqtt_topics import cmd_topic, tag_in_topic, tag_out_topic

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.BUTTON]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


def _default_bindings() -> list[dict]:
    """Default mock bindings — keep in sync with ``default_wedge_binding_config``."""
    return [
        {
            "tag": "LT_TANK",
            "entity": "number.plcassistant_lt_tank_in",
            "direction": "IN",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "LT_RES",
            "entity": "number.plcassistant_lt_res_in",
            "direction": "IN",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "FT_INLET",
            "entity": "number.plcassistant_ft_inlet_in",
            "direction": "IN",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "SP_LEVEL_REQ",
            "entity": "number.plcassistant_sp_level_req_in",
            "direction": "IN",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "CMD_SPEED",
            "entity": "number.plcassistant_cmd_speed_out",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "SP_LEVEL",
            "entity": "number.plcassistant_sp_level_out",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "SP_FLOW",
            "entity": "number.plcassistant_sp_flow_out",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
    ]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    instance_id = entry.data.get(CONF_INSTANCE_ID, DEFAULT_INSTANCE_ID)
    bindings = entry.data.get(CONF_BINDINGS) or _default_bindings()
    mock_mode = entry.data.get(CONF_MOCK_MODE, True)

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_INSTANCE_ID: instance_id,
        CONF_BINDINGS: bindings,
        CONF_MOCK_MODE: mock_mode,
        "out_values": {},
        "unsubs": [],
    }

    async def _publish_cmd(name: str, call: ServiceCall) -> None:
        # Prefer explicit instance_id in the service call; else first entry.
        target = call.data.get(CONF_INSTANCE_ID)
        data = None
        if target:
            for entry_data in hass.data[DOMAIN].values():
                if isinstance(entry_data, dict) and entry_data.get(CONF_INSTANCE_ID) == target:
                    data = entry_data
                    break
        if data is None:
            data = hass.data[DOMAIN].get(entry.entry_id)
        if data is None:
            return
        topic = cmd_topic(data[CONF_INSTANCE_ID], name)
        await hass.services.async_call(
            "mqtt",
            "publish",
            {
                "topic": topic,
                "payload": call.data.get("payload", "1"),
                "qos": 1,
                "retain": False,
            },
            blocking=False,
        )

    async def handle_start(call: ServiceCall) -> None:
        await _publish_cmd(SERVICE_START, call)

    async def handle_stop(call: ServiceCall) -> None:
        await _publish_cmd(SERVICE_STOP, call)

    async def handle_reset(call: ServiceCall) -> None:
        await _publish_cmd(SERVICE_RESET, call)

    if not hass.services.has_service(DOMAIN, SERVICE_START):
        hass.services.async_register(DOMAIN, SERVICE_START, handle_start)
        hass.services.async_register(DOMAIN, SERVICE_STOP, handle_stop)
        hass.services.async_register(DOMAIN, SERVICE_RESET, handle_reset)

    for binding in bindings:
        direction = str(binding.get("direction", "")).upper()
        if direction not in ("OUT", "INOUT"):
            continue
        tag = binding["tag"]
        topic = tag_out_topic(instance_id, tag)

        def _make_out_handler(tag_name: str, entry_id: str):
            async def _on_out(msg) -> None:
                try:
                    payload = msg.payload
                    if isinstance(payload, bytes):
                        text = payload.decode("utf-8")
                    else:
                        text = str(payload)
                except UnicodeDecodeError:
                    return
                store = hass.data[DOMAIN].get(entry_id)
                if store is None:
                    return
                store["out_values"][tag_name] = text
                hass.bus.async_fire(
                    f"{DOMAIN}_tag_out",
                    {"tag": tag_name, "payload": text, "entry_id": entry_id},
                )

            return _on_out

        unsub = await async_subscribe(
            hass, topic, _make_out_handler(tag, entry.entry_id), qos=1
        )
        hass.data[DOMAIN][entry.entry_id]["unsubs"].append(unsub)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id) or {}
    for unsub in data.get("unsubs") or []:
        unsub()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


__all__ = [
    "PLATFORMS",
    "async_setup",
    "async_setup_entry",
    "async_unload_entry",
    "tag_in_topic",
    "tag_out_topic",
    "cmd_topic",
]
