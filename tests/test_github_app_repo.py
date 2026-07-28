"""GitHub App repository metadata (SWD-127 / A5)."""

from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_repository_yaml_at_repo_root():
    path = ROOT / "repository.yaml"
    assert path.is_file()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "name" in data
    assert "url" in data
    assert "github.com" in data["url"]


def test_app_folder_is_direct_child():
    """HA discovers Apps as direct children of the repository root."""
    app = ROOT / "plc_assistant"
    assert (app / "config.yaml").is_file()
    assert (app / "Dockerfile").is_file()
    assert (app / "run.sh").is_file()
    data = yaml.safe_load((app / "config.yaml").read_text(encoding="utf-8"))
    assert data["slug"] == "plcassistant"
    assert data["ingress"] is True


def test_install_docs_exist():
    """Canonical install guide is the root README; INSTALL.md points there."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Mosquitto" in readme
    assert "plc_assistant" in readme
    assert "8099" in readme
    assert "no App-side auth" in readme or "LAN-trust" in readme
    assert "custom_components/plcassistant" in readme
    assert "https://github.com/marcuskrogh/PLCAssistant" in readme

    install = ROOT / "ha_app" / "INSTALL.md"
    assert install.is_file()
    pointer = install.read_text(encoding="utf-8")
    assert "README.md" in pointer
    assert "Mosquitto" in pointer or "8099" in pointer
