"""Named Datablocks grouping tags and HA entity bindings (SWD-184).

Datablocks are industrial I/O packages owned by the thin HA integration.
Soft-PLC Programs declare which Datablock id(s) they can access; Soft-PLC
only sees the union of those tags.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from plcassistant.io.binding import Binding, BindingTable, TagDecl


@dataclass
class Datablock:
    """One named Datablock: tag declarations + directional bindings."""

    datablock_id: str
    description: str = ""
    tags: dict[str, TagDecl] = field(default_factory=dict)
    bindings: list[Binding] = field(default_factory=list)

    def binding_table(self) -> BindingTable:
        """Return a BindingTable for this Datablock alone."""
        return BindingTable(tags=self.tags, bindings=list(self.bindings))

    def tag_names(self) -> frozenset[str]:
        return frozenset(self.tags)


class DatablockCatalog:
    """Collection of Datablocks with merge helpers for Soft-PLC access."""

    def __init__(self, datablocks: Mapping[str, Datablock] | None = None) -> None:
        self._blocks: dict[str, Datablock] = dict(datablocks or {})

    @property
    def datablocks(self) -> Mapping[str, Datablock]:
        return self._blocks

    def get(self, datablock_id: str) -> Datablock | None:
        return self._blocks.get(datablock_id)

    def upsert(self, block: Datablock) -> None:
        if not block.datablock_id:
            raise ValueError("datablock_id required")
        block.binding_table()
        self._blocks[block.datablock_id] = block

    def delete(self, datablock_id: str) -> None:
        if datablock_id not in self._blocks:
            raise KeyError(f"Datablock {datablock_id!r} not found")
        del self._blocks[datablock_id]

    def tag_names_for(self, datablock_ids: list[str] | tuple[str, ...] | None) -> frozenset[str]:
        names: set[str] = set()
        for db_id in datablock_ids or ():
            block = self._blocks.get(str(db_id))
            if block is None:
                raise KeyError(f"Datablock {db_id!r} not found")
            names.update(block.tag_names())
        return frozenset(names)

    def binding_table_for(
        self,
        datablock_ids: list[str] | tuple[str, ...] | None,
    ) -> BindingTable:
        tags: dict[str, TagDecl] = {}
        bindings: list[Binding] = []
        for db_id in datablock_ids or ():
            block = self._blocks.get(str(db_id))
            if block is None:
                raise KeyError(f"Datablock {db_id!r} not found")
            for name, decl in block.tags.items():
                prior = tags.get(name)
                if prior is not None and (
                    prior.default != decl.default or prior.unit != decl.unit
                ):
                    raise ValueError(
                        f"conflicting tag declaration for {name!r} across Datablocks"
                    )
                tags[name] = decl
            bindings.extend(block.bindings)
        return BindingTable(tags=tags, bindings=bindings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "datablocks": {
                db_id: datablock_to_dict(block) for db_id, block in self._blocks.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DatablockCatalog:
        raw = data.get("datablocks") or {}
        if not isinstance(raw, Mapping):
            raise ValueError("'datablocks' must be a mapping")
        blocks: dict[str, Datablock] = {}
        for db_id, payload in raw.items():
            if not isinstance(payload, Mapping):
                raise ValueError(f"datablock {db_id!r} must be a mapping")
            block = datablock_from_dict(payload, datablock_id=str(db_id))
            # Validate BindingTable rules per block on load.
            block.binding_table()
            blocks[block.datablock_id] = block
        return cls(blocks)


def datablock_to_dict(block: Datablock) -> dict[str, Any]:
    return {
        "id": block.datablock_id,
        "description": block.description,
        "tags": {
            name: {"default": decl.default, "unit": decl.unit}
            for name, decl in block.tags.items()
        },
        "bindings": [
            {
                "tag": b.tag,
                "entity": b.entity,
                "direction": b.direction.value,
                "scale": b.scale,
                "offset": b.offset,
                "entity_unit": b.entity_unit,
                "treat_uncertain_as_good": b.treat_uncertain_as_good,
            }
            for b in block.bindings
        ],
    }


def datablock_from_dict(
    data: Mapping[str, Any],
    *,
    datablock_id: str | None = None,
) -> Datablock:
    db_id = str(datablock_id or data.get("id") or "").strip()
    if not db_id:
        raise ValueError("datablock id required")
    table = BindingTable.from_config(
        {
            "tags": data.get("tags") or {},
            "bindings": data.get("bindings") or [],
        }
    )
    return Datablock(
        datablock_id=db_id,
        description=str(data.get("description") or ""),
        tags=dict(table.tags),
        bindings=list(table.bindings),
    )


def program_accessible_tags(
    catalog: DatablockCatalog,
    datablock_ids: list[str] | tuple[str, ...] | None,
) -> frozenset[str]:
    """Tags a Soft-PLC Program may see given its Datablock access list."""
    return catalog.tag_names_for(list(datablock_ids or ()))


def union_program_access_ids(
    program_access: Mapping[str, Any] | None,
) -> list[str]:
    """Ordered unique Datablock ids from a program_access map."""
    ordered: list[str] = []
    seen: set[str] = set()
    for dbs in (program_access or {}).values():
        if not isinstance(dbs, list):
            continue
        for db_id in dbs:
            key = str(db_id)
            if key and key not in seen:
                seen.add(key)
                ordered.append(key)
    return ordered


def binding_rows_from_table(table: BindingTable) -> list[dict[str, Any]]:
    """Serialize a BindingTable to HA platform binding rows."""
    return [
        {
            "tag": b.tag,
            "entity": b.entity,
            "direction": b.direction.value,
            "scale": b.scale,
            "offset": b.offset,
            "entity_unit": b.entity_unit,
            "treat_uncertain_as_good": b.treat_uncertain_as_good,
        }
        for b in table.bindings
    ]


def default_tank_datablock() -> Datablock:
    """Fully defined demo Datablock for the tank example (SWD-184 / SWD-183).

    Includes PID faceplate SP-source tags (Manual / Automatic / Remote).
    """
    return datablock_from_dict(
        {
            "id": "DB_Tank",
            "description": "Tank level/flow cascade process I/O (demo).",
            "tags": {
                "LT_TANK": {"default": 0.15, "unit": "m"},
                "LT_RES": {"default": 0.20, "unit": "m"},
                "FT_INLET": {"default": 0.0, "unit": "L/min"},
                # Legacy request alias — automatic SP writer for level loop.
                "SP_LEVEL_REQ": {"default": 0.20, "unit": "m"},
                "SP_LEVEL": {"default": 0.20, "unit": "m"},
                "SP_LEVEL_MAN": {"default": 0.20, "unit": "m"},
                "SP_LEVEL_AUTO": {"default": 0.20, "unit": "m"},
                "SP_LEVEL_REM": {"default": 0.20, "unit": "m"},
                "LEVEL_MODE": {"default": 1.0, "unit": None},
                "LEVEL_KP": {"default": 40.0, "unit": None},
                "LEVEL_KI": {"default": 5.0, "unit": None},
                "LEVEL_KD": {"default": 0.0, "unit": None},
                "SP_FLOW": {"default": 0.0, "unit": "L/min"},
                "SP_FLOW_MAN": {"default": 0.0, "unit": "L/min"},
                "SP_FLOW_AUTO": {"default": 0.0, "unit": "L/min"},
                "SP_FLOW_REM": {"default": 0.0, "unit": "L/min"},
                "FLOW_MODE": {"default": 1.0, "unit": None},
                "FLOW_KP": {"default": 12.0, "unit": None},
                "FLOW_KI": {"default": 2.0, "unit": None},
                "FLOW_KD": {"default": 0.0, "unit": None},
                "CMD_SPEED": {"default": 0.0, "unit": "pct"},
                "CO_LEVEL_MAN": {"default": 0.0, "unit": "L/min"},
                "CO_FLOW_MAN": {"default": 0.0, "unit": "pct"},
                "MODE": {"default": "STOP", "unit": None},
                "PERM_OK": {"default": False, "unit": None},
                "TRIP_ACTIVE": {"default": False, "unit": None},
            },
            "bindings": [
                {
                    "tag": "SP_LEVEL_REQ",
                    "entity": "number.plcassistant_sp_level_req",
                    "direction": "IN",
                },
                {
                    "tag": "SP_LEVEL_MAN",
                    "entity": "number.plcassistant_sp_level_man",
                    "direction": "IN",
                },
                {
                    "tag": "SP_LEVEL_AUTO",
                    "entity": "number.plcassistant_sp_level_auto",
                    "direction": "IN",
                },
                {
                    "tag": "SP_LEVEL_REM",
                    "entity": "number.plcassistant_sp_level_rem",
                    "direction": "IN",
                },
                {
                    "tag": "LEVEL_MODE",
                    "entity": "number.plcassistant_level_mode",
                    "direction": "IN",
                },
                {
                    "tag": "SP_FLOW_MAN",
                    "entity": "number.plcassistant_sp_flow_man",
                    "direction": "IN",
                },
                {
                    "tag": "SP_FLOW_REM",
                    "entity": "number.plcassistant_sp_flow_rem",
                    "direction": "IN",
                },
                {
                    "tag": "FLOW_MODE",
                    "entity": "number.plcassistant_flow_mode",
                    "direction": "IN",
                },
                {
                    "tag": "CO_LEVEL_MAN",
                    "entity": "number.plcassistant_co_level_man",
                    "direction": "IN",
                },
                {
                    "tag": "CO_FLOW_MAN",
                    "entity": "number.plcassistant_co_flow_man",
                    "direction": "IN",
                },
                {
                    "tag": "LT_TANK",
                    "entity": "number.plcassistant_lt_tank_in",
                    "direction": "IN",
                },
                {
                    "tag": "LT_RES",
                    "entity": "number.plcassistant_lt_res_in",
                    "direction": "IN",
                },
                {
                    "tag": "FT_INLET",
                    "entity": "number.plcassistant_ft_inlet_in",
                    "direction": "IN",
                },
                {
                    "tag": "CMD_SPEED",
                    "entity": "sensor.plcassistant_cmd_speed",
                    "direction": "OUT",
                },
                {
                    "tag": "SP_LEVEL",
                    "entity": "sensor.plcassistant_sp_level",
                    "direction": "OUT",
                },
                {
                    "tag": "SP_FLOW",
                    "entity": "sensor.plcassistant_sp_flow",
                    "direction": "OUT",
                },
                {
                    "tag": "SP_FLOW_AUTO",
                    "entity": "sensor.plcassistant_sp_flow_auto",
                    "direction": "OUT",
                },
                {
                    "tag": "MODE",
                    "entity": "sensor.plcassistant_mode",
                    "direction": "OUT",
                },
                {
                    "tag": "PERM_OK",
                    "entity": "sensor.plcassistant_perm_ok",
                    "direction": "OUT",
                },
                {
                    "tag": "TRIP_ACTIVE",
                    "entity": "sensor.plcassistant_trip_active",
                    "direction": "OUT",
                },
                {
                    "tag": "LEVEL_KP",
                    "entity": "number.plcassistant_level_kp",
                    "direction": "IN",
                },
                {
                    "tag": "LEVEL_KI",
                    "entity": "number.plcassistant_level_ki",
                    "direction": "IN",
                },
                {
                    "tag": "FLOW_KP",
                    "entity": "number.plcassistant_flow_kp",
                    "direction": "IN",
                },
                {
                    "tag": "FLOW_KI",
                    "entity": "number.plcassistant_flow_ki",
                    "direction": "IN",
                },
                {
                    "tag": "LEVEL_KD",
                    "entity": "number.plcassistant_level_kd",
                    "direction": "IN",
                },
                {
                    "tag": "FLOW_KD",
                    "entity": "number.plcassistant_flow_kd",
                    "direction": "IN",
                },
            ],
        }
    )


def default_tank_datablock_catalog() -> DatablockCatalog:
    catalog = DatablockCatalog()
    catalog.upsert(default_tank_datablock())
    return catalog


def default_program_datablock_access() -> dict[str, list[str]]:
    return {"tank": ["DB_Tank"]}


__all__ = [
    "Datablock",
    "DatablockCatalog",
    "binding_rows_from_table",
    "datablock_from_dict",
    "datablock_to_dict",
    "default_program_datablock_access",
    "default_tank_datablock",
    "default_tank_datablock_catalog",
    "program_accessible_tags",
    "union_program_access_ids",
]
