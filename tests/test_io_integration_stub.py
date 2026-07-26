"""Unit tests for thin-integration stub + mock entity store (SWD-99)."""

from __future__ import annotations

import pytest

from plcassistant.io import (
    Binding,
    BindingTable,
    Direction,
    IoImage,
    MockEntityStore,
    QualityStatus,
    ReasonCode,
    TagDecl,
    ThinIntegrationStub,
)


CONFIG = {
    "tags": {
        "LT_TANK": {"default": 0.0, "unit": "m"},
        "CMD_SPEED": {"default": 0.0, "unit": "pct"},
    },
    "bindings": [
        {
            "tag": "LT_TANK",
            "entity": "sensor.tank_level",
            "direction": "IN",
            "scale": 0.01,
            "offset": 0.0,
        },
        {
            "tag": "CMD_SPEED",
            "entity": "number.cmd_speed",
            "direction": "OUT",
        },
    ],
}


def test_mock_entity_to_image_in_with_units():
    stub = ThinIntegrationStub(CONFIG)
    image = stub.attach()
    stub.entities.set("sensor.tank_level", 25.0)  # raw → 0.25 m

    stub.scan_inputs(image)

    assert image.get_value("LT_TANK") == pytest.approx(0.25)
    assert image.get_quality("LT_TANK").status is QualityStatus.GOOD


def test_image_out_to_mock_entity_every_scan():
    stub = ThinIntegrationStub(CONFIG)
    image = stub.attach()
    stub.entities.set("sensor.tank_level", 10.0)

    def logic(img: IoImage) -> None:
        img.set_output("CMD_SPEED", 40.0)

    flush1 = stub.run_scan(image, logic)
    assert flush1 == {"number.cmd_speed": pytest.approx(40.0)}
    assert stub.entities.get("number.cmd_speed").value == pytest.approx(40.0)
    assert stub.entities.get("number.cmd_speed").status is QualityStatus.GOOD

    def logic2(img: IoImage) -> None:
        img.set_output("CMD_SPEED", 55.0)

    stub.run_scan(image, logic2)
    # Flushed every scan (no change-detect)
    assert stub.entities.get("number.cmd_speed").value == pytest.approx(55.0)


def test_missing_entity_bad_unavailable_default_then_last_good():
    stub = ThinIntegrationStub(CONFIG)
    image = stub.attach()

    # Never present: BAD / unavailable + default
    stub.scan_inputs(image)
    assert image.get_value("LT_TANK") == 0.0
    q = image.get_quality("LT_TANK")
    assert q.status is QualityStatus.BAD
    assert q.reason is ReasonCode.UNAVAILABLE

    # First GOOD establishes last-good
    stub.entities.set("sensor.tank_level", 30.0)  # → 0.30 m
    stub.scan_inputs(image)
    assert image.get_value("LT_TANK") == pytest.approx(0.30)
    assert image.get_quality("LT_TANK").status is QualityStatus.GOOD

    # Entity removed → BAD / unavailable retains last-good
    stub.entities.remove("sensor.tank_level")
    stub.scan_inputs(image)
    assert image.get_value("LT_TANK") == pytest.approx(0.30)
    q = image.get_quality("LT_TANK")
    assert q.status is QualityStatus.BAD
    assert q.reason is ReasonCode.UNAVAILABLE


def test_mock_path_same_api_as_field_different_store_values():
    """Mock and “field” both go through BindingTable.apply_in/apply_out."""
    table = BindingTable.from_config(CONFIG)
    image_mock = IoImage()
    image_field = IoImage()
    table.declare_on(image_mock)
    table.declare_on(image_field)

    mock_store = MockEntityStore()
    field_store = MockEntityStore()
    mock_stub = ThinIntegrationStub(table, entities=mock_store)
    field_stub = ThinIntegrationStub(table, entities=field_store)

    mock_store.set("sensor.tank_level", 20.0)  # → 0.20 m
    field_store.set("sensor.tank_level", 40.0)  # → 0.40 m

    mock_stub.scan_inputs(image_mock)
    field_stub.scan_inputs(image_field)

    assert image_mock.get_value("LT_TANK") == pytest.approx(0.20)
    assert image_field.get_value("LT_TANK") == pytest.approx(0.40)

    image_mock.set_output("CMD_SPEED", 11.0)
    image_field.set_output("CMD_SPEED", 22.0)
    mock_stub.scan_outputs(image_mock)
    field_stub.scan_outputs(image_field)

    assert mock_store.get("number.cmd_speed").value == pytest.approx(11.0)
    assert field_store.get("number.cmd_speed").value == pytest.approx(22.0)


def test_multi_in_single_out_enforced_via_binding_table():
    # Multi-IN same entity OK through stub construction
    multi = ThinIntegrationStub(
        {
            "tags": {
                "LT_A": {"default": 0.0},
                "LT_B": {"default": 0.0},
                "CMD": {"default": 0.0},
            },
            "bindings": [
                {"tag": "LT_A", "entity": "sensor.shared", "direction": "IN"},
                {
                    "tag": "LT_B",
                    "entity": "sensor.shared",
                    "direction": "IN",
                    "scale": 100.0,
                },
                {"tag": "CMD", "entity": "number.cmd", "direction": "OUT"},
            ],
        }
    )
    image = multi.attach()
    multi.entities.set("sensor.shared", 0.5)
    multi.scan_inputs(image)
    assert image.get_value("LT_A") == pytest.approx(0.5)
    assert image.get_value("LT_B") == pytest.approx(50.0)

    # Dual OUT writers still rejected by BindingTable
    with pytest.raises(ValueError, match="duplicate OUT writer"):
        ThinIntegrationStub(
            {
                "tags": {
                    "A": {"default": 0.0},
                    "B": {"default": 0.0},
                },
                "bindings": [
                    {"tag": "A", "entity": "number.x", "direction": "OUT"},
                    {"tag": "B", "entity": "number.x", "direction": "OUT"},
                ],
            }
        )


def test_attach_declares_on_provided_image():
    stub = ThinIntegrationStub(CONFIG)
    image = IoImage()
    returned = stub.attach(image)
    assert returned is image
    assert stub.image is image
    assert "LT_TANK" in image.names()
    assert "CMD_SPEED" in image.names()


def test_construct_from_binding_table():
    table = BindingTable(
        tags={"T": TagDecl("T", default=1.0)},
        bindings=[Binding("T", "sensor.t", Direction.IN)],
    )
    stub = ThinIntegrationStub(table)
    image = stub.attach()
    stub.entities.set("sensor.t", 3.0)
    stub.scan_inputs(image)
    assert image.get_value("T") == pytest.approx(3.0)


def test_mock_store_get_missing_is_unavailable():
    store = MockEntityStore()
    sample = store.get("sensor.missing")
    assert sample.status is QualityStatus.BAD
    assert sample.reason is ReasonCode.UNAVAILABLE
    assert store.has("sensor.missing") is False


def test_scan_outputs_skips_never_written_out_tags():
    """Never-written OUT must not appear in the entity store as GOOD."""
    stub = ThinIntegrationStub(CONFIG)
    image = stub.attach()
    stub.entities.set("sensor.tank_level", 10.0)

    stub.scan_inputs(image)
    flush = stub.scan_outputs(image)
    assert flush == {}
    assert stub.entities.has("number.cmd_speed") is False

    image.set_output("CMD_SPEED", 12.0)
    flush = stub.scan_outputs(image)
    assert flush == {"number.cmd_speed": pytest.approx(12.0)}
    assert stub.entities.get("number.cmd_speed").status is QualityStatus.GOOD
    assert stub.entities.get("number.cmd_speed").value == pytest.approx(12.0)


def test_entity_sample_composes_tag_quality_validation():
    from plcassistant.io import EntitySample

    with pytest.raises(ValueError):
        EntitySample(value=1.0, status=QualityStatus.GOOD, reason=ReasonCode.FAULT)
    with pytest.raises(ValueError):
        EntitySample(value=1.0, status=QualityStatus.BAD)
