"""Soft-PLC cyclic scan shell (SWD-85 / docs/control/01-scan-scheduler.md).

Owns phase order and period notion. Wall-clock is injectable; core never
hard-codes time. Overrun/jitter are hobby-grade diagnostics, not SIL timing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Sequence


class ScanPhase(str, Enum):
    """Fixed Soft-PLC scan phases — order is part of the product contract."""

    IN = "IN"
    SAFETY = "SAFETY"
    CONTROL = "CONTROL"
    OUT = "OUT"


PHASE_ORDER: tuple[ScanPhase, ...] = (
    ScanPhase.IN,
    ScanPhase.SAFETY,
    ScanPhase.CONTROL,
    ScanPhase.OUT,
)


@dataclass
class ScanConfig:
    """Scan period / overrun threshold.

    ``scan_period_s`` is the *configured* period (demo default 0.1 s ≤ 100 ms).
    Callers still pass injectable ``dt`` into logic each cycle — the period is
    for scheduling/diagnostics, not a hidden wall-clock sleep inside FB math.
    """

    scan_period_s: float = 0.1
    """Configured cycle period (seconds). Must be > 0."""

    def __post_init__(self) -> None:
        if self.scan_period_s <= 0:
            raise ValueError("scan_period_s must be positive")


@dataclass
class ScanDiagnostics:
    """Hobby-grade scan diagnostics (counters / last sample — not HMI tags)."""

    scan_count: int = 0
    overrun_count: int = 0
    last_duration_s: Optional[float] = None
    last_dt_s: Optional[float] = None
    last_phases: tuple[ScanPhase, ...] = ()
    """Phases actually executed on the last scan (should match PHASE_ORDER)."""


PhaseCallback = Callable[[], None]


@dataclass
class ScanShell:
    """Runs one cyclic scan in locked phase order with optional timing hooks.

    Typical Add-on path::

        shell.run(
            dt,
            on_in=lambda: integration.scan_inputs(image),
            on_safety=...,
            on_control=...,
            on_out=lambda: integration.scan_outputs(image),
            duration_s=measured_wall_time,  # optional
        )
    """

    config: ScanConfig = field(default_factory=ScanConfig)
    diagnostics: ScanDiagnostics = field(default_factory=ScanDiagnostics)

    def run(
        self,
        dt: float,
        *,
        on_in: PhaseCallback,
        on_safety: PhaseCallback,
        on_control: PhaseCallback,
        on_out: PhaseCallback,
        duration_s: Optional[float] = None,
    ) -> ScanDiagnostics:
        """Execute IN → SAFETY → CONTROL → OUT.

        ``dt`` is the sample time handed to continuous FBs (must be ≥ 0).
        ``duration_s``, when provided, is wall/logical duration of this cycle
        for overrun counting against ``scan_period_s``.
        """
        if dt < 0:
            raise ValueError("dt must be non-negative")

        callbacks: Sequence[tuple[ScanPhase, PhaseCallback]] = (
            (ScanPhase.IN, on_in),
            (ScanPhase.SAFETY, on_safety),
            (ScanPhase.CONTROL, on_control),
            (ScanPhase.OUT, on_out),
        )
        executed: list[ScanPhase] = []
        for phase, cb in callbacks:
            cb()
            executed.append(phase)

        diag = self.diagnostics
        diag.scan_count += 1
        diag.last_dt_s = dt
        diag.last_phases = tuple(executed)
        diag.last_duration_s = duration_s
        if duration_s is not None and duration_s > self.config.scan_period_s:
            diag.overrun_count += 1
        return diag


def assert_phase_order(phases: Sequence[ScanPhase]) -> None:
    """Raise ``AssertionError`` if ``phases`` is not exactly ``PHASE_ORDER``."""
    got = tuple(phases)
    if got != PHASE_ORDER:
        raise AssertionError(f"scan phase order {got!r} != {PHASE_ORDER!r}")


__all__ = [
    "PHASE_ORDER",
    "ScanConfig",
    "ScanDiagnostics",
    "ScanPhase",
    "ScanShell",
    "assert_phase_order",
]
