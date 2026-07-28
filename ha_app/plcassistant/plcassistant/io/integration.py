"""Thin-integration stub: mock entities + scan-boundary image refresh (SWD-99).

Owns tag declarations / bindings / units / mock entity store. The Add-on owns
the live ``IoImage``; this stub only feeds INs and sinks OUTs via
``BindingTable.apply_in`` / ``apply_out`` (mock path ≡ field path).

No Home Assistant dependency. Real HA path is MQTT (SWD-84): see
``plcassistant.io.mqtt_entity_bridge`` and ``custom_components/plcassistant/``.
This stub remains the non-HA pytest path (mock path ≡ field path).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from plcassistant.io.binding import BindingTable
from plcassistant.io.image import IoImage
from plcassistant.io.quality import QualityStatus, ReasonCode, TagQuality


@dataclass(frozen=True)
class EntitySample:
    """One mock (or field-shaped) entity sample."""

    value: Any
    status: QualityStatus = QualityStatus.GOOD
    reason: ReasonCode | None = None

    def __post_init__(self) -> None:
        # Compose TagQuality validation (GOOD ↔ reason rules) instead of duplicating.
        TagQuality(self.status, self.reason)

    def as_apply_sample(self) -> Any:
        """Shape accepted by ``BindingTable.apply_in`` entity_samples values."""
        if self.status is QualityStatus.GOOD and self.reason is None:
            return self.value
        return (self.value, self.status, self.reason)


_MISSING = EntitySample(
    value=0.0,
    status=QualityStatus.BAD,
    reason=ReasonCode.UNAVAILABLE,
)


class MockEntityStore:
    """In-memory entity id → (value, quality, reason) for stub / tests.

    Missing entities read as ``BAD`` / ``unavailable`` (same quality contract as
    an absent field sample). Set/get are for tests and mock drivers.
    """

    def __init__(self) -> None:
        self._entities: dict[str, EntitySample] = {}

    def set(
        self,
        entity_id: str,
        value: Any,
        status: QualityStatus = QualityStatus.GOOD,
        reason: ReasonCode | None = None,
    ) -> None:
        """Write or replace an entity sample."""
        self._entities[entity_id] = EntitySample(value=value, status=status, reason=reason)

    def get(self, entity_id: str) -> EntitySample:
        """Return the stored sample, or BAD/unavailable if the entity is missing."""
        return self._entities.get(entity_id, _MISSING)

    def has(self, entity_id: str) -> bool:
        return entity_id in self._entities

    def clear(self) -> None:
        self._entities.clear()

    def remove(self, entity_id: str) -> None:
        self._entities.pop(entity_id, None)

    def ids(self) -> tuple[str, ...]:
        return tuple(self._entities)


class ThinIntegrationStub:
    """Thin integration stand-in: bindings + mock store + scan IN/OUT API.

    Construct from a config dict (``tags`` / ``bindings``) or an existing
    ``BindingTable``. Holds a ``MockEntityStore``. Attach (or create) an
    Add-on-owned ``IoImage``, then call ``scan_inputs`` / ``scan_outputs`` on
    each scan boundary (in-process API; HA IPC comes later / SWD-84).
    """

    def __init__(
        self,
        config_or_table: Mapping[str, Any] | BindingTable,
        *,
        entities: MockEntityStore | None = None,
    ) -> None:
        if isinstance(config_or_table, BindingTable):
            self._table = config_or_table
        else:
            self._table = BindingTable.from_config(config_or_table)
        self._entities = entities if entities is not None else MockEntityStore()
        self._image: IoImage | None = None

    @property
    def table(self) -> BindingTable:
        return self._table

    @property
    def entities(self) -> MockEntityStore:
        return self._entities

    @property
    def image(self) -> IoImage | None:
        """Last image passed to ``attach``, if any."""
        return self._image

    def attach(self, image: IoImage | None = None) -> IoImage:
        """Declare configured tags on ``image`` (or a new ``IoImage``) and retain it.

        The Add-on owns the live image; the stub only declares tags via
        ``BindingTable.declare_on``.
        """
        if image is None:
            image = IoImage()
        self._table.declare_on(image)
        self._image = image
        return image

    def scan_inputs(self, image: IoImage) -> None:
        """Scan start: read mock store → ``BindingTable.apply_in`` for IN/INOUT.

        Missing entities become ``BAD`` / ``unavailable`` samples so the image
        retains last-good or default (same path as a bad field sample).
        """
        samples: dict[str, Any] = {}
        for binding in self._table.bindings:
            if not binding.direction.reads:
                continue
            samples[binding.entity] = self._entities.get(binding.entity).as_apply_sample()
        self._table.apply_in(image, samples)

    def scan_outputs(self, image: IoImage) -> dict[str, float]:
        """Scan end: ``BindingTable.apply_out`` → write raw values into the store.

        Only tags logic wrote (``set_output`` / ``is_output``) are flushed —
        never-written OUT bindings are omitted. Entity quality follows the
        image tag (do not force GOOD for non-GOOD / never-written tags).
        Returns entity → raw.
        """
        flush = self._table.apply_out(image)
        by_entity = {
            binding.entity: binding
            for binding in self._table.bindings
            if binding.direction.writes
        }
        for entity_id, raw in flush.items():
            binding = by_entity[entity_id]
            quality = image.get_quality(binding.tag)
            self._entities.set(entity_id, raw, quality.status, quality.reason)
        return flush

    def run_scan(
        self,
        image: IoImage,
        logic: Callable[[IoImage], None],
    ) -> dict[str, float]:
        """Test helper: ``scan_inputs`` → ``logic(image)`` → ``scan_outputs``."""
        self.scan_inputs(image)
        logic(image)
        return self.scan_outputs(image)
