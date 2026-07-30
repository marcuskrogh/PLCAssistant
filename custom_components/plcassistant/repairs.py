"""Repairs flow: restart Core after thin-integration sync (SWD-168)."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import data_entry_flow
from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .version_sync import ISSUE_RESTART_REQUIRED


class RestartRequiredRepairFlow(RepairsFlow):
    """Confirm and restart Home Assistant Core."""

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        placeholders = self._issue_placeholders()
        if user_input is not None:
            await self.hass.services.async_call("homeassistant", "restart")
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders=placeholders,
        )

    def _issue_placeholders(self) -> dict[str, str]:
        """Copy translation placeholders from the issue registry when present."""
        issue = ir.async_get(self.hass).async_get_issue(DOMAIN, self.issue_id)
        if issue is None or not issue.translation_placeholders:
            return {"loaded": "?", "disk": "?"}
        return {k: str(v) for k, v in issue.translation_placeholders.items()}


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create a repair flow for a PLCAssistant issue."""
    del hass, data  # Required by HA repairs protocol; unused here.
    if issue_id == ISSUE_RESTART_REQUIRED:
        return RestartRequiredRepairFlow()
    return ConfirmRepairFlow()
