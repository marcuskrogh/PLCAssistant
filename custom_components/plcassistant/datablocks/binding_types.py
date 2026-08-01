"""HA-local binding types for Datablocks (SWD-219).

Thin integration runs in HA Core and must not import Soft-PLC ``plcassistant``.
This is a schema-only subset of ``plcassistant.io.binding`` (no IoImage).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class Direction(str, Enum):
    """Strictly declared binding direction — never inferred."""

    IN = "IN"
    OUT = "OUT"
    INOUT = "INOUT"

    @property
    def reads(self) -> bool:
        return self is Direction.IN or self is Direction.INOUT

    @property
    def writes(self) -> bool:
        return self is Direction.OUT or self is Direction.INOUT


@dataclass(frozen=True)
class TagDecl:
    """Tag declaration owned by the thin integration."""

    name: str
    default: Any
    unit: str | None = None


@dataclass(frozen=True)
class Binding:
    """One declared tag↔entity link with linear unit conversion."""

    tag: str
    entity: str
    direction: Direction
    scale: float = 1.0
    offset: float = 0.0
    entity_unit: str | None = None
    treat_uncertain_as_good: bool = False

    def __post_init__(self) -> None:
        if self.scale == 0:
            raise ValueError(f"binding scale must be non-zero for tag {self.tag!r}")


def _parse_direction(value: str | Direction) -> Direction:
    if isinstance(value, Direction):
        return value
    try:
        return Direction(str(value).upper())
    except ValueError as exc:
        raise ValueError(f"invalid direction: {value!r}") from exc


class BindingTable:
    """Validated set of tag declarations and directional bindings."""

    def __init__(
        self,
        tags: Mapping[str, TagDecl] | None = None,
        bindings: list[Binding] | None = None,
    ) -> None:
        self._tags: dict[str, TagDecl] = dict(tags or {})
        self._bindings: list[Binding] = list(bindings or [])
        self._by_tag: dict[str, Binding] = {}
        self._validate()

    def _validate(self) -> None:
        out_writer: dict[str, Binding] = {}
        for binding in self._bindings:
            if binding.tag in self._by_tag:
                raise ValueError(f"duplicate binding for tag: {binding.tag!r}")
            if binding.tag not in self._tags:
                raise ValueError(f"binding references undeclared tag: {binding.tag!r}")
            self._by_tag[binding.tag] = binding
            if binding.direction.writes:
                prior = out_writer.get(binding.entity)
                if prior is not None:
                    raise ValueError(
                        "duplicate OUT writer for entity "
                        f"{binding.entity!r}: tags {prior.tag!r} and {binding.tag!r}"
                    )
                out_writer[binding.entity] = binding

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> BindingTable:
        """Load from the YAML-oriented dict schema in docs/io/02-binding-model.md."""
        raw_tags = config.get("tags") or {}
        if not isinstance(raw_tags, Mapping):
            raise ValueError("config 'tags' must be a mapping")
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

        raw_bindings = config.get("bindings") or []
        if not isinstance(raw_bindings, list):
            raise ValueError("config 'bindings' must be a list")
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
                    treat_uncertain_as_good=bool(
                        item.get("treat_uncertain_as_good", False)
                    ),
                )
            )
        return cls(tags=tags, bindings=bindings)

    @property
    def tags(self) -> Mapping[str, TagDecl]:
        return self._tags

    @property
    def bindings(self) -> tuple[Binding, ...]:
        return tuple(self._bindings)

    def binding_for(self, tag: str) -> Binding:
        try:
            return self._by_tag[tag]
        except KeyError as exc:
            raise KeyError(f"no binding for tag: {tag!r}") from exc


__all__ = [
    "Binding",
    "BindingTable",
    "Direction",
    "TagDecl",
]
