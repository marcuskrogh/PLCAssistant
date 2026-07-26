"""PLCAssistant Home Assistant custom integration (config + bindings + diagnostics)."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    ATTR_ENTRY_ID,
    DOMAIN,
    PLATFORMS,
    SERVICE_RELOAD,
    SERVICE_START,
    SERVICE_STOP,
)
from .control_plane import AddonUnavailableError
from .coordinator import PlcAssistantCoordinator
from .store import BindingStore

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTRY_ID): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    store = BindingStore(hass, entry.entry_id)
    await store.async_load()
    coordinator = PlcAssistantCoordinator(hass, entry, store)
    # On setup and after options reload: push SoT bindings (AC3 / PLAN).
    await coordinator.async_sync_to_addon_best_effort()
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "store": store,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _iter_entry_data(hass: HomeAssistant, call: ServiceCall) -> list[dict[str, Any]]:
    domain_data = hass.data.get(DOMAIN, {})
    entry_id = call.data.get(ATTR_ENTRY_ID)
    if entry_id:
        data = domain_data.get(entry_id)
        if data is None:
            raise HomeAssistantError(f"Unknown config entry_id: {entry_id}")
        return [data]
    return list(domain_data.values())


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_RELOAD):
        return

    async def _reload(call: ServiceCall) -> None:
        for data in _iter_entry_data(hass, call):
            coordinator: PlcAssistantCoordinator = data["coordinator"]
            try:
                await hass.async_add_executor_job(coordinator.sync_to_addon)
            except AddonUnavailableError as exc:
                raise HomeAssistantError(f"Addon unavailable: {exc}") from exc
            await coordinator.async_request_refresh()

    async def _start(call: ServiceCall) -> None:
        for data in _iter_entry_data(hass, call):
            coordinator: PlcAssistantCoordinator = data["coordinator"]
            try:
                await hass.async_add_executor_job(coordinator.client.start)
            except AddonUnavailableError as exc:
                raise HomeAssistantError(f"Addon unavailable: {exc}") from exc
            await coordinator.async_request_refresh()

    async def _stop(call: ServiceCall) -> None:
        for data in _iter_entry_data(hass, call):
            coordinator: PlcAssistantCoordinator = data["coordinator"]
            try:
                await hass.async_add_executor_job(coordinator.client.stop)
            except AddonUnavailableError as exc:
                raise HomeAssistantError(f"Addon unavailable: {exc}") from exc
            await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_RELOAD, _reload, schema=_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_START, _start, schema=_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP, _stop, schema=_SERVICE_SCHEMA)
