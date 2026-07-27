"""Config flow for PLCAssistant thin integration (SWD-126)."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_INSTANCE_ID,
    CONF_MQTT_BROKER,
    CONF_MQTT_PORT,
    DEFAULT_INSTANCE_ID,
    DEFAULT_MQTT_BROKER,
    DEFAULT_MQTT_PORT,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_INSTANCE_ID, default=DEFAULT_INSTANCE_ID): str,
        vol.Required(CONF_MQTT_BROKER, default=DEFAULT_MQTT_BROKER): str,
        vol.Required(CONF_MQTT_PORT, default=DEFAULT_MQTT_PORT): int,
        vol.Optional("mock_mode", default=True): bool,
    }
)


class PlcAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PLCAssistant."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        await self.async_set_unique_id(user_input[CONF_INSTANCE_ID])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title="PLCAssistant", data=user_input)
