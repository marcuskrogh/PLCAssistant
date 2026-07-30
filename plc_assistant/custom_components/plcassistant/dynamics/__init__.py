"""Integration-owned process dynamics (SWD-146 / SWD-144 / SWD-143)."""

from .compile import SpecModel, load_model_document, parse_model_document
from .core import FixedStepRunner, ModelSpec, parse_scan_period_s
from .expr import ExpressionError, compile_expr
from .ops import OP_CATALOG
from .options import (
    DEFAULT_DYNAMICS_PRESET,
    normalize_preset,
    parse_dynamics_params,
    resolve_dynamics_options,
    validate_preset,
)
from .plant import PlantSimulator
from .registry import add_model_dir, clear_extra_model_dirs, get_preset, list_presets
from .skid import PRESETS, SKID_SPEC, SkidModel
from .store import OP_UI_META, catalog_payload, validate_document

__all__ = [
    "DEFAULT_DYNAMICS_PRESET",
    "OP_CATALOG",
    "OP_UI_META",
    "ExpressionError",
    "FixedStepRunner",
    "ModelSpec",
    "PRESETS",
    "PlantSimulator",
    "SKID_SPEC",
    "SkidModel",
    "SpecModel",
    "add_model_dir",
    "catalog_payload",
    "clear_extra_model_dirs",
    "compile_expr",
    "get_preset",
    "list_presets",
    "load_model_document",
    "normalize_preset",
    "parse_dynamics_params",
    "parse_model_document",
    "parse_scan_period_s",
    "resolve_dynamics_options",
    "validate_document",
    "validate_preset",
]
