"""Unit tests for directional bindings, units, uniqueness, and config load (SWD-98)."""

from __future__ import annotations

import pytest

from plcassistant.io import (
    Binding,
    BindingTable,
    Direction,
    IoImage,
    QualityStatus,
    ReasonCode,
    TagDecl,
    TagQuality,
)


def _level_table(*, scale: float = 1.0, offset: float = 0.0) -> BindingTable:
    return BindingTable(
        tags={"LT_TANK": TagDecl("LT_TANK", default=0.0, unit="m")},
        bindings=[
            Binding(
                tag="LT_TANK",
                entity="sensor.tank_level",
                direction=Direction.IN,
                scale=scale,
                offset=offset,
                entity_unit="m",
            )
        ],
    )


def test_direction_in_applies_to_image_out_does_not_read():
    """IN bindings feed apply_in; OUT-only bindings are skipped on the IN path."""
    table = BindingTable(
        tags={
            "LT_TANK": TagDecl("LT_TANK", default=0.0),
            "CMD_SPEED": TagDecl("CMD_SPEED", default=0.0),
        },
        bindings=[
            Binding("LT_TANK", "sensor.tank_level", Direction.IN),
            Binding("CMD_SPEED", "number.cmd_speed", Direction.OUT),
        ],
    )
    image = IoImage()
    table.declare_on(image)

    table.apply_in(
        image,
        {
            "sensor.tank_level": 0.25,
            "number.cmd_speed": 99.0,  # OUT-only: must not become an input sample
        },
    )
    assert image.get_value("LT_TANK") == pytest.approx(0.25)
    assert image.get_quality("LT_TANK").status is QualityStatus.GOOD
    # CMD_SPEED never received apply_input; still initial BAD / default
    assert image.get_value("CMD_SPEED") == 0.0
    assert image.get_quality("CMD_SPEED").status is QualityStatus.BAD


def test_direction_out_flushes_writers_skips_in():
    table = BindingTable(
        tags={
            "LT_TANK": TagDecl("LT_TANK", default=0.0),
            "CMD_SPEED": TagDecl("CMD_SPEED", default=0.0),
        },
        bindings=[
            Binding("LT_TANK", "sensor.tank_level", Direction.IN),
            Binding("CMD_SPEED", "number.cmd_speed", Direction.OUT),
        ],
    )
    image = IoImage()
    table.declare_on(image)
    image.set_output("CMD_SPEED", 40.0)

    flush = table.apply_out(image)
    assert flush == {"number.cmd_speed": pytest.approx(40.0)}
    assert "sensor.tank_level" not in flush


def test_inout_reads_and_writes():
    table = BindingTable(
        tags={"SP_BIDIR": TagDecl("SP_BIDIR", default=0.0)},
        bindings=[
            Binding("SP_BIDIR", "input_number.sp", Direction.INOUT, scale=2.0, offset=1.0)
        ],
    )
    image = IoImage()
    table.declare_on(image)
    # raw 3 → eng = 3*2+1 = 7
    table.apply_in(image, {"input_number.sp": 3.0})
    assert image.get_value("SP_BIDIR") == pytest.approx(7.0)
    image.set_output("SP_BIDIR", 11.0)
    # eng 11 → raw = (11-1)/2 = 5
    assert table.apply_out(image) == {"input_number.sp": pytest.approx(5.0)}


def test_multi_in_same_entity_ok():
    table = BindingTable(
        tags={
            "LT_A": TagDecl("LT_A", default=0.0),
            "LT_B": TagDecl("LT_B", default=0.0),
        },
        bindings=[
            Binding("LT_A", "sensor.shared_level", Direction.IN),
            Binding("LT_B", "sensor.shared_level", Direction.IN, scale=100.0),
        ],
    )
    image = IoImage()
    table.declare_on(image)
    table.apply_in(image, {"sensor.shared_level": 0.5})
    assert image.get_value("LT_A") == pytest.approx(0.5)
    assert image.get_value("LT_B") == pytest.approx(50.0)


def test_two_out_same_entity_rejected():
    with pytest.raises(ValueError, match="duplicate OUT writer"):
        BindingTable(
            tags={
                "CMD_A": TagDecl("CMD_A", default=0.0),
                "CMD_B": TagDecl("CMD_B", default=0.0),
            },
            bindings=[
                Binding("CMD_A", "number.speed", Direction.OUT),
                Binding("CMD_B", "number.speed", Direction.OUT),
            ],
        )


def test_out_plus_inout_same_entity_rejected():
    with pytest.raises(ValueError, match="duplicate OUT writer"):
        BindingTable(
            tags={
                "CMD_A": TagDecl("CMD_A", default=0.0),
                "SP_X": TagDecl("SP_X", default=0.0),
            },
            bindings=[
                Binding("CMD_A", "number.speed", Direction.OUT),
                Binding("SP_X", "number.speed", Direction.INOUT),
            ],
        )


def test_unit_scale_offset_in_and_out():
    # IN: eng = raw * 0.01 + 0.1  (e.g. percent raw → meters-ish)
    table = BindingTable(
        tags={
            "LT_TANK": TagDecl("LT_TANK", default=0.0, unit="m"),
            "CMD_VALVE": TagDecl("CMD_VALVE", default=0.0, unit="pct"),
        },
        bindings=[
            Binding(
                "LT_TANK",
                "sensor.tank_raw",
                Direction.IN,
                scale=0.01,
                offset=0.1,
            ),
            Binding(
                "CMD_VALVE",
                "number.valve_raw",
                Direction.OUT,
                scale=10.0,
                offset=-5.0,
            ),
        ],
    )
    image = IoImage()
    table.declare_on(image)
    table.apply_in(image, {"sensor.tank_raw": 20.0})
    assert image.get_value("LT_TANK") == pytest.approx(0.3)  # 20*0.01+0.1

    image.set_output("CMD_VALVE", 45.0)
    # raw = (45 - (-5)) / 10 = 5.0
    assert table.apply_out(image) == {"number.valve_raw": pytest.approx(5.0)}


def test_setpoint_split_in_request_out_active():
    """Default setpoint pattern: split IN (request) + OUT (active), not INOUT."""
    config = {
        "tags": {
            "SP_SPEED_REQ": {"default": 0.0, "unit": "pct"},
            "SP_SPEED": {"default": 0.0, "unit": "pct"},
        },
        "bindings": [
            {
                "tag": "SP_SPEED_REQ",
                "entity": "input_number.speed_setpoint",
                "direction": "IN",
            },
            {
                "tag": "SP_SPEED",
                "entity": "sensor.speed_setpoint_active",
                "direction": "OUT",
            },
        ],
    }
    table = BindingTable.from_config(config)
    assert table.binding_for("SP_SPEED_REQ").direction is Direction.IN
    assert table.binding_for("SP_SPEED").direction is Direction.OUT
    assert not any(b.direction is Direction.INOUT for b in table.bindings)

    image = IoImage()
    table.declare_on(image)
    table.apply_in(image, {"input_number.speed_setpoint": 55.0})
    assert image.get_value("SP_SPEED_REQ") == pytest.approx(55.0)
    # Logic copies request → active (stub behaviour for the test)
    image.set_output("SP_SPEED", image.get_value("SP_SPEED_REQ"))
    flush = table.apply_out(image)
    assert flush == {"sensor.speed_setpoint_active": pytest.approx(55.0)}


def test_from_config_dict_round_trip_fields():
    config = {
        "tags": {"LT_TANK": {"default": 0.05, "unit": "m"}},
        "bindings": [
            {
                "tag": "LT_TANK",
                "entity": "sensor.tank_level",
                "direction": "IN",
                "entity_unit": "cm",
                "scale": 0.01,
                "offset": 0.0,
                "treat_uncertain_as_good": True,
            }
        ],
    }
    table = BindingTable.from_config(config)
    assert table.tags["LT_TANK"].default == 0.05
    assert table.tags["LT_TANK"].unit == "m"
    b = table.bindings[0]
    assert b.entity == "sensor.tank_level"
    assert b.direction is Direction.IN
    assert b.entity_unit == "cm"
    assert b.scale == 0.01
    assert b.treat_uncertain_as_good is True

    image = IoImage()
    table.declare_on(image)
    assert image.get_value("LT_TANK") == 0.05
    table.apply_in(
        image,
        {
            "sensor.tank_level": (
                120.0,
                QualityStatus.UNCERTAIN,
                ReasonCode.STALE,
            )
        },
    )
    # Image retention unchanged: UNCERTAIN does not overwrite last-good/default
    assert image.get_value("LT_TANK") == 0.05
    assert image.get_quality("LT_TANK").status is QualityStatus.UNCERTAIN
    assert b.usable_for_safety(image.get_quality("LT_TANK")) is True
    assert b.usable_for_safety(TagQuality(QualityStatus.BAD, ReasonCode.FAULT)) is False


def test_from_config_rejects_duplicate_out_writer():
    with pytest.raises(ValueError, match="duplicate OUT writer"):
        BindingTable.from_config(
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


def test_zero_scale_rejected():
    with pytest.raises(ValueError, match="scale must be non-zero"):
        Binding("T", "e", Direction.IN, scale=0.0)


def test_undeclared_tag_and_duplicate_tag_binding():
    with pytest.raises(ValueError, match="undeclared tag"):
        BindingTable(
            tags={},
            bindings=[Binding("MISSING", "sensor.x", Direction.IN)],
        )
    with pytest.raises(ValueError, match="duplicate binding for tag"):
        BindingTable(
            tags={"T": TagDecl("T", default=0.0)},
            bindings=[
                Binding("T", "sensor.a", Direction.IN),
                Binding("T", "sensor.b", Direction.IN),
            ],
        )


def test_apply_in_non_good_none_keeps_last_good():
    """Non-GOOD may carry None; must not float(raw) before apply_input."""
    table = _level_table()
    image = IoImage()
    table.declare_on(image)
    table.apply_in(image, {"sensor.tank_level": 0.42})
    assert image.get_value("LT_TANK") == pytest.approx(0.42)

    table.apply_in(
        image,
        {
            "sensor.tank_level": (
                None,
                QualityStatus.BAD,
                ReasonCode.UNAVAILABLE,
            )
        },
    )
    assert image.get_value("LT_TANK") == pytest.approx(0.42)
    q = image.get_quality("LT_TANK")
    assert q.status is QualityStatus.BAD
    assert q.reason is ReasonCode.UNAVAILABLE


def test_apply_in_good_none_demotes_unavailable_retains_last_good():
    """GOOD path with None must not float(raw) / abort; demote BAD+unavailable."""
    table = _level_table()
    image = IoImage()
    table.declare_on(image)
    table.apply_in(image, {"sensor.tank_level": 0.42})
    assert image.get_value("LT_TANK") == pytest.approx(0.42)

    table.apply_in(image, {"sensor.tank_level": None})
    assert image.get_value("LT_TANK") == pytest.approx(0.42)
    q = image.get_quality("LT_TANK")
    assert q.status is QualityStatus.BAD
    assert q.reason is ReasonCode.UNAVAILABLE


def test_apply_in_good_none_via_store_set_does_not_leave_stale_good():
    """store.set(entity, None) as GOOD → BAD unavailable; mid-scan peers still apply."""
    from plcassistant.io.integration import MockEntityStore, ThinIntegrationStub

    config = {
        "tags": {
            "LT_TANK": {"default": 0.0},
            "LT_RES": {"default": 0.0},
        },
        "bindings": [
            {
                "tag": "LT_TANK",
                "entity": "sensor.tank_level",
                "direction": "IN",
            },
            {
                "tag": "LT_RES",
                "entity": "sensor.res_level",
                "direction": "IN",
            },
        ],
    }
    stub = ThinIntegrationStub(config)
    image = stub.attach()
    stub.entities.set("sensor.tank_level", 0.30)
    stub.entities.set("sensor.res_level", 0.25)
    stub.scan_inputs(image)
    assert image.get_quality("LT_TANK").status is QualityStatus.GOOD
    assert image.get_quality("LT_RES").status is QualityStatus.GOOD

    stub.entities.set("sensor.tank_level", None)  # GOOD + None
    stub.entities.set("sensor.res_level", 0.28)
    stub.scan_inputs(image)
    assert image.get_value("LT_TANK") == pytest.approx(0.30)
    q = image.get_quality("LT_TANK")
    assert q.status is QualityStatus.BAD
    assert q.reason is ReasonCode.UNAVAILABLE
    # Peer binding still advanced (loop did not abort mid-scan)
    assert image.get_value("LT_RES") == pytest.approx(0.28)
    assert image.get_quality("LT_RES").status is QualityStatus.GOOD


@pytest.mark.parametrize(
    "raw,reason",
    [
        ("not-a-number", ReasonCode.UNAVAILABLE),
        (float("nan"), ReasonCode.FAULT),
        (float("inf"), ReasonCode.FAULT),
        (float("-inf"), ReasonCode.FAULT),
    ],
)
def test_apply_in_good_non_numeric_or_non_finite_demotes(raw, reason):
    table = _level_table()
    image = IoImage()
    table.declare_on(image)
    table.apply_in(image, {"sensor.tank_level": 0.15})
    table.apply_in(image, {"sensor.tank_level": raw})
    assert image.get_value("LT_TANK") == pytest.approx(0.15)
    q = image.get_quality("LT_TANK")
    assert q.status is QualityStatus.BAD
    assert q.reason is reason


def test_apply_in_missing_entity_is_bad_unavailable():
    table = _level_table(scale=0.01)
    image = IoImage()
    table.declare_on(image)
    table.apply_in(image, {"sensor.tank_level": 20.0})
    assert image.get_value("LT_TANK") == pytest.approx(0.20)

    # Missing key (not skip-retain): apply BAD + unavailable → keep last-good
    table.apply_in(image, {})
    assert image.get_value("LT_TANK") == pytest.approx(0.20)
    q = image.get_quality("LT_TANK")
    assert q.status is QualityStatus.BAD
    assert q.reason is ReasonCode.UNAVAILABLE


def test_apply_out_skips_never_written_tags():
    table = BindingTable(
        tags={
            "LT_TANK": TagDecl("LT_TANK", default=0.0),
            "CMD_SPEED": TagDecl("CMD_SPEED", default=0.0),
        },
        bindings=[
            Binding("LT_TANK", "sensor.tank_level", Direction.IN),
            Binding("CMD_SPEED", "number.cmd_speed", Direction.OUT),
        ],
    )
    image = IoImage()
    table.declare_on(image)
    # No set_output → nothing to flush (do not publish default as GOOD)
    assert table.apply_out(image) == {}

    image.set_output("CMD_SPEED", 33.0)
    assert table.apply_out(image) == {"number.cmd_speed": pytest.approx(33.0)}


def test_parse_sample_requires_reason_when_not_good():
    from plcassistant.io.binding import _parse_sample

    with pytest.raises(ValueError, match="requires a reason code"):
        _parse_sample((None, QualityStatus.BAD))
    with pytest.raises(ValueError, match="requires a reason code"):
        _parse_sample((1.0, QualityStatus.UNCERTAIN))
    value, status, reason = _parse_sample(
        (None, QualityStatus.BAD, ReasonCode.UNAVAILABLE)
    )
    assert value is None
    assert status is QualityStatus.BAD
    assert reason is ReasonCode.UNAVAILABLE
