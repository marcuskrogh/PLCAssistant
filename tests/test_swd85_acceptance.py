"""SWD-85 control semantics acceptance — docs/control/05-acceptance.md."""

from __future__ import annotations

import pytest

from plcassistant.control import (
    PHASE_ORDER,
    ScanConfig,
    ScanPhase,
    ScanShell,
    assert_phase_order,
)
from plcassistant.wedge.control import CascadeConfig, CascadeController
from plcassistant.wedge.process import ProcessConfig
from plcassistant.wedge.safety import Mode, TripCode
from plcassistant.wedge.skid import LimitConfig, OperatorCommand, Skid, SkidConfig


def test_scan_shell_phase_order_locked():
    shell = ScanShell(ScanConfig(scan_period_s=0.1))
    seen: list[ScanPhase] = []

    def track(phase: ScanPhase):
        def _cb() -> None:
            seen.append(phase)

        return _cb

    diag = shell.run(
        0.05,
        on_in=track(ScanPhase.IN),
        on_safety=track(ScanPhase.SAFETY),
        on_control=track(ScanPhase.CONTROL),
        on_out=track(ScanPhase.OUT),
    )
    assert tuple(seen) == PHASE_ORDER
    assert_phase_order(diag.last_phases)
    assert diag.last_dt_s == 0.05
    assert diag.scan_count == 1
    assert ScanConfig().scan_period_s == 0.1


def test_scan_shell_overrun_counter():
    shell = ScanShell(ScanConfig(scan_period_s=0.1))
    shell.run(
        0.1,
        on_in=lambda: None,
        on_safety=lambda: None,
        on_control=lambda: None,
        on_out=lambda: None,
        duration_s=0.25,
    )
    assert shell.diagnostics.overrun_count == 1
    shell.run(
        0.1,
        on_in=lambda: None,
        on_safety=lambda: None,
        on_control=lambda: None,
        on_out=lambda: None,
        duration_s=0.05,
    )
    assert shell.diagnostics.overrun_count == 1
    assert shell.diagnostics.scan_count == 2


def test_skid_exposes_phase_order_each_scan():
    skid = Skid()
    snap = skid.step(0.1)
    assert snap.scan_phases == PHASE_ORDER
    assert snap.scan_diagnostics is not None
    assert snap.scan_diagnostics.last_dt_s == 0.1


def test_dt_injectable_negative_rejected():
    ctrl = CascadeController()
    with pytest.raises(ValueError):
        ctrl.step(-0.1, lt_tank=0.1, ft_inlet=0.0, sp_level=0.2, running=True)
    skid = Skid()
    with pytest.raises(ValueError):
        skid.step(-0.01)


def test_trip_same_scan_forces_cmd_speed_zero():
    """Safety before control: trip on scan N zeros CV on scan N."""
    skid = Skid(
        SkidConfig(
            cascade=CascadeConfig(level_kp=50.0, level_ki=0.0, flow_kp=20.0, flow_ki=0.0),
            process=ProcessConfig(
                pump_tau=0.05,
                q_pump_max=8.0,
                k_drain=1.0,
                initial_h_tank=0.15,
                initial_h_res=0.20,
            ),
            limits=LimitConfig(lim_level_hh=0.36, lim_res_ll=0.05),
            sp_level=0.25,
        )
    )
    assert skid.step(0.1, OperatorCommand.START).mode is Mode.RUNNING
    for _ in range(20):
        skid.step(0.1)
    assert skid.last is not None
    assert skid.last.cmd_speed > 0.0
    assert skid.last.mode is Mode.RUNNING

    skid.force_lt_tank_bad(True)
    tripped = skid.step(0.1)
    assert tripped.mode is Mode.TRIPPED
    assert TripCode.LOS_LT_TANK in tripped.trip_codes
    assert tripped.cmd_speed == 0.0
    assert tripped.safety.pump_permit is False


def test_anti_windup_integral_does_not_grow_unbounded_at_clamp():
    ctrl = CascadeController(
        CascadeConfig(
            level_kp=1000.0,
            level_ki=100.0,
            flow_kp=0.0,
            flow_ki=0.0,
            sp_flow_max=6.0,
        )
    )
    # Huge positive error → SP_FLOW saturated high
    for _ in range(50):
        out = ctrl.step(0.1, lt_tank=0.0, ft_inlet=0.0, sp_level=1.0, running=True)
        assert out.sp_flow == 6.0
    i_after = ctrl.level_integral
    for _ in range(50):
        ctrl.step(0.1, lt_tank=0.0, ft_inlet=0.0, sp_level=1.0, running=True)
    assert ctrl.level_integral == pytest.approx(i_after)


def test_bumpless_start_limits_first_cmd_jump():
    ctrl = CascadeController(
        CascadeConfig(level_kp=40.0, level_ki=5.0, flow_kp=12.0, flow_ki=2.0)
    )
    # Idle with held SP_FLOW from a prior run
    ctrl.step(0.1, lt_tank=0.10, ft_inlet=0.0, sp_level=0.20, running=True)
    held = ctrl.last.sp_flow
    ctrl.step(0.1, lt_tank=0.10, ft_inlet=0.0, sp_level=0.20, running=False)
    assert ctrl.last.cmd_speed == 0.0
    assert ctrl.last.sp_flow == held

    ctrl.prepare_bumpless(
        lt_tank=0.10,
        ft_inlet=0.0,
        sp_level=0.20,
        target_sp_flow=held,
        target_cmd_speed=0.0,
    )
    first = ctrl.step(0.1, lt_tank=0.10, ft_inlet=0.0, sp_level=0.20, running=True)
    assert first.sp_flow == pytest.approx(held, abs=1e-9)
    assert first.cmd_speed == pytest.approx(0.0, abs=1e-6)


def test_skid_bumpless_on_start_edge():
    skid = Skid(
        SkidConfig(
            cascade=CascadeConfig(level_kp=80.0, level_ki=20.0, flow_kp=25.0, flow_ki=10.0),
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
    first = skid.step(0.1, OperatorCommand.START)
    assert first.mode is Mode.RUNNING
    # Without bumpless, empty I + large error would slam toward clamp immediately;
    # with bumpless, first CMD stays near 0.
    assert first.cmd_speed < 30.0


def test_td_stubs_default_zero():
    cfg = CascadeConfig()
    assert cfg.level_td == 0.0
    assert cfg.flow_td == 0.0


def test_skid_snapshot_diagnostics_are_copied():
    """Prior snapshots must not share mutable ScanShell.diagnostics."""
    skid = Skid()
    s1 = skid.step(0.1)
    assert s1.scan_diagnostics is not None
    count1 = s1.scan_diagnostics.scan_count
    s2 = skid.step(0.1)
    assert s2.scan_diagnostics is not None
    assert s1.scan_diagnostics is not s2.scan_diagnostics
    assert s1.scan_diagnostics is not skid.scan_shell.diagnostics
    assert s1.scan_diagnostics.scan_count == count1
    assert s2.scan_diagnostics.scan_count == count1 + 1


def test_dt_zero_holds_integrals_and_recomputes_p():
    ctrl = CascadeController(
        CascadeConfig(level_kp=10.0, level_ki=5.0, flow_kp=0.0, flow_ki=0.0)
    )
    out1 = ctrl.step(0.1, lt_tank=0.10, ft_inlet=0.0, sp_level=0.20, running=True)
    i1 = ctrl.level_integral
    out0 = ctrl.step(0.0, lt_tank=0.10, ft_inlet=0.0, sp_level=0.20, running=True)
    assert ctrl.level_integral == pytest.approx(i1)
    # Same error → same P+I output when dt==0 (no I advance)
    assert out0.sp_flow == pytest.approx(out1.sp_flow)


def test_skid_duration_s_overrun_counter():
    skid = Skid(SkidConfig(scan=ScanConfig(scan_period_s=0.1)))
    snap = skid.step(0.1, duration_s=0.25)
    assert snap.scan_diagnostics is not None
    assert snap.scan_diagnostics.overrun_count == 1
