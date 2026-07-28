"""Operator command buttons — Start / Stop / Reset over MQTT."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_INSTANCE_ID,
    DOMAIN,
    SERVICE_RESET,
    SERVICE_START,
    SERVICE_STOP,
)
from .mqtt_topics import cmd_topic


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    instance_id = data[CONF_INSTANCE_ID]
    async_add_entities(
        [
            PlcAssistantCmdButton(entry.entry_id, instance_id, SERVICE_START, "Start"),
            PlcAssistantCmdButton(entry.entry_id, instance_id, SERVICE_STOP, "Stop"),
            PlcAssistantCmdButton(entry.entry_id, instance_id, SERVICE_RESET, "Reset"),
        ]
    )


class PlcAssistantCmdButton(ButtonEntity):
    """Press publishes a Soft-PLC command topic pulse."""

    _attr_should_poll = False

    def __init__(
        self,
        entry_id: str,
        instance_id: str,
        cmd: str,
        label: str,
    ) -> None:
        self._entry_id = entry_id
        self._instance_id = instance_id
        self._cmd = cmd
        self._attr_name = f"PLCAssistant {label}"
        self._attr_unique_id = f"{entry_id}_cmd_{cmd}"

    async def async_press(self) -> None:
        await self.hass.services.async_call(
            "mqtt",
            "publish",
            {
                "topic": cmd_topic(self._instance_id, self._cmd),
                "payload": "1",
                "qos": 1,
                "retain": False,
            },
            blocking=False,
        )
