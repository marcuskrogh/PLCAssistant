"""Binding and status models aligned with docs/IO_HAL.md."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class BindingDirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    MEMORY_MIRROR = "memory_mirror"


class ValueType(str, Enum):
    BOOL = "bool"
    NUMBER = "number"
    STRING = "string"


class InputPolicy(str, Enum):
    HOLD_LAST = "hold_last"
    FORCE_ZERO = "force_zero"
    FORCE_VALUE = "force_value"
    FAULT = "fault"


class ColdStartPolicy(str, Enum):
    FORCE_ZERO = "force_zero"
    FORCE_VALUE = "force_value"
    FAULT = "fault"


class OutputFaultPolicy(str, Enum):
    HOLD_LAST_COMMAND = "hold_last_command"
    SAFE_OFF = "safe_off"
    NOOP = "noop"


@dataclass(frozen=True)
class ServiceTarget:
    domain: str
    service: str
    data_template: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "service": self.service,
            "data_template": dict(self.data_template),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ServiceTarget | None:
        if not data:
            return None
        return cls(
            domain=str(data["domain"]),
            service=str(data["service"]),
            data_template=dict(data.get("data_template") or {}),
        )


@dataclass
class Binding:
    """One entity ↔ PLC tag mapping."""

    tag: str
    direction: BindingDirection
    entity_id: str
    value_type: ValueType
    attribute: str | None = None
    enabled: bool = True
    # Input / mirror freshness
    unavailable_policy: InputPolicy = InputPolicy.HOLD_LAST
    stale_after_s: float | None = None
    stale_policy: InputPolicy | None = None
    safe_value: Any = None
    cold_start_policy: ColdStartPolicy = ColdStartPolicy.FORCE_ZERO
    scale: float = 1.0
    offset: float = 0.0
    # Output
    write_mode: str | None = None  # "service" | "entity"
    service: ServiceTarget | None = None
    idempotent: bool = True
    min_write_interval_ms: int = 0
    on_bridge_fault: OutputFaultPolicy = OutputFaultPolicy.HOLD_LAST_COMMAND
    critical: bool = False
    # Memory mirror
    mirror_to_ha: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["direction"] = self.direction.value
        data["value_type"] = self.value_type.value
        data["unavailable_policy"] = self.unavailable_policy.value
        data["cold_start_policy"] = self.cold_start_policy.value
        data["on_bridge_fault"] = self.on_bridge_fault.value
        if self.stale_policy is not None:
            data["stale_policy"] = self.stale_policy.value
        if self.service is not None:
            data["service"] = self.service.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Binding:
        stale = data.get("stale_policy")
        return cls(
            tag=str(data["tag"]),
            direction=BindingDirection(data["direction"]),
            entity_id=str(data["entity_id"]),
            value_type=ValueType(data["value_type"]),
            attribute=data.get("attribute"),
            enabled=bool(data.get("enabled", True)),
            unavailable_policy=InputPolicy(
                data.get("unavailable_policy", InputPolicy.HOLD_LAST.value)
            ),
            stale_after_s=data.get("stale_after_s"),
            stale_policy=InputPolicy(stale) if stale else None,
            safe_value=data.get("safe_value"),
            cold_start_policy=ColdStartPolicy(
                data.get("cold_start_policy", ColdStartPolicy.FORCE_ZERO.value)
            ),
            scale=float(data.get("scale", 1.0)),
            offset=float(data.get("offset", 0.0)),
            write_mode=data.get("write_mode"),
            service=ServiceTarget.from_dict(data.get("service")),
            idempotent=bool(data.get("idempotent", True)),
            min_write_interval_ms=int(data.get("min_write_interval_ms", 0)),
            on_bridge_fault=OutputFaultPolicy(
                data.get("on_bridge_fault", OutputFaultPolicy.HOLD_LAST_COMMAND.value)
            ),
            critical=bool(data.get("critical", False)),
            mirror_to_ha=bool(data.get("mirror_to_ha", False)),
        )


@dataclass
class ScanOptions:
    scan_period_ms: int = 100
    default_unavailable_policy: InputPolicy = InputPolicy.HOLD_LAST
    default_on_bridge_fault: OutputFaultPolicy = OutputFaultPolicy.HOLD_LAST_COMMAND

    def to_dict(self) -> dict[str, Any]:
        return {
            "scan_period_ms": self.scan_period_ms,
            "default_unavailable_policy": self.default_unavailable_policy.value,
            "default_on_bridge_fault": self.default_on_bridge_fault.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ScanOptions:
        data = data or {}
        return cls(
            scan_period_ms=int(data.get("scan_period_ms", 100)),
            default_unavailable_policy=InputPolicy(
                data.get("default_unavailable_policy", InputPolicy.HOLD_LAST.value)
            ),
            default_on_bridge_fault=OutputFaultPolicy(
                data.get(
                    "default_on_bridge_fault",
                    OutputFaultPolicy.HOLD_LAST_COMMAND.value,
                )
            ),
        )


@dataclass
class RuntimeStatus:
    """Addon GetStatus / StatusPush payload (IO_HAL diagnostics)."""

    scan_period_ms: float = 100.0
    last_cycle_ms: float = 0.0
    overrun_count: int = 0
    bridge_connected: bool = False
    bridge_lag_ms: float = 0.0
    stale_binding_count: int = 0
    fail_safe_active: bool = False
    binding_error_count: int = 0
    runtime_state: str = "stopped"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RuntimeStatus:
        data = data or {}
        return cls(
            scan_period_ms=float(data.get("scan_period_ms", 100.0)),
            last_cycle_ms=float(data.get("last_cycle_ms", 0.0)),
            overrun_count=int(data.get("overrun_count", 0)),
            bridge_connected=bool(data.get("bridge_connected", False)),
            bridge_lag_ms=float(data.get("bridge_lag_ms", 0.0)),
            stale_binding_count=int(data.get("stale_binding_count", 0)),
            fail_safe_active=bool(data.get("fail_safe_active", False)),
            binding_error_count=int(data.get("binding_error_count", 0)),
            runtime_state=str(data.get("runtime_state", "stopped")),
        )

    @classmethod
    def disconnected(cls, scan_period_ms: float = 100.0) -> RuntimeStatus:
        return cls(scan_period_ms=scan_period_ms, bridge_connected=False, runtime_state="stopped")
