"""SWD-86 PLAN acceptance checklist — contract/unit tests with mocked HA (SWD-100).

Each test is named after a PLAN acceptance bullet. Uses ThinIntegrationStub +
IoImage + MockEntityStore; skid gravity tags as example config. No real HA.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from plcassistant.io import (
    IoImage,
    MockEntityStore,
    QualityStatus,
    ReasonCode,
    ThinIntegrationStub,
)

# Gravity-skid tags (docs/wedge/02-io-hmi-contract.md / packaging sketch).
SKID_CONFIG = {
    "tags": {
        "LT_TANK": {"default": 0.15, "unit": "m"},
        "LT_RES": {"default": 0.20, "unit": "m"},
        "FT_INLET": {"default": 0.0, "unit": "L/min"},
        "CMD_SPEED": {"default": 0.0, "unit": "pct"},
        "SP_LEVEL_REQ": {"default": 0.15, "unit": "m"},
        "SP_LEVEL": {"default": 0.15, "unit": "m"},
    },
    "bindings": [
        {
            "tag": "LT_TANK",
            "entity": "sensor.mock_tank_level",
            "direction": "IN",
            "scale": 0.01,
            "offset": 0.0,
            "entity_unit": "pct",
        },
        {
            "tag": "LT_RES",
            "entity": "sensor.mock_res_level",
            "direction": "IN",
        },
        {
            "tag": "FT_INLET",
            "entity": "sensor.mock_inlet_flow",
            "direction": "IN",
        },
        {
            "tag": "CMD_SPEED",
            "entity": "number.mock_pump_speed",
            "direction": "OUT",
        },
        {
            "tag": "SP_LEVEL_REQ",
            "entity": "input_number.tank_sp",
            "direction": "IN",
        },
        {
            "tag": "SP_LEVEL",
            "entity": "sensor.tank_sp_active",
            "direction": "OUT",
        },
    ],
}


def _seed_good_pvs(stub: ThinIntegrationStub) -> None:
    stub.entities.set("sensor.mock_tank_level", 22.0)  # → 0.22 m
    stub.entities.set("sensor.mock_res_level", 0.25)
    stub.entities.set("sensor.mock_inlet_flow", 1.5)
    stub.entities.set("input_number.tank_sp", 0.20)


# --- 1. Sync refresh: IN at start, OUT at end every scan ---------------------


def test_sync_refresh_in_at_start_out_at_end_every_scan():
    """Acceptance: IN at scan start, OUT at scan end, every scan."""
    stub = ThinIntegrationStub(SKID_CONFIG)
    image = stub.attach()
    _seed_good_pvs(stub)

    order: list[str] = []

    def logic(img: IoImage) -> None:
        order.append("logic")
        assert img.get_value("LT_TANK") == pytest.approx(0.22)
        assert img.get_quality("LT_TANK").status is QualityStatus.GOOD
        # OUT not flushed until scan end
        assert not stub.entities.has("number.mock_pump_speed")
        img.set_output("CMD_SPEED", 35.0)
        img.set_output("SP_LEVEL", img.get_value("SP_LEVEL_REQ"))

    # Wrap to observe boundary order
    orig_in, orig_out = stub.scan_inputs, stub.scan_outputs

    def traced_in(img: IoImage) -> None:
        order.append("in")
        orig_in(img)

    def traced_out(img: IoImage) -> dict[str, float]:
        order.append("out")
        return orig_out(img)

    stub.scan_inputs = traced_in  # type: ignore[method-assign]
    stub.scan_outputs = traced_out  # type: ignore[method-assign]

    flush1 = stub.run_scan(image, logic)
    assert order == ["in", "logic", "out"]
    assert flush1["number.mock_pump_speed"] == pytest.approx(35.0)
    assert stub.entities.get("number.mock_pump_speed").value == pytest.approx(35.0)

    # Every scan: OUT flushed again (no change-detect)
    order.clear()

    def logic2(img: IoImage) -> None:
        order.append("logic")
        img.set_output("CMD_SPEED", 40.0)
        img.set_output("SP_LEVEL", 0.20)

    flush2 = stub.run_scan(image, logic2)
    assert order == ["in", "logic", "out"]
    assert flush2["number.mock_pump_speed"] == pytest.approx(40.0)


# --- 2. Quality transitions GOOD / UNCERTAIN / BAD + reasons -----------------


def test_quality_transitions_good_uncertain_bad_with_reasons():
    """Acceptance: quality transitions GOOD / UNCERTAIN / BAD + reasons."""
    stub = ThinIntegrationStub(SKID_CONFIG)
    image = stub.attach()
    _seed_good_pvs(stub)

    stub.scan_inputs(image)
    assert image.get_quality("LT_TANK").status is QualityStatus.GOOD
    assert image.get_quality("LT_TANK").reason is None

    stub.entities.set(
        "sensor.mock_tank_level",
        22.0,
        QualityStatus.UNCERTAIN,
        ReasonCode.STALE,
    )
    stub.scan_inputs(image)
    q = image.get_quality("LT_TANK")
    assert q.status is QualityStatus.UNCERTAIN
    assert q.reason is ReasonCode.STALE

    stub.entities.set(
        "sensor.mock_tank_level",
        22.0,
        QualityStatus.BAD,
        ReasonCode.FAULT,
    )
    stub.scan_inputs(image)
    q = image.get_quality("LT_TANK")
    assert q.status is QualityStatus.BAD
    assert q.reason is ReasonCode.FAULT

    stub.entities.set(
        "sensor.mock_tank_level",
        25.0,
        QualityStatus.BAD,
        ReasonCode.UNKNOWN,
    )
    stub.scan_inputs(image)
    assert image.get_quality("LT_TANK").reason is ReasonCode.UNKNOWN

    stub.entities.set("sensor.mock_tank_level", 30.0)  # GOOD again
    stub.scan_inputs(image)
    assert image.get_quality("LT_TANK").status is QualityStatus.GOOD
    assert image.get_value("LT_TANK") == pytest.approx(0.30)


# --- 3. Last-good retention --------------------------------------------------


def test_last_good_retention_when_quality_not_good():
    """Acceptance: last-good retained when quality ≠ GOOD."""
    stub = ThinIntegrationStub(SKID_CONFIG)
    image = stub.attach()
    _seed_good_pvs(stub)

    stub.scan_inputs(image)
    assert image.get_value("LT_TANK") == pytest.approx(0.22)
    assert image.snapshot()["LT_TANK"].last_good == pytest.approx(0.22)

    stub.entities.set(
        "sensor.mock_tank_level",
        99.0,
        QualityStatus.BAD,
        ReasonCode.FAULT,
    )
    stub.scan_inputs(image)
    assert image.get_value("LT_TANK") == pytest.approx(0.22)
    assert image.get_quality("LT_TANK").status is QualityStatus.BAD
    assert image.snapshot()["LT_TANK"].last_good == pytest.approx(0.22)

    stub.entities.set(
        "sensor.mock_tank_level",
        88.0,
        QualityStatus.UNCERTAIN,
        ReasonCode.STALE,
    )
    stub.scan_inputs(image)
    assert image.get_value("LT_TANK") == pytest.approx(0.22)
    assert image.get_quality("LT_TANK").status is QualityStatus.UNCERTAIN


# --- 4. Defaults before first GOOD -------------------------------------------


def test_defaults_before_first_good_bad_unavailable():
    """Acceptance: before first GOOD → BAD/unavailable + configured default."""
    stub = ThinIntegrationStub(SKID_CONFIG)
    image = stub.attach()

    # No entities seeded — missing → BAD / unavailable
    stub.scan_inputs(image)
    assert image.get_value("LT_TANK") == pytest.approx(0.15)
    q = image.get_quality("LT_TANK")
    assert q.status is QualityStatus.BAD
    assert q.reason is ReasonCode.UNAVAILABLE
    assert image.snapshot()["LT_TANK"].last_good is None

    assert image.get_value("LT_RES") == pytest.approx(0.20)
    assert image.get_quality("LT_RES").reason is ReasonCode.UNAVAILABLE
    assert image.get_value("FT_INLET") == pytest.approx(0.0)
    assert image.get_value("SP_LEVEL_REQ") == pytest.approx(0.15)


# --- 5. Direction enforcement ------------------------------------------------


def test_direction_enforcement_in_reads_out_writes_only():
    """Acceptance: IN feeds image; OUT does not read; OUT flushes writers only."""
    stub = ThinIntegrationStub(SKID_CONFIG)
    image = stub.attach()
    _seed_good_pvs(stub)
    # Poison OUT entity — must not become an input sample
    stub.entities.set("number.mock_pump_speed", 99.0)
    stub.entities.set("sensor.tank_sp_active", 77.0)

    stub.scan_inputs(image)
    assert image.get_value("LT_TANK") == pytest.approx(0.22)
    # CMD_SPEED / SP_LEVEL never received apply_input → still initial BAD/default
    assert image.get_value("CMD_SPEED") == pytest.approx(0.0)
    assert image.get_quality("CMD_SPEED").status is QualityStatus.BAD
    assert image.get_value("SP_LEVEL") == pytest.approx(0.15)
    assert image.get_quality("SP_LEVEL").status is QualityStatus.BAD

    image.set_output("CMD_SPEED", 42.0)
    image.set_output("SP_LEVEL", 0.18)
    flush = stub.scan_outputs(image)
    assert set(flush) == {"number.mock_pump_speed", "sensor.tank_sp_active"}
    assert "sensor.mock_tank_level" not in flush
    assert flush["number.mock_pump_speed"] == pytest.approx(42.0)
    assert flush["sensor.tank_sp_active"] == pytest.approx(0.18)


# --- 6. Multi-IN OK / single-OUT writer rejected -----------------------------


def test_multi_in_ok_single_out_writer_rejected():
    """Acceptance: many tags may read one entity; at most one OUT writer."""
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


# --- 7. Unit conversion scale / offset ----------------------------------------


def test_unit_conversion_scale_offset():
    """Acceptance: binding layer applies eng = raw*scale + offset (and inverse OUT)."""
    stub = ThinIntegrationStub(SKID_CONFIG)
    image = stub.attach()
    # LT_TANK: scale 0.01 → raw 25 → 0.25 m
    stub.entities.set("sensor.mock_tank_level", 25.0)
    stub.entities.set("sensor.mock_res_level", 0.20)
    stub.entities.set("sensor.mock_inlet_flow", 0.0)
    stub.entities.set("input_number.tank_sp", 0.15)

    stub.scan_inputs(image)
    assert image.get_value("LT_TANK") == pytest.approx(0.25)

    # Dedicated OUT scale/offset via a small config (skid OUTs are identity)
    conv = ThinIntegrationStub(
        {
            "tags": {"CMD_VALVE": {"default": 0.0, "unit": "pct"}},
            "bindings": [
                {
                    "tag": "CMD_VALVE",
                    "entity": "number.valve_raw",
                    "direction": "OUT",
                    "scale": 10.0,
                    "offset": -5.0,
                }
            ],
        }
    )
    out_image = conv.attach()
    out_image.set_output("CMD_VALVE", 45.0)
    # raw = (45 - (-5)) / 10 = 5.0
    flush = conv.scan_outputs(out_image)
    assert flush == {"number.valve_raw": pytest.approx(5.0)}
    assert conv.entities.get("number.valve_raw").value == pytest.approx(5.0)


# --- 8. Mock path ≡ field path into Add-on image -----------------------------


def test_mock_path_equiv_field_path_same_stub_api():
    """Acceptance: mock and field use the same stub API into the Add-on image."""
    mock_store = MockEntityStore()
    field_store = MockEntityStore()
    mock_stub = ThinIntegrationStub(SKID_CONFIG, entities=mock_store)
    field_stub = ThinIntegrationStub(SKID_CONFIG, entities=field_store)
    image_mock = mock_stub.attach(IoImage())
    image_field = field_stub.attach(IoImage())

    mock_store.set("sensor.mock_tank_level", 20.0)  # → 0.20 m
    mock_store.set("sensor.mock_res_level", 0.22)
    mock_store.set("sensor.mock_inlet_flow", 1.0)
    mock_store.set("input_number.tank_sp", 0.18)

    field_store.set("sensor.mock_tank_level", 35.0)  # → 0.35 m
    field_store.set("sensor.mock_res_level", 0.28)
    field_store.set("sensor.mock_inlet_flow", 2.0)
    field_store.set("input_number.tank_sp", 0.22)

    def logic_mock(img: IoImage) -> None:
        img.set_output("CMD_SPEED", 10.0)
        img.set_output("SP_LEVEL", img.get_value("SP_LEVEL_REQ"))

    def logic_field(img: IoImage) -> None:
        img.set_output("CMD_SPEED", 20.0)
        img.set_output("SP_LEVEL", img.get_value("SP_LEVEL_REQ"))

    mock_stub.run_scan(image_mock, logic_mock)
    field_stub.run_scan(image_field, logic_field)

    assert image_mock.get_value("LT_TANK") == pytest.approx(0.20)
    assert image_field.get_value("LT_TANK") == pytest.approx(0.35)
    assert mock_store.get("number.mock_pump_speed").value == pytest.approx(10.0)
    assert field_store.get("number.mock_pump_speed").value == pytest.approx(20.0)
    # Same API surface: both stubs expose scan_inputs / scan_outputs / run_scan
    assert callable(mock_stub.scan_inputs) and callable(field_stub.scan_inputs)
    assert callable(mock_stub.scan_outputs) and callable(field_stub.scan_outputs)


# --- 9. No real HA imports ---------------------------------------------------


def test_no_homeassistant_imports_in_production_or_tests():
    """Acceptance: no ``homeassistant`` imports in plcassistant/ or tests/."""
    root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []
    for base in (root / "plcassistant", root / "tests"):
        for path in base.rglob("*.py"):
            if path.name.startswith(".") or "__pycache__" in path.parts:
                continue
            source = path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(path))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "homeassistant" or alias.name.startswith(
                            "homeassistant."
                        ):
                            offenders.append(f"{path.relative_to(root)}:{node.lineno}")
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if mod == "homeassistant" or mod.startswith("homeassistant."):
                        offenders.append(f"{path.relative_to(root)}:{node.lineno}")
    assert offenders == [], f"forbidden homeassistant imports: {offenders}"
