"""HA-free helpers for dynamics model store + editor catalog (SWD-166/167)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from .compile import parse_model_document
from .equations import describe_op_equations, equation_templates
from .expr import ExpressionError
from .ops import OP_CATALOG

# Bind ports and editable params shown in the block editor UI.
OP_UI_META: dict[str, dict[str, Any]] = {
    "tank": {
        "label": "Tank",
        "binds": ["h", "q_in", "q_out"],
        "params": ["area"],
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
        "params": [],
        "ode": True,
        "help": "Author state equations (and optional algebraics) one row at a time.",
    },
}

# Skid global param / initial-state fields for the dynamics editor (SWD-250).
SKID_PARAM_FIELDS: list[dict[str, Any]] = [
    {
        "key": "q_pump_max",
        "label": "Max pump flow",
        "unit": "L/min",
        "highlight": True,
    },
    {"key": "a_tank", "label": "Tank cross-section", "unit": "m²"},
    {"key": "a_res", "label": "Reservoir cross-section", "unit": "m²"},
    {"key": "h_tank_max", "label": "Max tank level", "unit": "m"},
    {"key": "h_res_max", "label": "Max reservoir level", "unit": "m"},
    {"key": "k_drain", "label": "Drain coefficient", "unit": "L/(min·√m)"},
    {"key": "pump_tau", "label": "Pump time constant", "unit": "min"},
    {"key": "speed_fb_tau", "label": "Speed feedback lag", "unit": "min"},
    {"key": "lim_res_ll", "label": "Reservoir low-level limit", "unit": "m"},
]

SKID_INITIAL_FIELDS: list[dict[str, Any]] = [
    {"key": "h_tank", "label": "Tank level", "unit": "m"},
    {"key": "h_res", "label": "Reservoir level", "unit": "m"},
    {"key": "ft_inlet", "label": "Inlet flow", "unit": "L/min"},
    {"key": "sc_pump", "label": "Pump speed feedback", "unit": "%"},
]


def catalog_payload() -> dict[str, Any]:
    templates = equation_templates()
    return {
        "ops": [
            {
                "type": name,
                **{k: v for k, v in OP_UI_META.get(name, {}).items()},
                "equation_templates": templates.get(name, []),
                # Default example forms (unbound) for palette preview.
                "equations": [
                    e.as_dict()
                    for e in describe_op_equations(
                        name,
                        {b: b for b in OP_UI_META.get(name, {}).get("binds", [])},
                        {},
                    )
                ]
                if name != "custom_ode"
                else [],
            }
            for name in sorted(OP_CATALOG)
        ],
        "schema_version": "1.0",
        "measurement_help": (
            "Measurement equations map Soft-PLC IN tags to expressions over "
            "state, inputs, and params (y = g(x, u, θ)). Distinct from ODEs."
        ),
        "param_fields": {"skid": SKID_PARAM_FIELDS},
        "initial_fields": {"skid": SKID_INITIAL_FIELDS},
    }


def describe_document_op(op: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Substituted equations for one op instance (editor inspector)."""
    return [
        e.as_dict()
        for e in describe_op_equations(
            str(op.get("type") or ""),
            op.get("bind") or {},
            op.get("params") or {},
        )
    ]


def _reject_non_finite_mapping(mapping: Mapping[str, Any] | None, label: str) -> None:
    if not mapping:
        return
    for key, value in mapping.items():
        try:
            n = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label}[{key!r}] must be numeric") from exc
        if not math.isfinite(n):
            raise ValueError(f"{label}[{key!r}] must be finite")


def validate_document(doc: Mapping[str, Any] | dict[str, Any]) -> dict[str, Any]:
    """Parse + compile; return a JSON-serializable document or raise ValueError."""
    _reject_non_finite_mapping(doc.get("params"), "params")
    _reject_non_finite_mapping(doc.get("initial"), "initial")
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
    if (
        not key
        or "/" in key
        or "\\" in key
        or key in {".", ".."}
        or ".." in key
    ):
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
    "SKID_INITIAL_FIELDS",
    "SKID_PARAM_FIELDS",
    "catalog_payload",
    "describe_document_op",
    "list_user_models",
    "load_user_model",
    "models_dir",
    "save_user_model",
    "seed_skid_composed",
    "validate_document",
]
