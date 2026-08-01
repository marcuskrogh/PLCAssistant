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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    instance_id = data[CONF_INSTANCE_ID]
    async_add_entities(
        [
            PlcAssistantCmdButton(
                entry.entry_id, instance_id, SERVICE_START, "Start", "plcassistant_start"
            ),
            PlcAssistantCmdButton(
                entry.entry_id, instance_id, SERVICE_STOP, "Stop", "plcassistant_stop"
            ),
            PlcAssistantCmdButton(
                entry.entry_id, instance_id, SERVICE_RESET, "Reset", "plcassistant_reset"
            ),
        ]
    )


class PlcAssistantCmdButton(ButtonEntity):
    """Press routes through ``plcassistant.start|stop|reset`` (MQTT cmd pulse)."""

    _attr_should_poll = False

    def __init__(
        self,
        entry_id: str,
        instance_id: str,
        cmd: str,
        label: str,
        object_id: str,
    ) -> None:
        self._entry_id = entry_id
        self._instance_id = instance_id
        self._cmd = cmd
        self._attr_name = f"PLCAssistant {label}"
        self._attr_unique_id = f"{entry_id}_cmd_{cmd}"
        self._attr_suggested_object_id = object_id
        self.entity_id = f"button.{object_id}"
        icons = {
            SERVICE_START: "mdi:play",
            SERVICE_STOP: "mdi:stop",
            SERVICE_RESET: "mdi:restart",
        }
        self._attr_icon = icons.get(cmd, "mdi:gesture-tap-button")

    async def async_press(self) -> None:
        # Blocking so Start/Stop wait for MQTT qos1 + file cmd (SWD-222).
        await self.hass.services.async_call(
            DOMAIN,
            self._cmd,
            {CONF_INSTANCE_ID: self._instance_id},
            blocking=True,
        )
