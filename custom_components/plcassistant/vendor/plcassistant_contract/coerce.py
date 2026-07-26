"""HA state/attribute coercion into PLC tag types (docs/IO_HAL.md)."""

from __future__ import annotations

from typing import Any

from .models import ValueType

_UNAVAILABLE = {"unavailable", "unknown", "none", ""}


def _is_unavailable(raw: Any) -> bool:
    if raw is None:
        return True
    if isinstance(raw, str) and raw.strip().lower() in _UNAVAILABLE:
        return True
    return False


def coerce_ha_value(
    raw: Any,
    value_type: ValueType,
    *,
    scale: float = 1.0,
    offset: float = 0.0,
) -> tuple[Any | None, bool]:
    """
    Coerce a HA state/attribute to a PLC value.

    Returns (value, ok). ok is False when the raw value is unavailable/unknown
    or cannot be coerced — caller applies fail-safe policy.
    """
    if _is_unavailable(raw):
        return None, False

    if value_type is ValueType.STRING:
        return str(raw), True

    if value_type is ValueType.BOOL:
        if isinstance(raw, bool):
            return raw, True
        if isinstance(raw, (int, float)):
            return bool(raw), True
        text = str(raw).strip().lower()
        if text in {"on", "true", "1", "yes"}:
            return True, True
        if text in {"off", "false", "0", "no"}:
            return False, True
        try:
            return float(text) != 0.0, True
        except ValueError:
            return None, False

    # number
    if isinstance(raw, bool):
        number = 1.0 if raw else 0.0
    elif isinstance(raw, (int, float)):
        number = float(raw)
    else:
        text = str(raw).strip().lower()
        if text in {"on", "true", "yes"}:
            number = 1.0
        elif text in {"off", "false", "no"}:
            number = 0.0
        else:
            try:
                number = float(text)
            except ValueError:
                return None, False
    return number * scale + offset, True


def zero_for(value_type: ValueType) -> Any:
    if value_type is ValueType.BOOL:
        return False
    if value_type is ValueType.NUMBER:
        return 0.0
    return ""
