"""Persisted binding registry (source of truth)."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION

# Path bootstrap for contract package
from pathlib import Path
import sys

_REPO_CONTRACT = Path(__file__).resolve().parents[2] / "packages" / "plcassistant_contract"
if _REPO_CONTRACT.is_dir():
    path = str(_REPO_CONTRACT)
    if path not in sys.path:
        sys.path.insert(0, path)

from plcassistant_contract import Binding, ValidationError, validate_bindings


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
        self._bindings = [Binding.from_dict(item) for item in items]

    async def async_save(self) -> None:
        await self._store.async_save({"bindings": self.as_dicts()})

    def replace_from_dicts(self, payloads: list[dict[str, Any]]) -> None:
        bindings = [Binding.from_dict(item) for item in payloads]
        validate_bindings(bindings)
        self._bindings = bindings

    def set_bindings(self, bindings: list[Binding]) -> None:
        validate_bindings(bindings)
        self._bindings = list(bindings)
