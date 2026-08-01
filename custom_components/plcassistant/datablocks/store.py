"""Persist Datablock catalog + Program access in HA config (SWD-184)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from plcassistant.io.datablock import (
    DatablockCatalog,
    default_program_datablock_access,
    default_tank_datablock_catalog,
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
    # Ensure catalog validates.
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


def binding_rows_from_store(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten all Datablock bindings for entity platform setup."""
    catalog = catalog_from_store(payload)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for block in catalog.datablocks.values():
        for b in block.bindings:
            if b.tag in seen:
                continue
            seen.add(b.tag)
            rows.append(
                {
                    "tag": b.tag,
                    "entity": b.entity,
                    "direction": b.direction.value,
                    "scale": b.scale,
                    "offset": b.offset,
                }
            )
    return rows
