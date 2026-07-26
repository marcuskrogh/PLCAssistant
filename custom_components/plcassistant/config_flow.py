"""Config flow for PLCAssistant."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_ADDON_URL,
    CONF_SCAN_PERIOD_MS,
    CONF_TOKEN,
    DEFAULT_SCAN_PERIOD_MS,
    DOMAIN,
)


class PlcAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PLCAssistant."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ADDON_URL].rstrip("/"))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="PLCAssistant",
                data={
                    CONF_ADDON_URL: user_input[CONF_ADDON_URL].rstrip("/"),
                    CONF_TOKEN: user_input.get(CONF_TOKEN) or "",
                },
                options={
                    CONF_SCAN_PERIOD_MS: user_input.get(
                        CONF_SCAN_PERIOD_MS, DEFAULT_SCAN_PERIOD_MS
                    ),
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_ADDON_URL, default="http://localhost:8080"): str,
                vol.Optional(CONF_TOKEN, default=""): str,
                vol.Optional(CONF_SCAN_PERIOD_MS, default=DEFAULT_SCAN_PERIOD_MS): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=10_000)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return PlcAssistantOptionsFlow(config_entry)


class PlcAssistantOptionsFlow(config_entries.OptionsFlow):
    """Options: scan period + binding JSON editor (MVP UI)."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        from .store import BindingStore
        import json

        store = BindingStore(self.hass, self._entry.entry_id)
        await store.async_load()
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                raw = user_input.get("bindings_json") or "[]"
                payloads = json.loads(raw)
                if not isinstance(payloads, list):
                    raise ValueError("bindings_json must be a JSON array")
                store.replace_from_dicts(payloads)
                await store.async_save()
            except Exception:  # noqa: BLE001 — surface as form error
                errors["bindings_json"] = "invalid_bindings"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_SCAN_PERIOD_MS: user_input[CONF_SCAN_PERIOD_MS],
                    },
                )

        current = self._entry.options.get(CONF_SCAN_PERIOD_MS, DEFAULT_SCAN_PERIOD_MS)
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_PERIOD_MS, default=current): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=10_000)
                ),
                vol.Optional(
                    "bindings_json",
                    default=json.dumps(store.as_dicts(), indent=2),
                ): cv.string,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
