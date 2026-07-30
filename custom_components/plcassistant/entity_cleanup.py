"""Entity-registry cleanup for contracted plant Number entity IDs (SWD-170).

After unique_id / platform churn, Lovelace can keep pointing at orphaned
``number.plcassistant_*_in`` rows whose live replacements took ``_2`` suffixes.
Remove unavailable contracted IDs so nudge Numbers and plant sensors can bind.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Contracted plant Number entity_ids (bindings / Lovelace / README).
_PLANT_NUMBER_ENTITY_IDS: tuple[str, ...] = (
    "number.plcassistant_lt_tank_in",
    "number.plcassistant_lt_res_in",
    "number.plcassistant_ft_inlet_in",
)

# Tags corresponding to the entity_ids above (order matches).
_PLANT_NUMBER_TAGS: tuple[str, ...] = ("LT_TANK", "LT_RES", "FT_INLET")


def expected_plant_number_unique_id(instance_id: str, tag: str) -> str:
    """Stable unique_id for plant nudge Numbers (instance + tag)."""
    return f"plcassistant_{instance_id}_{tag}_number"


def expected_plant_sensor_unique_id(instance_id: str, tag: str) -> str:
    """Stable unique_id for plant IN display Sensors."""
    return f"plcassistant_{instance_id}_{tag}_plant_in"


def should_purge_plant_number(
    *,
    state_unavailable: bool,
    unique_id: str,
    expected_unique_id: str,
) -> bool:
    """True when a contracted plant Number registry row should be removed.

    Only purge when the contracted entity_id is unavailable (missing state or
    ``unavailable``). Never delete a live available entity solely because the
    unique_id differs — that can yank an active nudge mid-session.
    """
    del unique_id, expected_unique_id  # reserved for logging/callers; not a delete gate
    return bool(state_unavailable)


async def async_purge_orphaned_plant_numbers(
    hass: HomeAssistant, instance_id: str
) -> list[str]:
    """Remove unavailable plant Number registry entries that block contracted IDs.

    Returns the list of removed entity_ids (empty when nothing to do / APIs missing).
    """
    try:
        from homeassistant.helpers import entity_registry as er
    except ImportError:
        return []

    registry = er.async_get(hass)
    removed: list[str] = []
    for entity_id, tag in zip(_PLANT_NUMBER_ENTITY_IDS, _PLANT_NUMBER_TAGS, strict=True):
        entry = registry.async_get(entity_id)
        if entry is None:
            continue
        expected = expected_plant_number_unique_id(instance_id, tag)
        state = hass.states.get(entity_id)
        state_unavailable = state is None or str(state.state) == "unavailable"
        if not should_purge_plant_number(
            state_unavailable=state_unavailable,
            unique_id=str(entry.unique_id),
            expected_unique_id=expected,
        ):
            continue
        try:
            registry.async_remove(entity_id)
            removed.append(entity_id)
            _LOGGER.info(
                "PLCAssistant: removed orphaned plant Number %s "
                "(unique_id=%s, expected=%s, state=%s)",
                entity_id,
                entry.unique_id,
                expected,
                None if state is None else state.state,
            )
        except Exception:  # noqa: BLE001
            _LOGGER.debug(
                "PLCAssistant: failed to remove orphaned %s", entity_id, exc_info=True
            )
    return removed


__all__ = [
    "async_purge_orphaned_plant_numbers",
    "expected_plant_number_unique_id",
    "expected_plant_sensor_unique_id",
    "should_purge_plant_number",
]
