"""HA-free helpers for dynamics model store + editor catalog (SWD-166)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .compile import parse_model_document
from .expr import ExpressionError
from .ops import OP_CATALOG

# Bind ports and editable params shown in the block editor UI.
OP_UI_META: dict[str, dict[str, Any]] = {
    "tank": {
        "label": "Tank",
        "binds": ["h", "q_in", "q_out"],
        "params": [],
        "help": "Level inventory from net volumetric flow.",
    },
    "pump": {
        "label": "Pump",
        "binds": ["cmd", "h_source", "q"],
        "params": ["q_max", "tau", "lim_ll"],
        "help": "CMD/speed → flow with lag and low-level derate.",
    },
    "orifice": {
        "label": "Orifice",
        "binds": ["h", "q"],
        "params": ["k"],
        "help": "Gravity drain: q = k * sqrt(h).",
    },
    "lag": {
        "label": "Lag",
        "binds": ["u", "y"],
        "params": ["tau"],
        "help": "First-order lag.",
    },
    "custom_ode": {
        "label": "Custom ODE",
        "binds": [],
        "params": ["derivatives"],
        "ode": True,
        "help": "Map of state_key → d(state)/dt expression.",
    },
}


def catalog_payload() -> dict[str, Any]:
    return {
        "ops": [
            {
                "type": name,
                **{k: v for k, v in OP_UI_META.get(name, {}).items()},
            }
            for name in sorted(OP_CATALOG)
        ],
        "schema_version": "1.0",
    }


def validate_document(doc: Mapping[str, Any] | dict[str, Any]) -> dict[str, Any]:
    """Parse + compile; return a JSON-serializable document or raise ValueError."""
    try:
        parsed = parse_model_document(doc)
        from .compile import document_to_model

        document_to_model(parsed)
    except (ExpressionError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(str(exc)) from exc
    # Round-trip through JSON for a plain dict the editor can store.
    return json.loads(json.dumps(dict(doc), sort_keys=False))


def models_dir(root: Path) -> Path:
    path = Path(root) / "plcassistant" / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_user_models(root: Path) -> list[str]:
    base = models_dir(root)
    names: set[str] = set()
    for path in base.iterdir() if base.is_dir() else []:
        if path.suffix.lower() in {".json", ".yaml", ".yml"}:
            names.add(path.stem.lower())
    return sorted(names)


def load_user_model(root: Path, name: str) -> dict[str, Any]:
    key = str(name or "").strip().lower()
    if not key:
        raise ValueError("model name required")
    base = models_dir(root)
    for suffix in (".json", ".yaml", ".yml"):
        path = base / f"{key}{suffix}"
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            if suffix == ".json":
                data = json.loads(text)
            else:
                try:
                    import yaml  # type: ignore
                except ImportError as exc:
                    raise ValueError("YAML models require PyYAML") from exc
                data = yaml.safe_load(text)
            if not isinstance(data, dict):
                raise ValueError("model document must be an object")
            return data
    raise FileNotFoundError(f"model not found: {key}")


def save_user_model(root: Path, name: str, doc: Mapping[str, Any]) -> Path:
    key = str(name or "").strip().lower()
    if not key or any(ch in key for ch in "/\\.."):
        raise ValueError(f"invalid model name: {name!r}")
    validated = validate_document(doc)
    # Keep document name in sync with file stem.
    validated["name"] = key
    validated["version"] = str(validated.get("version") or "1.0")
    path = models_dir(root) / f"{key}.json"
    path.write_text(json.dumps(validated, indent=2) + "\n", encoding="utf-8")
    return path


def seed_skid_composed(root: Path, bundled: Path) -> Path | None:
    """Copy bundled skid_composed into user models if missing."""
    dest = models_dir(root) / "skid_composed.json"
    if dest.is_file():
        return None
    if not bundled.is_file():
        return None
    dest.write_text(bundled.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


__all__ = [
    "OP_UI_META",
    "catalog_payload",
    "list_user_models",
    "load_user_model",
    "models_dir",
    "save_user_model",
    "seed_skid_composed",
    "validate_document",
]
