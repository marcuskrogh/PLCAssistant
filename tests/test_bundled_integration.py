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
        "README.md",
    ):
        assert (CC / name).is_file(), name


def test_manifest_and_mqtt_config_keys():
    manifest = json.loads((CC / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == "plcassistant"
    assert manifest["config_flow"] is True

    const_text = (CC / "const.py").read_text(encoding="utf-8")
    for key in (
        "CONF_INSTANCE_ID",
        "CONF_MQTT_BROKER",
        "CONF_MQTT_PORT",
        "DEFAULT_MQTT_BROKER",
        "SERVICE_START",
        "SERVICE_STOP",
        "SERVICE_RESET",
    ):
        assert key in const_text

    topics = (CC / "mqtt_topics.py").read_text(encoding="utf-8")
    assert "tag/{tag}/in" in topics.replace("{}", "") or "tag/" in topics
    assert "/in" in topics and "/out" in topics


def test_services_yaml_has_operator_actions():
    text = (CC / "services.yaml").read_text(encoding="utf-8")
    assert "start:" in text
    assert "stop:" in text
    assert "reset:" in text


def test_bundle_docs_mention_copy_install():
    install = (ROOT / "ha_app" / "INSTALL.md").read_text(encoding="utf-8")
    assert "custom_components/plcassistant" in install
    assert "one-time copy" in install.lower() or "copy" in install.lower()
