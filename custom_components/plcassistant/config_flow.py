"""Config flow for PLCAssistant thin integration (SWD-126 / SWD-143)."""

from __future__ import annotations

import json
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DYNAMICS_PARAMS,
    CONF_DYNAMICS_PRESET,
    CONF_INSTANCE_ID,
    CONF_MOCK_MODE,
    CONF_MQTT_BROKER,
    CONF_MQTT_PORT,
    DEFAULT_DYNAMICS_PRESET,
    DEFAULT_INSTANCE_ID,
    DEFAULT_MQTT_BROKER,
    DEFAULT_MQTT_PORT,
    DOMAIN,
)
from .dynamics.options import parse_dynamics_params, resolve_dynamics_options, validate_preset
from .dynamics.registry import list_presets

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_INSTANCE_ID, default=DEFAULT_INSTANCE_ID): str,
        vol.Required(CONF_MQTT_BROKER, default=DEFAULT_MQTT_BROKER): str,
        vol.Required(CONF_MQTT_PORT, default=DEFAULT_MQTT_PORT): int,
        vol.Optional(CONF_MOCK_MODE, default=True): bool,
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

        # Broker fields document required Mosquitto alignment; transport uses HA MQTT.
        return self.async_create_entry(title="PLCAssistant", data=user_input)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return PlcAssistantOptionsFlow(config_entry)


class PlcAssistantOptionsFlow(config_entries.OptionsFlow):
    """Configure mock dynamics preset + numeric param overrides (SWD-143)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        current_preset, current_params = resolve_dynamics_options(
            self._config_entry.options
        )
        presets = list(list_presets()) or [DEFAULT_DYNAMICS_PRESET]
        if current_preset not in presets:
            presets = sorted({*presets, current_preset})

        if user_input is not None:
            try:
                preset = validate_preset(user_input.get(CONF_DYNAMICS_PRESET))
                params = parse_dynamics_params(user_input.get(CONF_DYNAMICS_PARAMS))
                # Ensure the selected preset can load with overrides.
                from .dynamics.registry import get_preset

                get_preset(preset, params=params)
                return self.async_create_entry(
                    title="",
                    data={
                        **dict(self._config_entry.options),
                        CONF_DYNAMICS_PRESET: preset,
                        CONF_DYNAMICS_PARAMS: params,
                    },
                )
            except (KeyError, ValueError, TypeError) as exc:
                _LOGGER.warning("Invalid dynamics options: %s", exc)
                errors["base"] = "invalid_dynamics"

        params_default = (
            json.dumps(current_params, sort_keys=True) if current_params else "{}"
        )
        schema = vol.Schema(
            {
                vol.Required(CONF_DYNAMICS_PRESET, default=current_preset): vol.In(
                    presets
                ),
                vol.Optional(CONF_DYNAMICS_PARAMS, default=params_default): str,
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )
