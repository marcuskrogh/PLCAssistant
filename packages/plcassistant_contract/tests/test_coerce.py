"""Table-driven coercion tests."""

from __future__ import annotations

import pytest

from plcassistant_contract import ValueType, coerce_ha_value


@pytest.mark.parametrize(
    "raw,value_type,expected",
    [
        ("on", ValueType.BOOL, True),
        ("off", ValueType.BOOL, False),
        ("true", ValueType.BOOL, True),
        ("false", ValueType.BOOL, False),
        ("1", ValueType.BOOL, True),
        ("0", ValueType.BOOL, False),
        (2.5, ValueType.BOOL, True),
        (0, ValueType.BOOL, False),
        ("on", ValueType.NUMBER, 1.0),
        ("off", ValueType.NUMBER, 0.0),
        ("3.5", ValueType.NUMBER, 3.5),
        (10, ValueType.NUMBER, 10.0),
        ("hello", ValueType.STRING, "hello"),
    ],
)
def test_coerce_ok(raw, value_type, expected):
    value, ok = coerce_ha_value(raw, value_type)
    assert ok is True
    assert value == expected


@pytest.mark.parametrize("raw", ["unavailable", "unknown", None, ""])
def test_coerce_unavailable(raw):
    value, ok = coerce_ha_value(raw, ValueType.BOOL)
    assert ok is False
    assert value is None


def test_scale_offset():
    value, ok = coerce_ha_value("10", ValueType.NUMBER, scale=0.1, offset=1.0)
    assert ok is True
    assert value == pytest.approx(2.0)
