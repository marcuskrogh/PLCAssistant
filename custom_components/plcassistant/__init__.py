"""PLCAssistant thin Home Assistant integration (SWD-126).

Owns tag declarations / entity↔tag bindings, mock entities, and operator
services. Talks to the Soft-PLC App over MQTT (Mosquitto required).

Unit tests in this repo do not import this module (no ``homeassistant`` in CI).
Testable MQTT mapping lives in ``plcassistant.io.mqtt_entity_bridge``;
filesystem tests assert this layout and topic usage.
"""

from __future__ import annotations

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

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up from YAML is unused; config entries only."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PLCAssistant from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    instance_id = entry.data.get(CONF_INSTANCE_ID, DEFAULT_INSTANCE_ID)
    bindings = entry.data.get(CONF_BINDINGS) or _default_bindings()
    mock_mode = entry.data.get(CONF_MOCK_MODE, True)

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_INSTANCE_ID: instance_id,
        CONF_BINDINGS: bindings,
        CONF_MOCK_MODE: mock_mode,
        "out_values": {},
    }

    async def _publish_cmd(name: str, call: ServiceCall) -> None:
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

    # Register once per domain (idempotent overwrite of handlers for this entry).
    if not hass.services.has_service(DOMAIN, SERVICE_START):
        hass.services.async_register(DOMAIN, SERVICE_START, handle_start)
        hass.services.async_register(DOMAIN, SERVICE_STOP, handle_stop)
        hass.services.async_register(DOMAIN, SERVICE_RESET, handle_reset)

    # Subscribe to Soft-PLC OUT topics for each OUT binding.
    for binding in bindings:
        direction = str(binding.get("direction", "")).upper()
        if direction not in ("OUT", "INOUT"):
            continue
        tag = binding["tag"]
        topic = tag_out_topic(instance_id, tag)

        def _make_out_handler(tag_name: str):
            async def _on_out(msg) -> None:
                payload = msg.payload
                if isinstance(payload, bytes):
                    text = payload.decode("utf-8")
                else:
                    text = str(payload)
                hass.data[DOMAIN][entry.entry_id]["out_values"][tag_name] = text
                hass.bus.async_fire(
                    f"{DOMAIN}_tag_out",
                    {"tag": tag_name, "payload": text, "entry_id": entry.entry_id},
                )

            return _on_out

        await hass.components.mqtt.async_subscribe(topic, _make_out_handler(tag), qos=1)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


def _default_bindings() -> list[dict]:
    """Default mock wedge bindings when config flow leaves bindings empty."""
    return [
        {
            "tag": "LT_TANK",
            "entity": "sensor.plcassistant_lt_tank",
            "direction": "IN",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "CMD_SPEED",
            "entity": "number.plcassistant_cmd_speed",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
    ]


# Re-export topic helpers so layout tests can grep this module for tag paths.
__all__ = [
    "PLATFORMS",
    "async_setup",
    "async_setup_entry",
    "async_unload_entry",
    "tag_in_topic",
    "tag_out_topic",
    "cmd_topic",
]
