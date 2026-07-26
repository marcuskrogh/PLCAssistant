"""PLCAssistant shared contract: bindings, coercion, fail-safe (no HA/OpenPLC imports)."""

from .models import (
    Binding,
    BindingDirection,
    ColdStartPolicy,
    InputPolicy,
    OutputFaultPolicy,
    RuntimeStatus,
    ScanOptions,
    ServiceTarget,
    ValueType,
)
from .coerce import coerce_ha_value
from .failsafe import (
    InputContext,
    apply_input_policy,
    apply_output_bridge_fault,
    effective_input,
)
from .validate import ValidationError, validate_binding, validate_bindings
from .client import AddonUnavailableError, ControlPlaneClient

__all__ = [
    "Binding",
    "BindingDirection",
    "ColdStartPolicy",
    "InputPolicy",
    "OutputFaultPolicy",
    "RuntimeStatus",
    "ScanOptions",
    "ServiceTarget",
    "ValueType",
    "coerce_ha_value",
    "InputContext",
    "apply_input_policy",
    "apply_output_bridge_fault",
    "effective_input",
    "ValidationError",
    "validate_binding",
    "validate_bindings",
    "AddonUnavailableError",
    "ControlPlaneClient",
]
