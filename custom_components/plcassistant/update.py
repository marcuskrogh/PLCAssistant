"""Update entity: Restart required after thin-integration sync (SWD-168).

When App Start copies a newer integration onto disk, this entity appears on
Settings → System → Updates with a HACS-style restart alert until Core reloads
the package.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.update import UpdateEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.issue_registry import (
    IssueSeverity,
    async_create_issue,
    async_delete_issue,
)

from .const import DOMAIN
from .version_sync import (
    ISSUE_RESTART_REQUIRED,
    LOADED_VERSION,
    RESTART_REQUIRED_SUMMARY,
    disk_version,
)

_LOGGER = logging.getLogger(__name__)

# Re-check often enough that App sync → UI gap is short without busy-polling.
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the PLCAssistant restart-required update entity."""
    entity = PlcAssistantRestartUpdateEntity(entry)
    async_add_entities([entity], update_before_add=True)


@callback
def async_sync_restart_required_issue(
    hass: HomeAssistant,
    *,
    needs_restart: bool,
    loaded: str,
    on_disk: str,
) -> None:
    """Create or clear the fixable restart_required repair issue."""
    if needs_restart:
        async_create_issue(
            hass,
            DOMAIN,
            ISSUE_RESTART_REQUIRED,
            is_fixable=True,
            severity=IssueSeverity.WARNING,
            translation_key="restart_required",
            translation_placeholders={
                "loaded": loaded,
                "disk": on_disk,
            },
            learn_more_url=(
                "https://github.com/marcuskrogh/PLCAssistant/blob/main/"
                "docs/packaging/04-updates.md"
            ),
        )
    else:
        async_delete_issue(hass, DOMAIN, ISSUE_RESTART_REQUIRED)


class PlcAssistantRestartUpdateEntity(UpdateEntity):
    """Shows Restart required when synced files are newer than loaded code."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_title = "PLCAssistant"
    _attr_icon = "mdi:memory"
    _attr_should_poll = True
    _attr_supported_features = 0
    _attr_auto_update = False
    _attr_suggested_object_id = "plcassistant"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_restart_required"
        self._attr_installed_version = LOADED_VERSION
        self._attr_latest_version = LOADED_VERSION
        self._attr_release_summary = None
        self._last_disk_ok = True

    async def async_update(self) -> None:
        """Refresh disk version and sync Updates + Repairs UX."""
        loaded = LOADED_VERSION
        try:
            on_disk = await self.hass.async_add_executor_job(disk_version)
        except (OSError, ValueError, TypeError, AttributeError) as err:
            _LOGGER.debug("PLCAssistant: could not read disk version: %s", err)
            # Do not clear a pending restart alert on a transient/corrupt read.
            self._last_disk_ok = False
            return

        self._last_disk_ok = True
        needs = on_disk != loaded
        self._attr_installed_version = loaded
        self._attr_latest_version = on_disk if needs else loaded
        self._attr_release_summary = RESTART_REQUIRED_SUMMARY if needs else None

        async_sync_restart_required_issue(
            self.hass,
            needs_restart=needs,
            loaded=loaded,
            on_disk=on_disk,
        )

    def version_is_newer(self, latest_version: str, installed_version: str) -> bool:
        """Any disk≠loaded mismatch means a restart is pending."""
        return latest_version != installed_version
