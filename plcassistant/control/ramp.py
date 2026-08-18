"""Setpoint rate limiter (faceplate SP path, not a PID equation param)."""

from __future__ import annotations


def ramp_setpoint(
    current: float,
    target: float,
    max_rate: float,
    dt: float,
) -> float:
    """Move ``current`` toward ``target`` at most ``max_rate`` units per second.

    ``max_rate <= 0`` or ``dt <= 0`` is instant (return ``target``). When the
    remaining distance fits in one scan, snap to ``target``.
    """
    dest = float(target)
    rate = float(max_rate)
    step_dt = float(dt)
    if rate <= 0.0 or step_dt <= 0.0:
        return dest
    here = float(current)
    delta = dest - here
    step = rate * step_dt
    if abs(delta) <= step:
        return dest
    return here + (step if delta > 0.0 else -step)


__all__ = ["ramp_setpoint"]
