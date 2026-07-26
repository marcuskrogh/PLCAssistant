"""Cascade control: SP_LEVEL → SP_FLOW → CMD_SPEED; process response."""

from __future__ import annotations

import pytest

from plcassistant.io.quality import QualityStatus, is_good
from plcassistant.wedge.control import CascadeConfig, CascadeController
from plcassistant.wedge.process import MockProcess, ProcessConfig, ProcessPort
from plcassistant.wedge.safety import Mode, TripCode
from plcassistant.wedge.skid import OperatorCommand, Skid, SkidConfig


def test_level_loop_produces_sp_flow_when_running():
    ctrl = CascadeController(CascadeConfig(level_kp=40.0, level_ki=0.0, flow_kp=0.0, flow_ki=0.0))
    out = ctrl.step(0.1, lt_tank=0.15, ft_inlet=0.0, sp_level=0.20, running=True)
    assert out.level_error == pytest.approx(0.05)
    assert out.sp_flow > 0.0


def test_flow_loop_produces_cmd_speed_when_running():
    ctrl = CascadeController(
        CascadeConfig(level_kp=40.0, level_ki=0.0, flow_kp=15.0, flow_ki=0.0, sp_flow_max=6.0)
    )
    out = ctrl.step(0.1, lt_tank=0.10, ft_inlet=0.0, sp_level=0.20, running=True)
    assert out.sp_flow > 0.0
    assert out.cmd_speed > 0.0


def test_cascade_holds_sp_flow_when_not_running():
    """STOP / idle: CMD_SPEED=0, hold last SP_FLOW (docs/wedge/03)."""
    ctrl = CascadeController()
    running_out = ctrl.step(0.1, lt_tank=0.10, ft_inlet=0.0, sp_level=0.20, running=True)
    assert running_out.sp_flow > 0.0
    out = ctrl.step(0.1, lt_tank=0.10, ft_inlet=0.0, sp_level=0.20, running=False)
    assert out.cmd_speed == 0.0
    assert out.sp_flow == running_out.sp_flow


def test_process_responds_to_speed_command():
    proc = MockProcess(ProcessConfig(pump_tau=0.01, k_drain=0.0, q_pump_max=8.0))
    proc.set_levels(lt_tank=0.10, lt_res=0.20)
    before = proc.state.lt_tank
    for _ in range(30):
        proc.step(0.1, cmd_speed=100.0)
    assert proc.state.ft_inlet > 0.0
    assert proc.state.lt_tank > before
    assert proc.state.cmd_speed == 100.0


def test_process_dt_zero_holds_ft_inlet_and_levels():
    """dt==0 records CMD_SPEED but must not wipe flow/level/lag state."""
    proc = MockProcess(ProcessConfig(pump_tau=0.5, speed_fb_tau=0.2, k_drain=0.0, q_pump_max=8.0))
    proc.set_levels(lt_tank=0.10, lt_res=0.20)
    for _ in range(20):
        proc.step(0.1, cmd_speed=100.0)
    before = proc.state
    assert before.ft_inlet > 0.0
    after = proc.step(0.0, cmd_speed=50.0)
    assert after.cmd_speed == 50.0
    assert after.ft_inlet == before.ft_inlet
    assert after.lt_tank == before.lt_tank
    assert after.lt_res == before.lt_res
    assert after.sc_pump == before.sc_pump


def test_gravity_drain_lowers_tank_when_pump_off():
    proc = MockProcess(ProcessConfig(k_drain=5.0, q_pump_max=0.0))
    proc.set_levels(lt_tank=0.30, lt_res=0.15)
    before = proc.state.lt_tank
    for _ in range(60):
        proc.step(0.1, cmd_speed=0.0)
    assert proc.state.lt_tank < before


def test_process_conserves_inventory_near_clamps():
    """Inventory limiting prevents clamp-induced mass create/destroy."""
    proc = MockProcess(
        ProcessConfig(
            pump_tau=0.0,
            k_drain=20.0,
            q_pump_max=20.0,
            a_tank=0.05,
            a_res=0.10,
            h_tank_max=0.40,
            h_res_max=0.30,
        )
    )
    proc.set_levels(lt_tank=0.39, lt_res=0.01)

    def inventory_m3() -> float:
        s = proc.state
        return s.lt_tank * proc.config.a_tank + s.lt_res * proc.config.a_res

    before = inventory_m3()
    for _ in range(100):
        proc.step(0.1, cmd_speed=100.0)
    after = inventory_m3()
    assert after == pytest.approx(before, rel=1e-9, abs=1e-12)


def test_mock_process_satisfies_process_port():
    proc = MockProcess()
    assert isinstance(proc, ProcessPort)


def test_skid_cascade_when_running_produces_sp_flow_and_speed():
    skid = Skid(
        SkidConfig(
            cascade=CascadeConfig(level_kp=50.0, level_ki=4.0, flow_kp=15.0, flow_ki=2.0),
            process=ProcessConfig(pump_tau=0.2, k_drain=3.0),
            sp_level=0.22,
        )
    )
    skid.process.set_levels(lt_tank=0.12, lt_res=0.20)
    snap = skid.step(0.1, command=OperatorCommand.START)
    assert snap.mode is Mode.RUNNING

    for _ in range(25):
        snap = skid.step(0.1)

    assert snap.sp_flow > 0.0
    assert snap.cmd_speed > 0.0
    assert snap.ft_inlet is not None and snap.ft_inlet > 0.0
    assert is_good(snap.lt_tank_quality) is True
    assert snap.lt_tank_quality.status is QualityStatus.GOOD


def test_skid_stop_zeros_speed_and_holds_sp_flow():
    skid = Skid()
    skid.process.set_levels(lt_tank=0.15, lt_res=0.20)
    skid.step(0.1, command=OperatorCommand.START)
    for _ in range(5):
        skid.step(0.1)
    before = skid.last
    assert before is not None
    snap = skid.step(0.1, command=OperatorCommand.STOP)
    assert snap.mode is Mode.STOP
    assert snap.cmd_speed == 0.0
    assert snap.cascade.cmd_speed == 0.0
    assert snap.cascade.sp_flow == before.sp_flow


def test_skid_measurement_view_shared_on_override():
    """Safety and snapshot use the same override/LOS view (not raw live)."""
    skid = Skid()
    skid.process.set_levels(lt_tank=0.15, lt_res=0.20)
    skid.step(0.1, command=OperatorCommand.START)
    skid.set_signal_override(lt_tank=None)
    snap = skid.step(0.1)
    assert snap.lt_tank is None
    assert is_good(snap.lt_tank_quality) is False
    assert snap.measurement.lt_tank is None
    assert TripCode.LOS_LT_TANK in snap.trip_codes
    assert snap.cmd_speed == 0.0


def test_skid_measurement_view_nan_is_bad_and_trips_los():
    """Non-finite override maps to BAD quality, None PV, LOS trip."""
    skid = Skid()
    skid.process.set_levels(lt_tank=0.15, lt_res=0.20)
    skid.step(0.1, command=OperatorCommand.START)
    skid.set_signal_override(lt_tank=float("nan"))
    snap = skid.step(0.1)
    assert is_good(snap.lt_tank_quality) is False
    assert snap.lt_tank_quality.status is QualityStatus.BAD
    assert snap.lt_tank is None
    assert snap.measurement.lt_tank is None
    assert is_good(snap.measurement.lt_tank_quality) is False
    assert TripCode.LOS_LT_TANK in snap.trip_codes
    assert snap.mode is Mode.TRIPPED
    assert snap.cmd_speed == 0.0
