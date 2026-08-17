"""SWD-367: IFAC 2024 incremental PID reference (listings 1–4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from plcassistant.control.pid import (
    WINDUP_BOTH,
    WINDUP_LOWER,
    WINDUP_UPPER,
    pid_scan,
    zoh_fy,
)
from plcassistant.surface.builtin import (
    PID_EQUATION,
    PID_EQUATION_HYBRID,
    is_factory_pid_equation,
    pid_default_params,
    pid_template,
)
from plcassistant.surface.equations import evaluate_equation

ROOT = Path(__file__).resolve().parents[1]


def _pins(**overrides: object) -> dict[str, object]:
    pins: dict[str, object] = {
        "pv": 0.0,
        "sp": 0.0,
        "running": True,
        "uff": 0.0,
        "track": False,
        "utrack": 0.0,
        "auto": True,
        "uman": 0.0,
        "windup": 0.0,
    }
    pins.update(overrides)
    return pins


def _eval_eq(params: dict, pins: dict, state: dict, dt: float = 0.1) -> float:
    tmpl = pid_template()
    out = evaluate_equation(PID_EQUATION, tmpl, pins, params, state, dt)
    return float(out["cv"])


def _eval_py(params: dict, pins: dict, state: dict, dt: float = 0.1) -> float:
    return pid_scan(
        pv=float(pins["pv"]),
        sp=float(pins["sp"]),
        running=bool(pins["running"]),
        uff=float(pins.get("uff", 0.0)),
        track=bool(pins.get("track", False)),
        utrack=float(pins.get("utrack", 0.0)),
        auto=bool(pins.get("auto", True)),
        uman=float(pins.get("uman", 0.0)),
        windup=float(pins.get("windup", 0.0)),
        kp=float(params["kp"]),
        ki=float(params["ki"]),
        kd=float(params["kd"]),
        beta=float(params.get("beta", 1.0)),
        u0=float(params.get("u0", 0.0)),
        direct_acting=bool(params.get("direct_acting", False)),
        cv_min=float(params["cv_min"]),
        cv_max=float(params["cv_max"]),
        hold_when_stopped=bool(params.get("hold_when_stopped", False)),
        ts=float(params.get("ts", 0.1)),
        tf_ts=float(params.get("tf_ts", 10.0)),
        dt=dt,
        state=state,
    )


def test_unit_hybrid_equation_is_still_factory() -> None:
    assert is_factory_pid_equation(PID_EQUATION_HYBRID)
    assert is_factory_pid_equation(PID_EQUATION)


def test_unit_zoh_fy_bypass_is_identity() -> None:
    a11, a12, a21, a22, b1, b2 = zoh_fy(0.0, 1.0)
    assert (a11, a12, a21, a22, b1, b2) == (0.0, 0.0, 0.0, 0.0, 1.0, 0.0)


def test_unit_zoh_fy_paper_tx_one() -> None:
    import math

    tf_ts, tx = 10.0, 1.0
    h1 = tx / tf_ts
    h2 = math.exp(-h1)
    h3 = h1 * h2
    h4 = h3 / tf_ts
    a11, a12, a21, a22, b1, b2 = zoh_fy(tf_ts, tx)
    assert a11 == pytest.approx(h2 + h3)
    assert a12 == pytest.approx(h2)
    assert a21 == pytest.approx(-h4)
    assert a22 == pytest.approx(h2 - h3)
    assert b1 == pytest.approx(1.0 - h2 - h3)
    assert b2 == pytest.approx(h4)


def test_unit_equation_matches_python_reference_trace() -> None:
    params = pid_default_params()
    params.update({"kp": 2.0, "ki": 1.0, "kd": 0.5, "cv_min": -50.0, "cv_max": 50.0, "tf_ts": 10.0})
    state_eq: dict = {}
    state_py: dict = {}
    samples = [
        (0.0, 0.0, True, 0.0, True, 0.0, 0.0, 0.1),
        (1.0, 0.2, True, 0.0, True, 0.0, 0.0, 0.1),
        (1.0, 0.4, True, 0.0, True, 0.0, 0.0, 0.12),
        (0.5, 0.4, True, 3.0, True, 0.0, 0.0, 0.1),
        (0.5, 0.4, True, 3.0, False, 8.0, 0.0, 0.1),
        (0.5, 0.4, False, 0.0, True, 0.0, 0.0, 0.1),
        (0.5, 0.4, True, 0.0, True, 0.0, 3.0, 0.1),
    ]
    for sp, pv, running, uff, auto, uman, windup, dt in samples:
        pins = _pins(sp=sp, pv=pv, running=running, uff=uff, auto=auto, uman=uman, windup=windup)
        cv_eq = _eval_eq(params, pins, state_eq, dt)
        cv_py = _eval_py(params, pins, state_py, dt)
        assert cv_eq == pytest.approx(cv_py, abs=1e-9)


def test_unit_output_manual_follows_uman() -> None:
    params = pid_default_params()
    params.update({"kp": 10.0, "ki": 5.0, "kd": 0.0, "cv_min": 0.0, "cv_max": 100.0})
    cv = _eval_eq(params, _pins(pv=0.0, sp=10.0, auto=False, uman=33.0), {}, 0.1)
    assert cv == pytest.approx(33.0)


def test_unit_external_windup_lower_blocks_negative_i() -> None:
    params = pid_default_params()
    params.update(
        {
            "kp": 0.0,
            "ki": 10.0,
            "kd": 0.0,
            "tf_ts": 0.0,
            "cv_min": -50.0,
            "cv_max": 50.0,
        }
    )
    state: dict = {}
    pins = _pins(pv=10.0, sp=0.0, windup=float(WINDUP_LOWER))
    cv = 0.0
    for _ in range(5):
        cv = _eval_eq(params, pins, state, 0.1)
    assert cv == pytest.approx(0.0)
    pins_up = _pins(pv=0.0, sp=10.0, windup=float(WINDUP_LOWER))
    cv = _eval_eq(params, pins_up, state, 0.1)
    assert cv > 0.0


def test_unit_external_windup_upper_blocks_positive_i() -> None:
    params = pid_default_params()
    params.update({"kp": 0.0, "ki": 10.0, "kd": 0.0, "tf_ts": 0.0, "cv_min": -50.0, "cv_max": 50.0})
    cv = _eval_eq(params, _pins(pv=0.0, sp=10.0, windup=float(WINDUP_UPPER)), {}, 0.1)
    assert cv == pytest.approx(0.0)


def test_unit_filter_lags_measurement_step() -> None:
    params = pid_default_params()
    params.update({"kp": 1.0, "ki": 0.0, "kd": 0.0, "u0": 0.0, "tf_ts": 10.0, "cv_min": -50.0, "cv_max": 50.0})
    state: dict = {}
    _eval_eq(params, _pins(pv=0.0, sp=0.0), state, 0.1)
    cv_step = _eval_eq(params, _pins(pv=10.0, sp=0.0), state, 0.1)
    # Reverse P on lagged yf: |cv| < kp * 10 on the first filtered step.
    assert abs(cv_step) < 10.0
    assert abs(cv_step) > 0.0


def test_unit_tx_scales_derivative() -> None:
    params = pid_default_params()
    params.update(
        {
            "kp": 0.0,
            "ki": 0.1,
            "kd": 2.0,
            "tf_ts": 0.0,
            "cv_min": -100.0,
            "cv_max": 100.0,
        }
    )
    settle = _pins(pv=0.0, sp=0.0)
    state_fast: dict = {}
    state_slow: dict = {}
    for _ in range(3):
        _eval_eq(params, settle, state_fast, 0.1)
        _eval_eq(params, settle, state_slow, 0.1)
    step = _pins(pv=1.0, sp=0.0)
    cv_fast = _eval_eq(params, step, state_fast, 0.1)
    cv_slow = _eval_eq(params, step, state_slow, 0.2)
    assert cv_fast != pytest.approx(cv_slow, abs=1e-9)


def test_unit_track_adds_increments_to_utrack() -> None:
    params = pid_default_params()
    params.update({"kp": 0.0, "ki": 0.0, "kd": 0.0, "u0": 0.0, "cv_min": 0.0, "cv_max": 100.0})
    cv = _eval_eq(params, _pins(track=True, utrack=40.0, uff=5.0), {}, 0.1)
    assert cv == pytest.approx(45.0)


def test_unit_windup_both_freezes_i() -> None:
    params = pid_default_params()
    params.update({"kp": 0.0, "ki": 8.0, "kd": 0.0, "tf_ts": 0.0, "cv_min": -20.0, "cv_max": 20.0})
    cv = _eval_eq(params, _pins(pv=0.0, sp=5.0, windup=float(WINDUP_BOTH)), {}, 0.1)
    assert cv == pytest.approx(0.0)


def test_unit_iterate_tracks_swd367() -> None:
    text = Path("docs/ITERATE.md").read_text(encoding="utf-8")
    assert "SWD-367" in text
    assert "10.1016/j.ifacol.2024.08.090" in text
    assert "tf_ts" in text


def test_system_app_version_is_0_1_57() -> None:
    assert 'version: "0.1.57"' in (ROOT / "plc_assistant" / "config.yaml").read_text(
        encoding="utf-8"
    )
    manifest = (ROOT / "custom_components" / "plcassistant" / "manifest.json").read_text(
        encoding="utf-8"
    )
    assert '"0.1.57"' in manifest
    docker = (ROOT / "plc_assistant" / "Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.57" in docker
    dual = ROOT / "plc_assistant" / "custom_components" / "plcassistant" / "manifest.json"
    assert '"0.1.57"' in dual.read_text(encoding="utf-8")
