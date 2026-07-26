"""Data update coordinator: poll GetStatus and sync PutBindings."""

from __future__ import annotations

from datetime import timedelta
import logging
from pathlib import Path
import sys

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_ADDON_URL, CONF_SCAN_PERIOD_MS, CONF_TOKEN, DEFAULT_SCAN_PERIOD_MS, DOMAIN
from .store import BindingStore

_REPO_CONTRACT = Path(__file__).resolve().parents[2] / "packages" / "plcassistant_contract"
if _REPO_CONTRACT.is_dir():
    path = str(_REPO_CONTRACT)
    if path not in sys.path:
        sys.path.insert(0, path)

from plcassistant_contract import RuntimeStatus, ScanOptions
from plcassistant_contract.client import AddonUnavailableError, ControlPlaneClient

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

    def sync_to_addon(self) -> None:
        """Push bindings + scan options (runs in executor)."""
        period = int(self.entry.options.get(CONF_SCAN_PERIOD_MS, DEFAULT_SCAN_PERIOD_MS))
        self.client.put_bindings(self.store.bindings)
        self.client.put_scan_options(ScanOptions(scan_period_ms=period))
        self.client.reload()

    async def _async_update_data(self) -> RuntimeStatus:
        period = float(self.entry.options.get(CONF_SCAN_PERIOD_MS, DEFAULT_SCAN_PERIOD_MS))
        try:
            return await self.hass.async_add_executor_job(self.client.get_status)
        except AddonUnavailableError as exc:
            _LOGGER.debug("Addon status unavailable: %s", exc)
            return RuntimeStatus.disconnected(scan_period_ms=period)
