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
        "config_flow.py",
        "services.yaml",
        "strings.json",
        "number.py",
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
        "DEFAULT_MQTT_BROKER",
        "SERVICE_START",
        "SERVICE_STOP",
        "SERVICE_RESET",
    ):
        assert key in const_text

    init_text = (CC / "__init__.py").read_text(encoding="utf-8")
    assert "tag_in_topic" in init_text
    assert "tag_out_topic" in init_text
    assert "Platform.NUMBER" in init_text
    # hass.components was removed in modern HA Core; subscribe via mqtt helper.
    assert "hass.components" not in init_text
    assert "from homeassistant.components.mqtt import async_subscribe" in init_text
    assert "await async_subscribe(" in init_text


def test_platforms_publish_and_subscribe_paths():
    number = (CC / "number.py").read_text(encoding="utf-8")
    assert "tag_in_topic" in number
    assert "async_set_native_value" in number
    assert "_tag_out" in number
    assert "PlcAssistantMockInNumber" in number
    assert "PlcAssistantMockOutNumber" in number

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

    install = (ROOT / "ha_app" / "INSTALL.md").read_text(encoding="utf-8")
    assert "custom_components/plcassistant" in install or "README.md" in install
    assert "README.md" in install
