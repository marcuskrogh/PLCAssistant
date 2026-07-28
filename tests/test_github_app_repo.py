"""GitHub App repository metadata (SWD-127 / A5)."""

from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Supervisor recursively discovers Apps via these filenames:
# https://developers.home-assistant.io/docs/apps/configuration/
_APP_CONFIG_NAMES = frozenset({"config.yaml", "config.yml", "config.json"})
_IGNORE_PARTS = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__", ".eggs", "dist", "build"})


def _iter_app_config_files() -> list[pathlib.Path]:
    found: list[pathlib.Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.name not in _APP_CONFIG_NAMES:
            continue
        if any(part in _IGNORE_PARTS for part in path.parts):
            continue
        found.append(path)
    return sorted(found)


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


def test_exactly_one_supervisor_app_config():
    """Exactly one Supervisor App config — duplicates break update detection forever."""
    configs = _iter_app_config_files()
    assert configs == [ROOT / "plc_assistant" / "config.yaml"], (
        "Supervisor recursively loads every config.yaml|yml|json. "
        f"Found: {[str(p.relative_to(ROOT)) for p in configs]}. "
        "Keep only plc_assistant/config.yaml."
    )
    data = yaml.safe_load(configs[0].read_text(encoding="utf-8"))
    assert data["slug"] == "plcassistant"
    assert isinstance(data.get("version"), str) and data["version"].strip()


def test_no_duplicate_app_slugs_even_if_extra_configs_appear():
    """Slug uniqueness is the invariant Supervisor needs for store updates."""
    slugs: list[str] = []
    for path in _iter_app_config_files():
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "slug" not in data:
            continue
        slugs.append(str(data["slug"]))
    assert slugs == ["plcassistant"], slugs


def test_ha_app_is_docs_only_not_a_second_app():
    """ha_app/ may hold install pointers, never a discoverable App config."""
    ha_app = ROOT / "ha_app"
    assert ha_app.is_dir()
    assert (ha_app / "INSTALL.md").is_file()
    leaked = [
        p
        for p in ha_app.rglob("*")
        if p.is_file() and p.name in _APP_CONFIG_NAMES
    ]
    assert not leaked, f"ha_app must not contain App configs: {leaked}"


def test_install_docs_exist():
    """Canonical install guide is the root README; INSTALL.md points there."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Mosquitto" in readme
    assert "plc_assistant" in readme
    assert "8099" in readme
    assert "no App-side auth" in readme or "LAN-trust" in readme
    assert "custom_components/plcassistant" in readme
    assert "https://github.com/marcuskrogh/PLCAssistant" in readme
    assert "Check for updates" in readme
    assert "plc_assistant/config.yaml" in readme

    install = ROOT / "ha_app" / "INSTALL.md"
    assert install.is_file()
    pointer = install.read_text(encoding="utf-8")
    assert "README.md" in pointer
    assert "Mosquitto" in pointer or "8099" in pointer
