"""Persist Datablock catalog + Program access in HA config (SWD-184)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from plcassistant.io.datablock import (
    DatablockCatalog,
    binding_rows_from_table,
    default_program_datablock_access,
    default_tank_datablock_catalog,
    union_program_access_ids,
)


def store_path(config_root: Path) -> Path:
    return Path(config_root) / "plcassistant" / "datablocks.json"


def default_store_payload() -> dict[str, Any]:
    catalog = default_tank_datablock_catalog()
    return {
        "version": 1,
        **catalog.to_dict(),
        "program_access": default_program_datablock_access(),
    }


def load_store(config_root: Path) -> dict[str, Any]:
    path = store_path(config_root)
    if not path.is_file():
        payload = default_store_payload()
        save_store(config_root, payload)
        return payload
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("datablocks store must be a JSON object")
    # Ensure catalog validates (per-block BindingTable rules).
    DatablockCatalog.from_dict(data)
    data.setdefault("program_access", default_program_datablock_access())
    return data


def save_store(config_root: Path, payload: dict[str, Any]) -> None:
    DatablockCatalog.from_dict(payload)
    path = store_path(config_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    tmp.replace(path)


def catalog_from_store(payload: dict[str, Any]) -> DatablockCatalog:
    return DatablockCatalog.from_dict(payload)


def accessible_datablock_ids(payload: dict[str, Any]) -> list[str]:
    """Datablock ids the HA MQTT/image path should wire.

    Returns the ordered union of ``program_access`` values. An empty access map
    yields no ids (no tags wired).
    """
    access = payload.get("program_access") or {}
    if not isinstance(access, dict):
        raise ValueError("'program_access' must be a mapping")
    if access:
        return union_program_access_ids(access)
    return []


def binding_rows_from_store(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten accessible Datablock bindings for entity platform setup.

    Respects ``program_access`` (union of Datablock ids). Raises on BindingTable
    conflicts instead of silently dropping duplicate tags.
    """
    catalog = catalog_from_store(payload)
    ids = accessible_datablock_ids(payload)
    if not ids:
        return []
    table = catalog.binding_table_for(ids)
    return binding_rows_from_table(table)
