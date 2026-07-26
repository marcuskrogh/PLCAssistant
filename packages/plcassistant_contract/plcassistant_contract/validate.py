"""Binding validation against IO_HAL rules."""

from __future__ import annotations

from .models import Binding, BindingDirection, InputPolicy, OutputFaultPolicy


class ValidationError(ValueError):
    """Invalid binding configuration."""


def validate_binding(binding: Binding) -> None:
    if not binding.tag.strip():
        raise ValidationError("tag is required")
    if not binding.entity_id.strip():
        raise ValidationError("entity_id is required")

    needs_safe = (
        binding.unavailable_policy is InputPolicy.FORCE_VALUE
        or binding.stale_policy is InputPolicy.FORCE_VALUE
        or binding.cold_start_policy.value == "force_value"
    )
    if needs_safe and binding.safe_value is None:
        raise ValidationError("safe_value is required when a force_value policy is selected")

    if binding.direction is BindingDirection.OUTPUT:
        if binding.write_mode not in {"service", "entity"}:
            raise ValidationError("output bindings require write_mode 'service' or 'entity'")
        if binding.write_mode == "service" and binding.service is None:
            raise ValidationError("service write_mode requires service {domain, service}")
        if binding.min_write_interval_ms < 0:
            raise ValidationError("min_write_interval_ms must be >= 0")

    if binding.direction is BindingDirection.MEMORY_MIRROR:
        # same freshness rules as inputs; no write_mode required
        pass

    if binding.stale_after_s is not None and binding.stale_after_s < 0:
        raise ValidationError("stale_after_s must be >= 0")


def validate_bindings(bindings: list[Binding]) -> None:
    seen: set[str] = set()
    for binding in bindings:
        validate_binding(binding)
        key = f"{binding.direction.value}:{binding.tag}"
        if key in seen:
            raise ValidationError(f"duplicate binding for {key}")
        seen.add(key)
