"""IFAC 2024 incremental PID reference (SWD-367).

Reimplementation of Sundström, Hägglund, Bauer, Eker, Soltesz,
*Reference Implementation of the PID Controller*, IFAC-PapersOnLine 58(7),
370–375, doi:10.1016/j.ifacol.2024.08.090.

Listings 1–4 are transcribed here. The Soft-PLC scan supplies ``dt``;
listing 5's threaded runtime is out of scope. Do not vendor copybit/pid.
"""

from __future__ import annotations

import math
from typing import Any

# External windup flag (listing 4): none / upper / lower / both.
WINDUP_NONE = 0
WINDUP_UPPER = 1
WINDUP_LOWER = 2
WINDUP_BOTH = 3

# Paper default: Tf / Ts = 10.
DEFAULT_TF_TS = 10.0
DEFAULT_TS = 0.1


def anti_windup(dui: float, windup: float | int) -> float:
    """Clamp the integral increment (listing 4)."""
    delta = float(dui)
    flag = int(float(windup))
    if flag in (WINDUP_LOWER, WINDUP_BOTH):
        delta = max(delta, 0.0)
    if flag in (WINDUP_UPPER, WINDUP_BOTH):
        delta = min(delta, 0.0)
    return delta


def zoh_fy(tf_ts: float, tx: float) -> tuple[float, float, float, float, float, float]:
    """Zero-order-hold coefficients for the measurement filter (listing 3).

    Returns ``(a11, a12, a21, a22, b1, b2)``. When ``tf_ts <= 0`` the filter
    is a bypass: ``yf = y``, ``dyf = 0``.
    """
    if tf_ts <= 0.0:
        return (0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    tx_safe = float(tx) if float(tx) > 0.0 else 1.0
    h1 = tx_safe / float(tf_ts)
    h2 = math.exp(-h1)
    h3 = h1 * h2
    h4 = h3 / float(tf_ts)
    a11 = h2 + h3
    a12 = h2
    a21 = -h4
    a22 = h2 - h3
    b1 = 1.0 - h2 - h3
    b2 = h4
    return a11, a12, a21, a22, b1, b2


def _tx(dt: float, ts: float) -> float:
    """Jitter scale Tx = dt / ts (paper §3.5). Nominal periodic scan → Tx = 1."""
    if dt > 0.0 and ts > 0.0:
        return dt / ts
    return 1.0


def pid_scan(
    *,
    pv: float,
    sp: float,
    running: bool,
    uff: float = 0.0,
    track: bool = False,
    utrack: float = 0.0,
    auto: bool = True,
    uman: float = 0.0,
    windup: float = 0.0,
    kp: float = 1.0,
    ki: float = 0.0,
    kd: float = 0.0,
    beta: float = 1.0,
    u0: float = 0.0,
    direct_acting: bool = False,
    cv_min: float = 0.0,
    cv_max: float = 100.0,
    hold_when_stopped: bool = False,
    ts: float = DEFAULT_TS,
    tf_ts: float = DEFAULT_TF_TS,
    dt: float = DEFAULT_TS,
    state: dict[str, Any],
) -> float:
    """One scan of listing 1 plus Soft-PLC permit ``running``.

    Mutates *state* with the same keys the builtin equation persists.
    ``ki`` is in 1/s: ``Dui = ki * e * dt`` (equivalent to the paper with
    discretised ``ki_disc = ki * ts`` and ``Tx = dt / ts``).
    """
    dir_sign = -1.0 if direct_acting else 1.0
    dt_ok = dt > 0.0
    tx = _tx(dt, ts)
    tx_safe = tx if tx > 0.0 else 1.0
    use_filter = tf_ts > 0.0
    ki_on = ki != 0.0
    b = 1.0 if not ki_on else float(beta)
    pending = bool(state.get("bumpless_pending", False))
    in_auto = bool(auto) and bool(running)

    a11, a12, a21, a22, b1, b2 = zoh_fy(float(tf_ts), tx_safe)
    yf1 = float(state.get("yf", pv))
    dyf_prev = float(state.get("dyf", 0.0))
    primed = bool(state.get("filter_primed", False))
    yf_start = float(pv) if not primed else yf1
    dyf_start = 0.0 if not primed else dyf_prev
    if dt_ok:
        yf = a11 * yf_start + a12 * dyf_start + b1 * float(pv)
        dyf_filt = a21 * yf_start + a22 * dyf_start + b2 * float(pv)
        dyf_fd = (float(pv) - yf_start) / dt
        dyf = dyf_filt if use_filter else dyf_fd
        filter_primed = True
    else:
        yf = yf_start
        dyf = dyf_start
        filter_primed = primed

    last_ep = float(state.get("last_ep", state.get("last_error", 0.0)))
    up_old = float(state.get("up_old", float(kp) * last_ep))
    ud_old = float(state.get("ud_old", 0.0))
    uff_old = float(state.get("uff_old", 0.0))
    u_old = float(state.get("u_old", state.get("last_cv", u0)))

    ep = dir_sign * (b * float(sp) - yf)
    ei = dir_sign * (float(sp) - yf)
    ud_now = dir_sign * (-float(kd) * dyf)

    if track:
        u_old_run = float(utrack)
        up_old_run = 0.0
        ud_old_run = 0.0
        uff_old_run = 0.0
    elif not ki_on:
        u_old_run = float(u0)
        up_old_run = 0.0
        ud_old_run = 0.0
        uff_old_run = 0.0
    else:
        u_old_run = u_old
        up_old_run = up_old
        ud_old_run = ud_old
        uff_old_run = uff_old

    dup = float(kp) * ep - up_old_run
    dui_raw = float(ki) * ei * dt if (dt_ok and (not pending) and ki_on) else 0.0
    dui = anti_windup(dui_raw, windup)
    dud = (ud_now - ud_old_run) / tx_safe if dt_ok else 0.0
    duff = float(uff) - uff_old_run
    u_auto = u_old_run + dup + dui + dud + duff

    if not running:
        u_unsat = u_old if hold_when_stopped else 0.0
    elif in_auto:
        u_unsat = u_auto
    else:
        u_unsat = float(uman)

    low, high = float(cv_min), float(cv_max)
    if low > high:
        low, high = high, low
    cv = min(max(u_unsat, low), high)

    state["yf"] = yf
    state["dyf"] = dyf
    state["filter_primed"] = filter_primed
    state["bumpless_pending"] = False
    state["u_old"] = cv
    state["up_old"] = float(kp) * ep
    state["ud_old"] = ud_now
    state["uff_old"] = float(uff)
    state["last_cv"] = cv
    state["last_ep"] = ep
    return cv


__all__ = [
    "DEFAULT_TF_TS",
    "DEFAULT_TS",
    "WINDUP_BOTH",
    "WINDUP_LOWER",
    "WINDUP_NONE",
    "WINDUP_UPPER",
    "anti_windup",
    "pid_scan",
    "zoh_fy",
]
