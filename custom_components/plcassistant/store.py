"""Persisted binding registry (source of truth)."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .bootstrap import ensure_contract
from .const import STORAGE_KEY, STORAGE_VERSION

ensure_contract()

from plcassistant_contract import Binding, ValidationError, validate_bindings  # noqa: E402

_LOGGER = logging.getLogger(__name__)


class BindingStore:
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry_id}")
        self._bindings: list[Binding] = []

    @property
    def bindings(self) -> list[Binding]:
        return list(self._bindings)

    def as_dicts(self) -> list[dict[str, Any]]:
        return [b.to_dict() for b in self._bindings]

    async def async_load(self) -> None:
        data = await self._store.async_load()
        if not data:
            self._bindings = []
            return
        items = data.get("bindings") or []
        bindings = [Binding.from_dict(item) for item in items]
        try:
            validate_bindings(bindings)
        except ValidationError as exc:
            _LOGGER.error("Stored bindings failed validation (%s); keeping empty set", exc)
            self._bindings = []
            return
        self._bindings = bindings

    async def async_save(self) -> None:
        await self._store.async_save({"bindings": self.as_dicts()})

    def replace_from_dicts(self, payloads: list[dict[str, Any]]) -> None:
        bindings = [Binding.from_dict(item) for item in payloads]
        validate_bindings(bindings)
        self._bindings = bindings

    def set_bindings(self, bindings: list[Binding]) -> None:
        validate_bindings(bindings)
        self._bindings = list(bindings)
