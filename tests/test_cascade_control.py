"""Cascade control: SP_LEVEL → SP_FLOW → CMD_SPEED; process response."""

from __future__ import annotations

import pytest

from plcassistant.wedge.control import CascadeConfig, CascadeController
from plcassistant.wedge.process import MockProcess, ProcessConfig
from plcassistant.wedge.safety import Mode
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


def test_cascade_idle_when_not_running():
    ctrl = CascadeController()
    ctrl.step(0.1, lt_tank=0.10, ft_inlet=0.0, sp_level=0.20, running=True)
    out = ctrl.step(0.1, lt_tank=0.10, ft_inlet=0.0, sp_level=0.20, running=False)
    assert out.cmd_speed == 0.0
    assert out.sp_flow == 0.0


def test_process_responds_to_speed_command():
    proc = MockProcess(ProcessConfig(pump_tau=0.01, k_drain=0.0, q_pump_max=8.0))
    proc.set_levels(lt_tank=0.10, lt_res=0.20)
    before = proc.state.lt_tank
    for _ in range(30):
        proc.step(0.1, cmd_speed=100.0)
    assert proc.state.ft_inlet > 0.0
    assert proc.state.lt_tank > before
    assert proc.state.cmd_speed == 100.0


def test_gravity_drain_lowers_tank_when_pump_off():
    proc = MockProcess(ProcessConfig(k_drain=5.0, q_pump_max=0.0))
    proc.set_levels(lt_tank=0.30, lt_res=0.15)
    before = proc.state.lt_tank
    for _ in range(60):
        proc.step(0.1, cmd_speed=0.0)
    assert proc.state.lt_tank < before


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
    assert snap.ft_inlet > 0.0


def test_skid_stop_zeros_speed_and_cascade_idle():
    skid = Skid()
    skid.process.set_levels(lt_tank=0.15, lt_res=0.20)
    skid.step(0.1, command=OperatorCommand.START)
    for _ in range(5):
        skid.step(0.1)
    snap = skid.step(0.1, command=OperatorCommand.STOP)
    assert snap.mode is Mode.STOP
    assert snap.cmd_speed == 0.0
    assert snap.cascade.cmd_speed == 0.0
