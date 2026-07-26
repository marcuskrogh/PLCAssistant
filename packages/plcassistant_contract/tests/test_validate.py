"""Binding validation tests."""

from __future__ import annotations

import pytest

from plcassistant_contract import (
    Binding,
    BindingDirection,
    InputPolicy,
    ServiceTarget,
    ValidationError,
    ValueType,
    validate_binding,
    validate_bindings,
)


def test_output_service_requires_service_block():
    binding = Binding(
        tag="Q0",
        direction=BindingDirection.OUTPUT,
        entity_id="light.a",
        value_type=ValueType.BOOL,
        write_mode="service",
    )
    with pytest.raises(ValidationError, match="service"):
        validate_binding(binding)


def test_force_value_requires_safe_value():
    binding = Binding(
        tag="I0",
        direction=BindingDirection.INPUT,
        entity_id="sensor.t",
        value_type=ValueType.NUMBER,
        unavailable_policy=InputPolicy.FORCE_VALUE,
    )
    with pytest.raises(ValidationError, match="safe_value"):
        validate_binding(binding)


def test_valid_output_service():
    binding = Binding(
        tag="Q0",
        direction=BindingDirection.OUTPUT,
        entity_id="light.a",
        value_type=ValueType.BOOL,
        write_mode="service",
        service=ServiceTarget(domain="light", service="turn_on"),
    )
    validate_binding(binding)


def test_duplicate_tags_rejected():
    b1 = Binding(
        tag="I0",
        direction=BindingDirection.INPUT,
        entity_id="sensor.a",
        value_type=ValueType.BOOL,
    )
    b2 = Binding(
        tag="I0",
        direction=BindingDirection.INPUT,
        entity_id="sensor.b",
        value_type=ValueType.BOOL,
    )
    with pytest.raises(ValidationError, match="duplicate"):
        validate_bindings([b1, b2])
