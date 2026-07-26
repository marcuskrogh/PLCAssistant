"""Mock acceptance scenarios — docs/wedge/06-mock-acceptance.md (SWD-89).

Scenario ids A1–F match the runnable checklist in that document.
"""

from __future__ import annotations

import pytest

from plcassistant.io.quality import QualityStatus, ReasonCode, is_good
from plcassistant.wedge.control import CascadeConfig
from plcassistant.wedge.process import MockProcess, ProcessConfig
from plcassistant.wedge.safety import Mode, TripCode
from plcassistant.wedge.skid import LimitConfig, OperatorCommand, Skid, SkidConfig


def _clean_skid(**kwargs) -> Skid:
    cfg = SkidConfig(
        cascade=CascadeConfig(level_kp=50.0, level_ki=4.0, flow_kp=15.0, flow_ki=2.0),
        process=ProcessConfig(
            pump_tau=0.2,
            q_pump_max=8.0,
            k_drain=3.5,
            initial_h_tank=0.15,
            initial_h_res=0.20,
        ),
        limits=LimitConfig(lim_level_hh=0.36, lim_res_ll=0.05),
        sp_level=0.20,
        **kwargs,
    )
    return Skid(cfg)


def _start_running(skid: Skid) -> None:
    snap = skid.step(0.1, command=OperatorCommand.START)
    assert snap.mode is Mode.RUNNING, snap


# --- A — Start / Stop -------------------------------------------------------


def test_A1_start_blocked_when_not_permissive():
    """A1 — Start blocked when not permissive (latched / BAD quality)."""
    skid = _clean_skid()
    skid.force_quality("LT_TANK", QualityStatus.BAD, ReasonCode.FAULT)
    snap = skid.step(0.1, command=OperatorCommand.START)
    assert snap.perm_ok is False
    assert snap.mode in (Mode.STOP, Mode.TRIPPED)
    assert snap.cmd_speed == 0.0
    assert snap.mode is Mode.TRIPPED
    assert TripCode.LOS_LT_TANK in snap.trip_codes
    assert is_good(snap.lt_tank_quality) is False
    assert snap.lt_tank_quality.status is QualityStatus.BAD
    assert snap.lt_tank is None


def test_A2_clean_start():
    """A2 — Clean Start → MODE=RUNNING, CMD_SPEED leaves 0, FT_INLET rises."""
    skid = _clean_skid()
    skid.process.set_levels(lt_tank=0.12, lt_res=0.20)
    snap = skid.step(0.1, command=OperatorCommand.START)
    assert snap.mode is Mode.RUNNING

    for _ in range(20):
        snap = skid.step(0.1)

    assert snap.cmd_speed > 0.0
    assert snap.ft_inlet is not None and snap.ft_inlet > 0.0


def test_A3_stop_always_works():
    """A3 — From RUNNING, HMI_STOP → MODE=STOP, CMD_SPEED=0, no trip latch."""
    skid = _clean_skid()
    _start_running(skid)
    for _ in range(5):
        skid.step(0.1)

    before = skid.last
    assert before is not None and before.sp_flow > 0.0
    snap = skid.step(0.1, command=OperatorCommand.STOP)
    assert snap.mode is Mode.STOP
    assert snap.cmd_speed == 0.0
    assert snap.trip_active is False
    assert snap.sp_flow == before.sp_flow  # hold last SP_FLOW on STOP


# --- B — Cascade holds / responds -------------------------------------------


def test_B1_level_step_up():
    """B1 — Raise SP_LEVEL → SP_FLOW and CMD_SPEED rise; FT_INLET up; LT_TANK rises."""
    skid = _clean_skid()
    skid.process.set_levels(lt_tank=0.15, lt_res=0.20)
    skid.sp_level = 0.15
    _start_running(skid)
    for _ in range(40):
        skid.step(0.1)

    before = skid.last
    assert before is not None
    skid.sp_level = 0.22

    snap = None
    for _ in range(50):
        snap = skid.step(0.1)

    assert snap is not None
    assert snap.sp_flow > before.sp_flow
    assert snap.cmd_speed > before.cmd_speed
    assert snap.ft_inlet is not None and before.ft_inlet is not None
    assert snap.ft_inlet > before.ft_inlet
    assert snap.lt_tank is not None and before.lt_tank is not None
    assert snap.lt_tank > before.lt_tank - 0.01


def test_B2_level_step_down():
    """B2 — Lower SP_LEVEL → SP_FLOW and CMD_SPEED decrease; tank trends down."""
    skid = _clean_skid()
    skid.process.set_levels(lt_tank=0.18, lt_res=0.18)
    skid.sp_level = 0.22
    _start_running(skid)
    for _ in range(40):
        skid.step(0.1)

    high = skid.last
    assert high is not None
    skid.sp_level = 0.12

    snap = None
    for _ in range(60):
        snap = skid.step(0.1)

    assert snap is not None
    assert snap.sp_flow < high.sp_flow
    assert snap.cmd_speed < high.cmd_speed
    assert snap.lt_tank is not None and high.lt_tank is not None
    assert snap.lt_tank < high.lt_tank + 0.02


# --- C — High tank level trip -----------------------------------------------


def test_C_high_tank_trip_latch_reset():
    """C — HH_TANK trip, latch, Start blocked, Reset→STOP, Start again."""
    skid = _clean_skid()
    _start_running(skid)

    skid.process.set_levels(lt_tank=0.37)
    tripped = skid.step(0.1)
    assert TripCode.HH_TANK in tripped.trip_codes
    assert tripped.mode is Mode.TRIPPED
    assert tripped.cmd_speed == 0.0
    assert tripped.trip_active is True

    # Start while still high / latched → rejected
    blocked = skid.step(0.1, command=OperatorCommand.START)
    assert blocked.perm_ok is False
    assert blocked.mode is Mode.TRIPPED

    # Return below HH; Reset → STOP
    skid.process.set_levels(lt_tank=0.15)
    still = skid.step(0.1)
    assert still.trip_active is True

    reset = skid.step(0.1, command=OperatorCommand.RESET)
    assert reset.trip_active is False
    assert reset.mode is Mode.STOP

    restarted = skid.step(0.1, command=OperatorCommand.START)
    assert restarted.mode is Mode.RUNNING


# --- D — Low reservoir trip -------------------------------------------------


def test_D_low_reservoir_trip_latch_reset():
    """D — LL_RES latched; reset while low fails; restore+Reset → Start works."""
    skid = _clean_skid()
    _start_running(skid)

    skid.process.set_levels(lt_res=0.04)
    tripped = skid.step(0.1)
    assert TripCode.LL_RES in tripped.trip_codes
    assert tripped.mode is Mode.TRIPPED
    assert tripped.cmd_speed == 0.0

    # Reset while still low → trip remains
    still = skid.step(0.1, command=OperatorCommand.RESET)
    assert still.trip_active is True
    assert still.mode is Mode.TRIPPED

    skid.process.set_levels(lt_res=0.20)
    reset = skid.step(0.1, command=OperatorCommand.RESET)
    assert reset.mode is Mode.STOP
    assert reset.trip_active is False

    assert skid.step(0.1, command=OperatorCommand.START).mode is Mode.RUNNING


# --- E — Loss-of-signal trips -----------------------------------------------


def test_E1_loss_of_signal_lt_tank():
    """E1 — force_quality LT_TANK BAD → LOS_LT_TANK; clear alone keeps latch; Reset+Start."""
    skid = _clean_skid()
    _start_running(skid)

    skid.force_quality("LT_TANK", QualityStatus.BAD, ReasonCode.FAULT)
    tripped = skid.step(0.1)
    assert TripCode.LOS_LT_TANK in tripped.trip_codes
    assert tripped.mode is Mode.TRIPPED
    assert tripped.cmd_speed == 0.0
    assert is_good(tripped.lt_tank_quality) is False
    assert tripped.lt_tank is None

    skid.force_quality("LT_TANK", QualityStatus.GOOD)
    assert skid.step(0.1).trip_active is True

    skid.step(0.1, command=OperatorCommand.RESET)
    assert skid.step(0.1, command=OperatorCommand.START).mode is Mode.RUNNING


def test_E2_loss_of_signal_lt_res():
    """E2 — force_LT_RES_BAD wrapper → LOS_LT_RES; clear alone keeps latch; Reset+Start."""
    skid = _clean_skid()
    _start_running(skid)

    skid.force_lt_res_bad(True)
    tripped = skid.step(0.1)
    assert TripCode.LOS_LT_RES in tripped.trip_codes
    assert tripped.mode is Mode.TRIPPED
    assert tripped.cmd_speed == 0.0
    assert is_good(tripped.lt_res_quality) is False
    assert tripped.lt_res is None

    skid.force_lt_res_bad(False)
    assert skid.step(0.1).trip_active is True

    skid.step(0.1, command=OperatorCommand.RESET)
    assert skid.step(0.1, command=OperatorCommand.START).mode is Mode.RUNNING


def test_E3_loss_of_signal_ft_inlet():
    """E3 — force_FT_INLET_BAD wrapper → LOS_FT_INLET; clear alone keeps latch; Reset+Start."""
    skid = _clean_skid()
    _start_running(skid)

    skid.force_ft_inlet_bad(True)
    tripped = skid.step(0.1)
    assert TripCode.LOS_FT_INLET in tripped.trip_codes
    assert tripped.mode is Mode.TRIPPED
    assert tripped.cmd_speed == 0.0
    assert is_good(tripped.ft_inlet_quality) is False
    assert tripped.ft_inlet is None

    skid.force_ft_inlet_bad(False)
    assert skid.step(0.1).trip_active is True

    skid.step(0.1, command=OperatorCommand.RESET)
    assert skid.step(0.1, command=OperatorCommand.START).mode is Mode.RUNNING


# --- F — Latch discipline ---------------------------------------------------


def test_F_latch_discipline_no_auto_restart_after_reset():
    """F — Reset alone does not auto-restart; Stop zeros speed while latched."""
    skid = _clean_skid()
    _start_running(skid)
    skid.process.set_levels(lt_tank=0.37)
    skid.step(0.1)
    assert skid.last and skid.last.mode is Mode.TRIPPED

    # Stop path while tripped still keeps CMD_SPEED at 0; latch remains
    stopped = skid.step(0.1, command=OperatorCommand.STOP)
    assert stopped.cmd_speed == 0.0
    assert stopped.trip_active is True

    skid.process.set_levels(lt_tank=0.15)
    reset = skid.step(0.1, command=OperatorCommand.RESET)
    assert reset.mode is Mode.STOP
    assert reset.trip_active is False
    assert reset.cmd_speed == 0.0
    # No auto-restart
    idle = skid.step(0.1)
    assert idle.mode is Mode.STOP


def test_multi_latch_reset_requires_all_conditions_clear():
    """HH+LL both latched; clear only one → both codes remain; all clear → Reset."""
    skid = _clean_skid()
    _start_running(skid)

    skid.process.set_levels(lt_tank=0.37, lt_res=0.04)
    tripped = skid.step(0.1)
    assert TripCode.HH_TANK in tripped.trip_codes
    assert TripCode.LL_RES in tripped.trip_codes

    # Clear only HH condition; Reset must not clear either latch
    skid.process.set_levels(lt_tank=0.15, lt_res=0.04)
    partial = skid.step(0.1, command=OperatorCommand.RESET)
    assert TripCode.HH_TANK in partial.trip_codes
    assert TripCode.LL_RES in partial.trip_codes
    assert partial.trip_active is True
    assert partial.mode is Mode.TRIPPED

    # All underlying conditions clear → Reset clears both
    skid.process.set_levels(lt_tank=0.15, lt_res=0.20)
    still = skid.step(0.1)
    assert still.trip_active is True
    assert TripCode.HH_TANK in still.trip_codes
    assert TripCode.LL_RES in still.trip_codes

    reset = skid.step(0.1, command=OperatorCommand.RESET)
    assert reset.trip_active is False
    assert reset.mode is Mode.STOP
    assert reset.trip_codes == frozenset()

    assert skid.step(0.1, command=OperatorCommand.START).mode is Mode.RUNNING


def test_mock_process_is_first_class():
    """Mock path is a product module under plcassistant.wedge.process."""
    proc = MockProcess()
    assert proc.state.lt_tank == pytest.approx(0.15)
    s = proc.step(0.05, 50.0)
    assert s.cmd_speed == 50.0


def test_skid_limits_sync_process_and_safety():
    """SkidConfig.limits is the single owner for HH/LL thresholds."""
    skid = Skid(SkidConfig(limits=LimitConfig(lim_level_hh=0.30, lim_res_ll=0.08)))
    assert skid.config.process.lim_res_ll == 0.08
    assert skid.process.config.lim_res_ll == 0.08
    assert skid.safety.config.lim_level_hh == 0.30
    assert skid.safety.config.lim_res_ll == 0.08

    skid.process.set_levels(lt_tank=0.31, lt_res=0.20)
    snap = skid.step(0.1)
    assert TripCode.HH_TANK in snap.trip_codes
