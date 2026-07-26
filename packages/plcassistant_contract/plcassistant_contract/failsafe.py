"""Freshness, cold-start, and bridge-fault policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .coerce import coerce_ha_value, zero_for
from .models import (
    Binding,
    ColdStartPolicy,
    InputPolicy,
    OutputFaultPolicy,
    ValueType,
)


Clock = Callable[[], float]


@dataclass
class InputContext:
    """Mutable per-binding input state for HAL / tests."""

    last_good: Any | None = None
    has_good: bool = False
    last_update_ts: float | None = None
    faulted: bool = False
    stale: bool = False


def _apply_policy(
    policy: InputPolicy,
    binding: Binding,
    ctx: InputContext,
) -> Any:
    if policy is InputPolicy.HOLD_LAST:
        if ctx.has_good:
            return ctx.last_good
        return _cold_start(binding, ctx)
    if policy is InputPolicy.FORCE_ZERO:
        return zero_for(binding.value_type)
    if policy is InputPolicy.FORCE_VALUE:
        return binding.safe_value
    # FAULT
    ctx.faulted = True
    return zero_for(binding.value_type)


def _cold_start(binding: Binding, ctx: InputContext) -> Any:
    policy = binding.cold_start_policy
    if policy is ColdStartPolicy.FORCE_ZERO:
        return zero_for(binding.value_type)
    if policy is ColdStartPolicy.FORCE_VALUE:
        return binding.safe_value
    ctx.faulted = True
    return zero_for(binding.value_type)


def apply_input_policy(
    binding: Binding,
    raw: Any,
    ctx: InputContext,
    *,
    now: float | None = None,
    clock: Clock | None = None,
) -> Any:
    """Apply unavailable/stale/cold-start after coercion. Updates ctx."""
    ts = now if now is not None else (clock() if clock else None)
    value, ok = coerce_ha_value(
        raw, binding.value_type, scale=binding.scale, offset=binding.offset
    )

    if ok:
        ctx.last_good = value
        ctx.has_good = True
        ctx.last_update_ts = ts
        ctx.stale = False
        ctx.faulted = False
        return value

    # Unavailable / bad coerce
    if (
        binding.stale_after_s is not None
        and ctx.has_good
        and ctx.last_update_ts is not None
        and ts is not None
        and (ts - ctx.last_update_ts) >= binding.stale_after_s
    ):
        ctx.stale = True
        policy = binding.stale_policy or binding.unavailable_policy
        return _apply_policy(policy, binding, ctx)

    ctx.stale = False
    return _apply_policy(binding.unavailable_policy, binding, ctx)


def effective_input(
    binding: Binding,
    raw: Any,
    ctx: InputContext,
    *,
    now: float | None = None,
    clock: Clock | None = None,
) -> Any:
    """Alias for apply_input_policy (HAL-facing name)."""
    return apply_input_policy(binding, raw, ctx, now=now, clock=clock)


def apply_output_bridge_fault(binding: Binding) -> tuple[OutputFaultPolicy, Any | None]:
    """
    Decide output action when the HA bridge is unhealthy.

    Returns (policy, force_value_or_None).
    force_value is set only for SAFE_OFF.
    """
    policy = binding.on_bridge_fault
    if binding.critical and policy is OutputFaultPolicy.HOLD_LAST_COMMAND:
        policy = OutputFaultPolicy.SAFE_OFF

    if policy is OutputFaultPolicy.SAFE_OFF:
        if binding.safe_value is not None:
            return policy, binding.safe_value
        if binding.value_type is ValueType.BOOL:
            return policy, False
        if binding.value_type is ValueType.NUMBER:
            return policy, 0.0
        return policy, ""
    return policy, None
