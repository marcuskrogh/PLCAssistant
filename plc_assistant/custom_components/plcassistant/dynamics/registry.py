"""Preset registry for code and composed dynamics models (SWD-144)."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .compile import SpecModel, document_to_model, load_model_document
from .core import DynamicsModel
from .skid import PRESETS, SkidModel

_MODELS_DIR = Path(__file__).resolve().parent / "models"


def get_preset(
    name: str = "skid", params: Mapping[str, float] | None = None
) -> DynamicsModel:
    key = str(name or "skid").strip().lower() or "skid"
    if key in PRESETS:
        return PRESETS[key](params=params)
    # Composed / document presets (JSON preferred; YAML when PyYAML present).
    for suffix in (".json", ".yaml", ".yml"):
        path = _MODELS_DIR / f"{key}{suffix}"
        if path.is_file():
            doc = load_model_document(path)
            return document_to_model(doc, params=params)
    raise KeyError(f"unknown dynamics preset: {name!r}")


def list_presets() -> tuple[str, ...]:
    names = set(PRESETS)
    if _MODELS_DIR.is_dir():
        for path in _MODELS_DIR.iterdir():
            if path.suffix.lower() in {".json", ".yaml", ".yml"}:
                names.add(path.stem.lower())
    return tuple(sorted(names))


__all__ = ["SpecModel", "SkidModel", "get_preset", "list_presets"]
