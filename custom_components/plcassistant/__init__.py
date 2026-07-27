"""PLCAssistant thin Home Assistant integration (SWD-126).

Owns tag declarations / entity↔tag bindings, mock entities, and operator
services. Talks to the Soft-PLC App over MQTT (Mosquitto required).

This module is written to load under Home Assistant. Unit tests in this repo
**do not import** it (no ``homeassistant`` dependency in CI); they assert
layout and config keys via filesystem checks.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_INSTANCE_ID,
    DOMAIN,
    SERVICE_RESET,
    SERVICE_START,
    SERVICE_STOP,
)
from .mqtt_topics import cmd_topic

PLATFORMS: list[str] = []


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up from YAML is unused; config entries only."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PLCAssistant from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "instance_id": entry.data.get(CONF_INSTANCE_ID, "default"),
        "bindings": entry.data.get("bindings", []),
        "mock_mode": entry.data.get("mock_mode", True),
    }

    async def _publish_cmd(name: str, call: ServiceCall) -> None:
        instance_id = hass.data[DOMAIN][entry.entry_id]["instance_id"]
        topic = cmd_topic(instance_id, name)
        # Prefer HA MQTT integration publish helper when available.
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

    hass.services.async_register(DOMAIN, SERVICE_START, handle_start)
    hass.services.async_register(DOMAIN, SERVICE_STOP, handle_stop)
    hass.services.async_register(DOMAIN, SERVICE_RESET, handle_reset)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True
