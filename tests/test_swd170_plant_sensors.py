"""SWD-170: plant entity unique_id helpers + source wiring (no Home Assistant)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CC = ROOT / "custom_components" / "plcassistant"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_stable_unique_ids_are_instance_scoped() -> None:
    mod = _load("plcassistant_entity_cleanup", CC / "entity_cleanup.py")
    assert (
        mod.expected_plant_number_unique_id("default", "LT_TANK")
        == "plcassistant_default_LT_TANK_number"
    )
    assert (
        mod.expected_plant_sensor_unique_id("default", "FT_INLET")
        == "plcassistant_default_FT_INLET_plant_in"
    )
    assert mod.expected_plant_number_unique_id("a", "LT_RES") != (
        mod.expected_plant_number_unique_id("b", "LT_RES")
    )


def test_number_uses_stable_unique_id_helper() -> None:
    number = (CC / "number.py").read_text(encoding="utf-8")
    assert "expected_plant_number_unique_id" in number
    assert 'f"{entry_id}_{tag}_req"' not in number
    assert "in_values" in number


def test_simulator_caches_in_values_before_bus() -> None:
    sim = (CC / "dynamics" / "simulator.py").read_text(encoding="utf-8")
    assert 'store.setdefault("in_values"' in sim
    assert f"{'{'}DOMAIN{'}'}_plant_in" in sim or "_plant_in" in sim
    cache_at = sim.index('store.setdefault("in_values"')
    fire_at = sim.index("async_fire")
    assert cache_at < fire_at
