"""Data update coordinator: poll GetStatus and sync PutBindings."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .bootstrap import ensure_contract
from .const import (
    CONF_ADDON_URL,
    CONF_DEFAULT_ON_BRIDGE_FAULT,
    CONF_DEFAULT_UNAVAILABLE_POLICY,
    CONF_SCAN_PERIOD_MS,
    CONF_TOKEN,
    DEFAULT_ON_BRIDGE_FAULT,
    DEFAULT_SCAN_PERIOD_MS,
    DEFAULT_UNAVAILABLE_POLICY,
    DOMAIN,
)
from .control_plane import AddonUnavailableError, ControlPlaneClient
from .store import BindingStore

ensure_contract()

from plcassistant_contract import (  # noqa: E402
    InputPolicy,
    OutputFaultPolicy,
    RuntimeStatus,
    ScanOptions,
)

_LOGGER = logging.getLogger(__name__)


class PlcAssistantCoordinator(DataUpdateCoordinator[RuntimeStatus]):
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        store: BindingStore,
    ) -> None:
        self.entry = entry
        self.store = store
        self.client = ControlPlaneClient(
            base_url=entry.data[CONF_ADDON_URL],
            token=entry.data.get(CONF_TOKEN) or None,
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=5),
        )

    def _scan_options(self) -> ScanOptions:
        opts = self.entry.options
        period = int(opts.get(CONF_SCAN_PERIOD_MS, DEFAULT_SCAN_PERIOD_MS))
        unavailable = opts.get(CONF_DEFAULT_UNAVAILABLE_POLICY, DEFAULT_UNAVAILABLE_POLICY)
        bridge_fault = opts.get(CONF_DEFAULT_ON_BRIDGE_FAULT, DEFAULT_ON_BRIDGE_FAULT)
        return ScanOptions(
            scan_period_ms=period,
            default_unavailable_policy=InputPolicy(unavailable),
            default_on_bridge_fault=OutputFaultPolicy(bridge_fault),
        )

    def sync_to_addon(self) -> None:
        """Push bindings + scan options (runs in executor)."""
        self.client.put_bindings(self.store.bindings)
        self.client.put_scan_options(self._scan_options())
        self.client.reload()

    async def async_sync_to_addon_best_effort(self) -> None:
        """Persist-local SoT; PutBindings when addon reachable, else keep SoT."""
        try:
            await self.hass.async_add_executor_job(self.sync_to_addon)
        except AddonUnavailableError as exc:
            _LOGGER.warning(
                "Addon unavailable during PutBindings sync (%s); local bindings retained",
                exc,
            )

    async def _async_update_data(self) -> RuntimeStatus:
        period = float(
            self.entry.options.get(CONF_SCAN_PERIOD_MS, DEFAULT_SCAN_PERIOD_MS)
        )
        try:
            return await self.hass.async_add_executor_job(self.client.get_status)
        except AddonUnavailableError as exc:
            _LOGGER.debug("Addon status unavailable: %s", exc)
            return RuntimeStatus.disconnected(scan_period_ms=period)
