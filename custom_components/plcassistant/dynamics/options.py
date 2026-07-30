"""Resolve config-entry dynamics options (HA-free, SWD-143)."""

from __future__ import annotations

import json
from typing import Any, Mapping

from .registry import get_preset, list_presets

DEFAULT_DYNAMICS_PRESET = "skid"


def normalize_preset(name: str | None) -> str:
    key = str(name or DEFAULT_DYNAMICS_PRESET).strip().lower()
    return key or DEFAULT_DYNAMICS_PRESET


def parse_dynamics_params(raw: Any) -> dict[str, float]:
    """Parse options ``dynamics_params`` from mapping or JSON text."""
    if raw is None or raw == "":
        return {}
    data: Any
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"dynamics_params must be JSON object: {exc}") from exc
    elif isinstance(raw, Mapping):
        data = raw
    else:
        raise ValueError("dynamics_params must be a mapping or JSON object string")
    if not isinstance(data, Mapping):
        raise ValueError("dynamics_params must be a JSON object")
    out: dict[str, float] = {}
    for key, value in data.items():
        try:
            out[str(key)] = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"dynamics_params[{key!r}] must be numeric") from exc
    return out


def resolve_dynamics_options(
    options: Mapping[str, Any] | None,
) -> tuple[str, dict[str, float]]:
    """Return ``(preset, params)`` from config-entry options."""
    opts = options or {}
    preset = normalize_preset(opts.get("dynamics_preset"))
    params = parse_dynamics_params(opts.get("dynamics_params"))
    return preset, params


def validate_preset(name: str | None) -> str:
    """Normalize and ensure the preset exists in the registry."""
    key = normalize_preset(name)
    available = set(list_presets())
    if key not in available:
        # Still try load in case of race; KeyError message is operator-facing.
        try:
            get_preset(key)
        except KeyError as exc:
            raise KeyError(
                f"unknown dynamics preset: {key!r} (available: {sorted(available)})"
            ) from exc
    return key


__all__ = [
    "DEFAULT_DYNAMICS_PRESET",
    "normalize_preset",
    "parse_dynamics_params",
    "resolve_dynamics_options",
    "validate_preset",
]
