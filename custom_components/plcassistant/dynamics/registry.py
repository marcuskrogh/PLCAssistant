"""Preset registry for code and composed dynamics models (SWD-144 / SWD-166)."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .compile import SpecModel, document_to_model, load_model_document
from .core import DynamicsModel
from .skid import PRESETS, SkidModel

_MODELS_DIR = Path(__file__).resolve().parent / "models"
_EXTRA_MODEL_DIRS: list[Path] = []


def add_model_dir(path: Path | str) -> None:
    """Register an extra directory for user model documents (e.g. HA config)."""
    resolved = Path(path).resolve()
    if resolved not in _EXTRA_MODEL_DIRS:
        _EXTRA_MODEL_DIRS.append(resolved)


def clear_extra_model_dirs() -> None:
    """Test helper — reset extra model search paths."""
    _EXTRA_MODEL_DIRS.clear()


def _iter_model_dirs() -> list[Path]:
    # User dirs first so operators can override bundled documents by name.
    dirs: list[Path] = []
    for path in _EXTRA_MODEL_DIRS:
        if path.is_dir() and path not in dirs:
            dirs.append(path)
    if _MODELS_DIR.is_dir() and _MODELS_DIR not in dirs:
        dirs.append(_MODELS_DIR)
    return dirs


def get_preset(
    name: str = "skid", params: Mapping[str, float] | None = None
) -> DynamicsModel:
    key = str(name or "skid").strip().lower() or "skid"
    if key in PRESETS:
        return PRESETS[key](params=params)
    for base in _iter_model_dirs():
        for suffix in (".json", ".yaml", ".yml"):
            path = base / f"{key}{suffix}"
            if path.is_file():
                doc = load_model_document(path)
                return document_to_model(doc, params=params)
    raise KeyError(f"unknown dynamics preset: {name!r}")


def list_presets() -> tuple[str, ...]:
    names = set(PRESETS)
    for base in _iter_model_dirs():
        for path in base.iterdir():
            if path.suffix.lower() in {".json", ".yaml", ".yml"}:
                names.add(path.stem.lower())
    return tuple(sorted(names))


__all__ = [
    "SpecModel",
    "SkidModel",
    "add_model_dir",
    "clear_extra_model_dirs",
    "get_preset",
    "list_presets",
]
