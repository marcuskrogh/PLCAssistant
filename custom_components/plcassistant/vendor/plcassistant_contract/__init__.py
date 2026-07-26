"""PLCAssistant shared contract: bindings, coercion, fail-safe (no HA/OpenPLC imports).

Vendored under the HACS integration so installs do not require PyPI or monorepo
sys.path hacks. Canonical source for editable/dev installs remains
``packages/plcassistant_contract/`` — keep both in sync via
``scripts/sync_contract_vendor.sh``.
"""

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
]
