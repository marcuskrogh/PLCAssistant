"""SWD-170: plant entity unique_id helpers + source wiring (no Home Assistant)."""

from __future__ import annotations

import importlib.util
import re
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


def test_purge_only_when_unavailable() -> None:
    mod = _load("plcassistant_entity_cleanup_purge", CC / "entity_cleanup.py")
    # Missing/unavailable → purge (even if unique_id already matches).
    assert mod.should_purge_plant_number(
        state_unavailable=True,
        unique_id="stale",
        expected_unique_id="plcassistant_default_LT_TANK_number",
    )
    assert mod.should_purge_plant_number(
        state_unavailable=True,
        unique_id="plcassistant_default_LT_TANK_number",
        expected_unique_id="plcassistant_default_LT_TANK_number",
    )
    # Live available entity must not be deleted for unique_id mismatch alone.
    assert not mod.should_purge_plant_number(
        state_unavailable=False,
        unique_id="stale",
        expected_unique_id="plcassistant_default_LT_TANK_number",
    )


def test_number_uses_stable_unique_id_helper() -> None:
    number = (CC / "number.py").read_text(encoding="utf-8")
    assert "expected_plant_number_unique_id" in number
    assert 'f"{entry_id}_{tag}_req"' in number
    assert "in_values" in number
    # Request SP must not reuse plant `_number` unique_id suffix.
    assert 'plcassistant_{instance_id}_{tag}_number"' not in number


def test_plant_sensor_object_ids_match_lovelace() -> None:
    sensor = (CC / "sensor.py").read_text(encoding="utf-8")
    for object_id in (
        "plcassistant_lt_tank_in",
        "plcassistant_lt_res_in",
        "plcassistant_ft_inlet_in",
    ):
        assert f'"{object_id}"' in sensor
    lovelace = (CC / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    for entity in (
        "sensor.plcassistant_lt_tank_in",
        "sensor.plcassistant_lt_res_in",
        "sensor.plcassistant_ft_inlet_in",
    ):
        assert f"entity: {entity}" in lovelace
    # History graph uses the same plant IN sensor IDs.
    hist = lovelace.split("type: history-graph", 1)[1]
    assert "sensor.plcassistant_lt_tank_in" in hist
    assert "sensor.plcassistant_lt_res_in" in hist
    assert "sensor.plcassistant_ft_inlet_in" in hist


def test_simulator_caches_in_values_before_bus() -> None:
    sim = (CC / "dynamics" / "simulator.py").read_text(encoding="utf-8")
    assert 'store.setdefault("in_values"' in sim
    assert "_plant_in" in sim
    cache_at = sim.index('store.setdefault("in_values"')
    fire_at = sim.index("async_fire")
    assert cache_at < fire_at


def test_run_sh_refreshes_dashboard_versions_through_14() -> None:
    run = (ROOT / "plc_assistant" / "run.sh").read_text(encoding="utf-8")
    assert re.search(
        r"plcassistant_dashboard_version:\[\[:space:\]\]\*\(\[1-9\]\|1\[0-4\]\)",
        run,
    )
    assert "1[0-3]" not in run or "1[0-4]" in run
