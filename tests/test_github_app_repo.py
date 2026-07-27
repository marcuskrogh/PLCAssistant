"""GitHub App repository metadata (SWD-127 / A5)."""

from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
HA = ROOT / "ha_app"


def test_repository_yaml_exists():
    path = HA / "repository.yaml"
    assert path.is_file()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "name" in data
    assert "url" in data
    assert "github.com" in data["url"]


def test_install_docs_exist():
    install = HA / "INSTALL.md"
    assert install.is_file()
    text = install.read_text(encoding="utf-8")
    assert "Mosquitto" in text
    assert "Ingress" in text or "ingress" in text
    assert "8099" in text
