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


def test_unit_legacy_cascade_without_tf_ts_bypasses_filter() -> None:
    from plcassistant.surface.schema import program_from_dict

    raw = {
        "version": "1.0",
        "name": "Tank",
        "instances": {
            "level_pi": {
                "template_id": "level_pi",
                "library": "builtin",
                "params": {"kp": 40.0, "ki": 5.0, "cv_min": 0.0, "cv_max": 6.0},
            },
            "flow_pi": {
                "template_id": "flow_pi",
                "library": "builtin",
                "params": {"kp": 12.0, "ki": 2.0, "cv_min": 0.0, "cv_max": 100.0},
            },
        },
        "wires": [
            {
                "src_instance": "level_pi",
                "src_pin": "cv",
                "dst_instance": "flow_pi",
                "dst_pin": "sp",
            }
        ],
        "execution_order": ["level_pi", "flow_pi"],
    }
    prog = program_from_dict(raw)
    assert prog.instances["level_pi"].params["tf_ts"] == pytest.approx(0.0)
    assert prog.instances["flow_pi"].params["tf_ts"] == pytest.approx(0.0)


def test_unit_repair_forces_cascade_tf_ts_zero() -> None:
    from plcassistant.surface.builtin import (
        CASCADE_CMD_SPEED_MAX,
        CASCADE_SP_FLOW_MAX,
        PID_TEMPLATE_ID,
    )
    from plcassistant.surface.model import BlockInstance, Program
    from plcassistant.surface.schema import repair_cascade_pid_limits

    prog = Program(
        name="Tank",
        instances={
            "level_pi": BlockInstance(
                instance_id="level_pi",
                template_id=PID_TEMPLATE_ID,
                library="builtin",
                params={
                    "kp": 40.0,
                    "ki": 5.0,
                    "cv_min": 0.0,
                    "cv_max": CASCADE_SP_FLOW_MAX,
                    "tf_ts": 10.0,
                },
            ),
            "flow_pi": BlockInstance(
                instance_id="flow_pi",
                template_id=PID_TEMPLATE_ID,
                library="builtin",
                params={
                    "kp": 12.0,
                    "ki": 2.0,
                    "cv_min": 0.0,
                    "cv_max": CASCADE_CMD_SPEED_MAX,
                },
            ),
        },
        execution_order=["level_pi", "flow_pi"],
    )
    assert repair_cascade_pid_limits(prog) is True
    assert prog.instances["level_pi"].params["tf_ts"] == pytest.approx(0.0)
    assert prog.instances["flow_pi"].params["tf_ts"] == pytest.approx(0.0)
    assert repair_cascade_pid_limits(prog) is False


def test_system_start_seeds_ifac_bumpless_state() -> None:
    from plcassistant.wedge.control import CascadeConfig
    from plcassistant.wedge.process import ProcessConfig
    from plcassistant.wedge.safety import Mode
    from plcassistant.wedge.skid import OperatorCommand, Skid, SkidConfig

    skid = Skid(
        SkidConfig(
            cascade=CascadeConfig(
                level_kp=80.0, level_ki=20.0, flow_kp=25.0, flow_ki=10.0
            ),
            process=ProcessConfig(
                pump_tau=0.5,
                q_pump_max=8.0,
                k_drain=2.0,
                initial_h_tank=0.10,
                initial_h_res=0.20,
            ),
            sp_level=0.30,
        )
    )
    rt = skid.block_runtime
    assert rt is not None
    skid._prepare_bumpless_blocks(lt_tank=0.10, ft_inlet=0.0)
    level = rt.state["level_pi"]
    flow = rt.state["flow_pi"]
    assert level["bumpless_pending"] is True
    assert flow["bumpless_pending"] is True
    assert level["u_old"] == pytest.approx(0.0)
    assert flow["u_old"] == pytest.approx(0.0)
    assert "up_old" in level and "up_old" in flow
    assert level["yf"] == pytest.approx(0.10)
    assert flow["yf"] == pytest.approx(0.0)
    assert level["filter_primed"] is True
    assert flow["filter_primed"] is True
    assert "integral" not in level
    assert "integral" not in flow

    first = skid.step(0.1, OperatorCommand.START)
    assert first.mode is Mode.RUNNING
    assert first.sp_flow == pytest.approx(0.0, abs=1e-9)
    assert first.cmd_speed == pytest.approx(0.0, abs=1e-6)
    assert rt.state["level_pi"]["bumpless_pending"] is False
    assert rt.state["flow_pi"]["bumpless_pending"] is False


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
