"""Bundled thin integration layout (SWD-126 / A4)."""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CC = ROOT / "custom_components" / "plcassistant"


def test_integration_required_files():
    for name in (
        "manifest.json",
        "__init__.py",
        "const.py",
        "mqtt_topics.py",
        "ha_config_bridge.py",
        "config_flow.py",
        "services.yaml",
        "strings.json",
        "number.py",
        "button.py",
        "README.md",
    ):
        assert (CC / name).is_file(), name


def test_manifest_mqtt_dependency_and_config_keys():
    manifest = json.loads((CC / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == "plcassistant"
    assert manifest["config_flow"] is True
    assert "mqtt" in manifest.get("dependencies", [])

    const_text = (CC / "const.py").read_text(encoding="utf-8")
    for key in (
        "CONF_INSTANCE_ID",
        "CONF_MQTT_BROKER",
        "CONF_MQTT_PORT",
        "CONF_BINDINGS",
        "CONF_MOCK_MODE",
        "CONF_DYNAMICS_PRESET",
        "CONF_DYNAMICS_PARAMS",
        "DEFAULT_MQTT_BROKER",
        "SERVICE_START",
        "SERVICE_STOP",
        "SERVICE_RESET",
        "SERVICE_SET_DYNAMICS_PRESET",
    ):
        assert key in const_text

    init_text = (CC / "__init__.py").read_text(encoding="utf-8")
    assert "tag_in_topic" in init_text
    assert "tag_out_topic" in init_text
    assert "Platform.NUMBER" in init_text
    assert "Platform.BUTTON" in init_text
    assert "FT_INLET" in init_text
    assert "HassPlantSimulator" in init_text
    assert "plant_simulator" in init_text
    assert "resolve_dynamics_options" in init_text
    assert "set_dynamics_preset" in init_text
    # hass.components was removed in modern HA Core; subscribe via mqtt helper.
    assert "hass.components" not in init_text
    assert "from homeassistant.components.mqtt import async_subscribe" in init_text
    assert "await async_subscribe(" in init_text


def test_app_and_integration_versions_match():
    """App config.yaml version must equal thin-integration manifest version."""
    import yaml

    root = pathlib.Path(__file__).resolve().parents[1]
    app_ver = yaml.safe_load(
        (root / "plc_assistant" / "config.yaml").read_text(encoding="utf-8")
    )["version"]
    man = json.loads((CC / "manifest.json").read_text(encoding="utf-8"))
    assert man["version"] == app_ver
    bundled = json.loads(
        (
            root
            / "plc_assistant"
            / "custom_components"
            / "plcassistant"
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert bundled["version"] == app_ver
    dockerfile = (root / "plc_assistant" / "Dockerfile").read_text(encoding="utf-8")
    assert f"ARG BUILD_VERSION={app_ver}" in dockerfile


def test_platforms_publish_and_subscribe_paths():
    number = (CC / "number.py").read_text(encoding="utf-8")
    assert "tag_in_topic" in number
    assert "async_set_native_value" in number
    assert "PlcAssistantRequestNumber" in number
    assert "SP_LEVEL_REQ" in number
    assert "_simulator_owns" in number
    assert "set_tag" in number

    sensor = (CC / "sensor.py").read_text(encoding="utf-8")
    assert "_tag_out" in sensor
    assert "PlcAssistantOutSensor" in sensor

    button = (CC / "button.py").read_text(encoding="utf-8")
    assert "DOMAIN" in button
    assert "async_press" in button
    assert "PlcAssistantCmdButton" in button
    for svc in ("SERVICE_START", "SERVICE_STOP", "SERVICE_RESET"):
        assert svc in button

    lovelace = (CC / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "number.plcassistant_sp_level_req" in lovelace
    assert "button.plcassistant_start" in lovelace
    assert "number.plcassistant_lt_tank_in" in lovelace
    assert "sensor.plcassistant_status" in lovelace
    assert "sensor.plcassistant_mode" in lovelace
    assert "live simulator" in lovelace.lower() or "0.1.25" in lovelace or "dynamics" in lovelace.lower()
    assert "sensor.plcassistant_dynamics_preset" in lovelace
    assert "path: dynamics" in lovelace
    assert "set_dynamics_preset:" in (CC / "services.yaml").read_text(encoding="utf-8")
    assert "PlcAssistantOptionsFlow" in (CC / "config_flow.py").read_text(encoding="utf-8")
    assert (CC / "www" / "dynamics_editor.html").is_file()
    assert 'entity_id = f"number.' in number or "suggested_object_id" in number
    assert "plcassistant_sp_level_req" in number
    assert "plcassistant_lt_tank_in" in number
    assert "PlcAssistantStatusSensor" in sensor
    assert "status_topic" in (CC / "__init__.py").read_text(encoding="utf-8")
    # SWD-136: cache retained status + hydrate sensors on add.
    init_text = (CC / "__init__.py").read_text(encoding="utf-8")
    assert 'store["status_payload"]' in init_text or 'store["status_payload"] = text' in init_text
    assert "status_payload" in init_text
    assert "status_payload" in sensor
    assert "_apply_status_payload" in sensor
    assert 'store.get("out_values")' in sensor or "out_values" in sensor
    topics = (CC / "mqtt_topics.py").read_text(encoding="utf-8")
    assert "parse_app_status_payload" in topics


def test_services_yaml_has_operator_actions():
    text = (CC / "services.yaml").read_text(encoding="utf-8")
    assert "start:" in text
    assert "stop:" in text
    assert "reset:" in text


def test_bundle_docs_mention_auto_install():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "custom_components/plcassistant" in readme
    assert "auto-installed" in readme.lower() or "copies" in readme.lower()
    assert "Restart Home Assistant Core" in readme
    assert "Another job is running" in readme or "job group" in readme
    assert "hass.components" in readme or "builder prune" in readme

    install = (ROOT / "ha_app" / "INSTALL.md").read_text(encoding="utf-8")
    assert "custom_components/plcassistant" in install or "README.md" in install
    assert "README.md" in install
