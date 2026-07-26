"""Directional HA entity ↔ Soft-PLC tag bindings (docs/io/02-binding-model.md)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from plcassistant.io.image import IoImage
from plcassistant.io.quality import QualityStatus, ReasonCode, TagQuality, is_good


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
    """Tag declaration owned by the thin integration (default + optional unit hint)."""

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
    """API retained for future Soft-PLC wiring; safety uses ``is_good`` only for now."""

    def __post_init__(self) -> None:
        if self.scale == 0:
            raise ValueError(f"binding scale must be non-zero for tag {self.tag!r}")

    def to_engineering(self, raw: float) -> float:
        """HA raw → engineering units on the tag (IN path)."""
        return raw * self.scale + self.offset

    def to_raw(self, engineering: float) -> float:
        """Engineering units on the tag → HA raw (OUT path)."""
        return (engineering - self.offset) / self.scale

    def usable_for_safety(self, quality: TagQuality | QualityStatus) -> bool:
        """Safety collapse helper.

        Soft-PLC wiring of ``treat_uncertain_as_good`` is deferred: callers that
        mirror production safety should use ``is_good`` only. This method still
        honours the flag when opted in (API retained for a later package).
        """
        if is_good(quality):
            return True
        status = quality.status if isinstance(quality, TagQuality) else quality
        if status is QualityStatus.UNCERTAIN and self.treat_uncertain_as_good:
            return True
        return False


def _parse_direction(value: str | Direction) -> Direction:
    if isinstance(value, Direction):
        return value
    try:
        return Direction(str(value).upper())
    except ValueError as exc:
        raise ValueError(f"invalid direction: {value!r}") from exc


def _parse_sample(
    sample: Any,
) -> tuple[Any, QualityStatus, ReasonCode | None]:
    """Accept a raw number (→ GOOD) or (value, status, reason).

    Non-GOOD samples **require** a reason code. A 2-tuple is only valid when
    status is GOOD (reason omitted); otherwise raise ``ValueError``.
    """
    if isinstance(sample, tuple):
        if len(sample) == 2:
            value, status = sample
            reason = None
        elif len(sample) == 3:
            value, status, reason = sample
        else:
            raise ValueError(
                "entity sample tuple must be (value, status) or (value, status, reason)"
            )
        if not isinstance(status, QualityStatus):
            status = QualityStatus(status)
        if reason is not None and not isinstance(reason, ReasonCode):
            reason = ReasonCode(reason)
        if status is QualityStatus.GOOD:
            if reason is not None:
                raise ValueError("GOOD sample must not carry a reason code")
        elif reason is None:
            raise ValueError(f"{status.value} sample requires a reason code")
        return value, status, reason
    return sample, QualityStatus.GOOD, None


class BindingTable:
    """Validated set of tag declarations and directional bindings.

    Uniqueness: many IN bindings may share an entity; at most one OUT writer
    (OUT or INOUT) per entity. At most one binding per tag.
    """

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

    def declare_on(self, image: IoImage) -> None:
        """Declare all configured tags on an I/O image."""
        for decl in self._tags.values():
            image.declare(decl.name, default=decl.default)

    def apply_in(
        self,
        image: IoImage,
        entity_samples: Mapping[str, Any],
    ) -> None:
        """Scan-start: for each IN/INOUT binding, convert (when GOOD) and apply_input.

        ``entity_samples`` maps entity id → raw number (treated as GOOD) or
        ``(value, QualityStatus, ReasonCode)`` (reason required when not GOOD).
        OUT-only bindings are skipped. Missing entity keys are applied as
        ``BAD`` / ``unavailable`` (same as the thin-integration stub).
        """
        image.begin_inputs()
        for binding in self._bindings:
            if not binding.direction.reads:
                continue
            if binding.entity not in entity_samples:
                image.apply_input(
                    binding.tag,
                    0.0,
                    QualityStatus.BAD,
                    ReasonCode.UNAVAILABLE,
                )
                continue
            raw, status, reason = _parse_sample(entity_samples[binding.entity])
            if status is QualityStatus.GOOD:
                engineering = binding.to_engineering(float(raw))
                image.apply_input(binding.tag, engineering, status, reason)
            else:
                # Placeholder only: do not float/scale non-GOOD payloads (may be None).
                image.apply_input(binding.tag, 0.0, status, reason)

    def apply_out(self, image: IoImage) -> dict[str, float]:
        """Scan-end: convert written OUT/INOUT tag values to HA raw.

        Only tags present in ``image.snapshot_outputs()`` (logic called
        ``set_output`` / ``is_output``) are flushed. Never-written OUT bindings
        are omitted so callers do not publish defaults as GOOD.
        """
        written = image.snapshot_outputs()
        flush: dict[str, float] = {}
        for binding in self._bindings:
            if not binding.direction.writes:
                continue
            if binding.tag not in written:
                continue
            engineering = float(written[binding.tag])
            flush[binding.entity] = binding.to_raw(engineering)
        return flush
