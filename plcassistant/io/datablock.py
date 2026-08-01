"""Named Datablocks grouping tags and HA entity bindings (SWD-184).

Datablocks are industrial I/O packages owned by the thin HA integration.
Soft-PLC Programs declare which Datablock id(s) they can access; Soft-PLC
only sees the union of those tags.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from plcassistant.io.binding import Binding, BindingTable, Direction, TagDecl, _parse_direction


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
    raw_tags = data.get("tags") or {}
    if not isinstance(raw_tags, Mapping):
        raise ValueError("datablock 'tags' must be a mapping")
    tags: dict[str, TagDecl] = {}
    for name, spec in raw_tags.items():
        if not isinstance(spec, Mapping):
            raise ValueError(f"tag {name!r} spec must be a mapping")
        if "default" not in spec:
            raise ValueError(f"tag {name!r} requires 'default'")
        tags[str(name)] = TagDecl(
            name=str(name),
            default=spec["default"],
            unit=spec.get("unit"),
        )
    raw_bindings = data.get("bindings") or []
    if not isinstance(raw_bindings, list):
        raise ValueError("datablock 'bindings' must be a list")
    bindings: list[Binding] = []
    for i, item in enumerate(raw_bindings):
        if not isinstance(item, Mapping):
            raise ValueError(f"bindings[{i}] must be a mapping")
        for key in ("tag", "entity", "direction"):
            if key not in item:
                raise ValueError(f"bindings[{i}] missing required key {key!r}")
        bindings.append(
            Binding(
                tag=str(item["tag"]),
                entity=str(item["entity"]),
                direction=_parse_direction(item["direction"]),
                scale=float(item.get("scale", 1.0)),
                offset=float(item.get("offset", 0.0)),
                entity_unit=item.get("entity_unit"),
                treat_uncertain_as_good=bool(item.get("treat_uncertain_as_good", False)),
            )
        )
    return Datablock(
        datablock_id=db_id,
        description=str(data.get("description") or ""),
        tags=tags,
        bindings=bindings,
    )


def program_accessible_tags(
    catalog: DatablockCatalog,
    datablock_ids: list[str] | tuple[str, ...] | None,
) -> frozenset[str]:
    """Tags a Soft-PLC Program may see given its Datablock access list."""
    return catalog.tag_names_for(list(datablock_ids or ()))


def default_tank_datablock() -> Datablock:
    """Fully defined demo Datablock for the tank example (SWD-184)."""
    tags = {
        "LT_TANK": TagDecl("LT_TANK", 0.15, "m"),
        "LT_RES": TagDecl("LT_RES", 0.20, "m"),
        "FT_INLET": TagDecl("FT_INLET", 0.0, "L/min"),
        "SP_LEVEL_REQ": TagDecl("SP_LEVEL_REQ", 0.20, "m"),
        "SP_LEVEL": TagDecl("SP_LEVEL", 0.20, "m"),
        "SP_FLOW": TagDecl("SP_FLOW", 0.0, "L/min"),
        "CMD_SPEED": TagDecl("CMD_SPEED", 0.0, "pct"),
        "MODE": TagDecl("MODE", "STOP", None),
        "PERM_OK": TagDecl("PERM_OK", False, None),
        "TRIP_ACTIVE": TagDecl("TRIP_ACTIVE", False, None),
    }
    bindings = [
        Binding("SP_LEVEL_REQ", "number.plcassistant_sp_level_req", Direction.IN),
        Binding("LT_TANK", "number.plcassistant_lt_tank_in", Direction.IN),
        Binding("LT_RES", "number.plcassistant_lt_res_in", Direction.IN),
        Binding("FT_INLET", "number.plcassistant_ft_inlet_in", Direction.IN),
        Binding("CMD_SPEED", "sensor.plcassistant_cmd_speed", Direction.OUT),
        Binding("SP_LEVEL", "sensor.plcassistant_sp_level", Direction.OUT),
        Binding("SP_FLOW", "sensor.plcassistant_sp_flow", Direction.OUT),
        Binding("MODE", "sensor.plcassistant_mode", Direction.OUT),
        Binding("PERM_OK", "sensor.plcassistant_perm_ok", Direction.OUT),
        Binding("TRIP_ACTIVE", "sensor.plcassistant_trip_active", Direction.OUT),
    ]
    return Datablock(
        datablock_id="DB_Tank",
        description="Tank level/flow cascade process I/O (demo).",
        tags=tags,
        bindings=bindings,
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
    "datablock_from_dict",
    "datablock_to_dict",
    "default_program_datablock_access",
    "default_tank_datablock",
    "default_tank_datablock_catalog",
    "program_accessible_tags",
]
