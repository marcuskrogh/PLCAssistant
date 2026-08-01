"""SWD-143: dynamics options resolution + preset/param wiring (HA-free)."""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CC = ROOT / "custom_components" / "plcassistant"

if str(CC) not in sys.path:
    sys.path.insert(0, str(CC))


def test_resolve_dynamics_options_defaults() -> None:
    from dynamics.options import resolve_dynamics_options

    preset, params = resolve_dynamics_options({})
    assert preset == "skid"
    assert params == {}
    preset, params = resolve_dynamics_options(None)
    assert preset == "skid"
    assert params == {}


def test_resolve_dynamics_options_json_and_mapping() -> None:
    from dynamics.options import resolve_dynamics_options

    preset, params = resolve_dynamics_options(
        {"dynamics_preset": "Skid_Composed", "dynamics_params": '{"k_drain": 6}'}
    )
    assert preset == "skid_composed"
    assert params == {"k_drain": 6.0}

    preset, params = resolve_dynamics_options(
        {"dynamics_preset": "skid", "dynamics_params": {"a_tank": 0.07}}
    )
    assert preset == "skid"
    assert params["a_tank"] == pytest.approx(0.07)


def test_parse_dynamics_params_rejects_bad_json() -> None:
    from dynamics.options import parse_dynamics_params

    with pytest.raises(ValueError):
        parse_dynamics_params("{not-json")
    with pytest.raises(ValueError):
        parse_dynamics_params("[1,2]")
    with pytest.raises(ValueError):
        parse_dynamics_params({"k": "nope"})


def test_validate_preset_known_and_unknown() -> None:
    from dynamics.options import validate_preset

    assert validate_preset("skid") == "skid"
    assert validate_preset("skid_composed") == "skid_composed"
    with pytest.raises(KeyError):
        validate_preset("not_a_real_preset")


def test_for_preset_applies_param_overrides() -> None:
    from dynamics.plant import PlantSimulator

    published: dict[str, str] = {}

    def publish(tag: str, payload: str) -> None:
        published[tag] = payload

    plant = PlantSimulator.for_preset(
        publish, preset="skid", params={"k_drain": 9.0, "a_tank": 0.08}
    )
    assert plant.model.params["k_drain"] == pytest.approx(9.0)
    assert plant.model.params["a_tank"] == pytest.approx(0.08)

    composed = PlantSimulator.for_preset(publish, preset="skid_composed")
    assert "skid" in composed.model.spec.name


def test_options_flow_and_service_surface_in_integration_sources() -> None:
    """CI has no homeassistant — assert packaging contracts via source scan."""
    flow = (CC / "config_flow.py").read_text(encoding="utf-8")
    assert "PlcAssistantOptionsFlow" in flow
    assert "async_get_options_flow" in flow
    assert "CONF_DYNAMICS_PRESET" in flow
    assert "validate_preset" in flow

    init = (CC / "__init__.py").read_text(encoding="utf-8")
    assert "SERVICE_SET_DYNAMICS_PRESET" in init
    assert "set_dynamics_preset" in init
    assert "resolve_dynamics_options" in init
    assert "add_update_listener" in init
    assert "HassPlantSimulator" in init
    assert "preset=preset" in init
    # Service must register independently of start/stop/reset (upgrade path).
    assert "SERVICE_SET_DYNAMICS_PRESET" in init
    assert init.count("has_service(DOMAIN, SERVICE_") >= 2

    services = (CC / "services.yaml").read_text(encoding="utf-8")
    assert "set_dynamics_preset:" in services

    strings = (CC / "strings.json").read_text(encoding="utf-8")
    assert '"options"' in strings
    assert "invalid_dynamics" in strings

    sensor = (CC / "sensor.py").read_text(encoding="utf-8")
    assert "PlcAssistantDynamicsPresetSensor" in sensor
    assert "plcassistant_dynamics_preset" in sensor

    const = (CC / "const.py").read_text(encoding="utf-8")
    assert "CONF_DYNAMICS_PRESET" in const
    assert "CONF_DYNAMICS_PARAMS" in const

    # HA-free options helper must not import homeassistant.
    options = (CC / "dynamics" / "options.py").read_text(encoding="utf-8")
    assert "homeassistant" not in options


def test_lovelace_documents_preset_chooser() -> None:
    text = (CC / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 21" in text
    assert "sensor.plcassistant_dynamics_preset" in text
    assert "path: dynamics" in text
    assert "/api/plcassistant/dynamics/ui" in text
