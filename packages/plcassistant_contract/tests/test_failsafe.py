"""Fail-safe / cold-start / bridge-fault tests."""

from __future__ import annotations

import pytest

from plcassistant_contract import (
    Binding,
    BindingDirection,
    ColdStartPolicy,
    InputContext,
    InputPolicy,
    OutputFaultPolicy,
    ValueType,
    apply_input_policy,
    apply_output_bridge_fault,
)


def _input(**kwargs) -> Binding:
    base = dict(
        tag="I0",
        direction=BindingDirection.INPUT,
        entity_id="binary_sensor.x",
        value_type=ValueType.BOOL,
    )
    base.update(kwargs)
    return Binding(**base)


def test_cold_start_force_zero_before_first_good():
    binding = _input(unavailable_policy=InputPolicy.HOLD_LAST)
    ctx = InputContext()
    assert apply_input_policy(binding, "unavailable", ctx) is False
    assert ctx.has_good is False


def test_hold_last_after_good_sample():
    binding = _input(unavailable_policy=InputPolicy.HOLD_LAST)
    ctx = InputContext()
    assert apply_input_policy(binding, "on", ctx) is True
    assert apply_input_policy(binding, "unavailable", ctx) is True


def test_stale_policy_force_zero():
    binding = _input(
        unavailable_policy=InputPolicy.HOLD_LAST,
        stale_after_s=5.0,
        stale_policy=InputPolicy.FORCE_ZERO,
    )
    ctx = InputContext()
    assert apply_input_policy(binding, "on", ctx, now=0.0) is True
    out = apply_input_policy(binding, "unavailable", ctx, now=10.0)
    assert out is False
    assert ctx.stale is True


def test_force_value_requires_safe_value_at_runtime():
    binding = _input(
        unavailable_policy=InputPolicy.FORCE_VALUE,
        safe_value=True,
        cold_start_policy=ColdStartPolicy.FORCE_VALUE,
    )
    ctx = InputContext()
    assert apply_input_policy(binding, "unknown", ctx) is True


def test_critical_defaults_to_safe_off():
    binding = Binding(
        tag="Q0",
        direction=BindingDirection.OUTPUT,
        entity_id="switch.pump",
        value_type=ValueType.BOOL,
        write_mode="entity",
        critical=True,
        on_bridge_fault=OutputFaultPolicy.HOLD_LAST_COMMAND,
    )
    policy, force = apply_output_bridge_fault(binding)
    assert policy is OutputFaultPolicy.SAFE_OFF
    assert force is False


def test_hold_last_command_non_critical():
    binding = Binding(
        tag="Q1",
        direction=BindingDirection.OUTPUT,
        entity_id="switch.lamp",
        value_type=ValueType.BOOL,
        write_mode="entity",
        critical=False,
    )
    policy, force = apply_output_bridge_fault(binding)
    assert policy is OutputFaultPolicy.HOLD_LAST_COMMAND
    assert force is None
