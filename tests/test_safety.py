"""Unit tests for the safety layer: trips, latch, reset, start/stop."""

from __future__ import annotations

import pytest

from plcassistant.io.quality import QualityStatus, ReasonCode, TagQuality
from plcassistant.wedge.safety import Mode, SafetyConfig, SafetyLayer, TripCode


def _ok(**overrides):
    base = {"lt_tank": 0.15, "lt_res": 0.20, "ft_inlet": 2.0}
    base.update(overrides)
    return base


def test_start_accepted_when_permissives_ok():
    safety = SafetyLayer()
    state = safety.evaluate(**_ok(), start=True)
    assert state.perm_ok is False  # MODE now RUNNING → PERM_OK false
    assert state.mode is Mode.RUNNING
    assert state.running is True
    assert state.pump_permit is True
    assert state.trip_active is False


def test_start_blocked_when_latched():
    safety = SafetyLayer()
    safety.evaluate(**_ok(lt_tank=0.37))
    assert safety.state.trip_active is True
    assert safety.state.mode is Mode.TRIPPED

    state = safety.evaluate(**_ok(lt_tank=0.37), start=True)
    assert state.trip_active is True
    assert state.perm_ok is False
    assert state.mode is Mode.TRIPPED
    assert state.running is False


def test_start_blocked_while_latched_even_after_condition_clears_without_reset():
    safety = SafetyLayer()
    safety.evaluate(**_ok(lt_tank=0.37))
    state = safety.evaluate(**_ok(lt_tank=0.15), start=True)
    assert state.trip_active is True
    assert state.perm_ok is False
    assert state.running is False


def test_stop_always_forces_idle():
    safety = SafetyLayer()
    safety.evaluate(**_ok(), start=True)
    assert safety.state.mode is Mode.RUNNING

    state = safety.evaluate(**_ok(), stop=True)
    assert state.mode is Mode.STOP
    assert state.running is False
    assert state.trip_active is False
    assert state.perm_ok is True


def test_hh_tank_trips_latches_and_stops():
    safety = SafetyLayer()
    safety.evaluate(**_ok(), start=True)
    state = safety.evaluate(**_ok(lt_tank=0.37))
    assert state.trip_active is True
    assert TripCode.HH_TANK in state.trip_codes
    assert state.mode is Mode.TRIPPED
    assert state.running is False


def test_ll_res_trips_latches_and_stops():
    safety = SafetyLayer()
    safety.evaluate(**_ok(), start=True)
    state = safety.evaluate(**_ok(lt_res=0.04))
    assert state.trip_active is True
    assert TripCode.LL_RES in state.trip_codes
    assert state.mode is Mode.TRIPPED


@pytest.mark.parametrize(
    "kwargs,code",
    [
        ({"lt_tank": None}, TripCode.LOS_LT_TANK),
        ({"lt_res": None}, TripCode.LOS_LT_RES),
        ({"ft_inlet": None}, TripCode.LOS_FT_INLET),
        (
            {"lt_tank_quality": TagQuality(QualityStatus.BAD, ReasonCode.FAULT)},
            TripCode.LOS_LT_TANK,
        ),
        (
            {"lt_res_quality": TagQuality(QualityStatus.BAD, ReasonCode.FAULT)},
            TripCode.LOS_LT_RES,
        ),
        (
            {"ft_inlet_quality": TagQuality(QualityStatus.BAD, ReasonCode.FAULT)},
            TripCode.LOS_FT_INLET,
        ),
        (
            {"lt_tank_quality": QualityStatus.UNCERTAIN},
            TripCode.LOS_LT_TANK,
        ),
        ({"lt_tank": float("nan")}, TripCode.LOS_LT_TANK),
    ],
)
def test_loss_of_signal_trips(kwargs, code):
    safety = SafetyLayer()
    safety.evaluate(**_ok(), start=True)
    state = safety.evaluate(**_ok(**kwargs))
    assert state.trip_active is True
    assert code in state.trip_codes
    assert state.mode is Mode.TRIPPED


def test_clearing_condition_alone_does_not_clear_latch_or_restart():
    safety = SafetyLayer()
    safety.evaluate(**_ok(), start=True)
    safety.evaluate(**_ok(lt_tank=0.37))
    state = safety.evaluate(**_ok(lt_tank=0.15))
    assert state.trip_active is True
    assert state.mode is Mode.TRIPPED
    assert TripCode.HH_TANK in state.trip_codes


def test_reset_clears_latch_but_does_not_auto_start():
    safety = SafetyLayer()
    safety.evaluate(**_ok(), start=True)
    safety.evaluate(**_ok(lt_tank=0.37))
    state = safety.evaluate(**_ok(lt_tank=0.15), reset=True)
    assert state.trip_active is False
    assert state.mode is Mode.STOP
    assert state.running is False
    assert state.perm_ok is True


def test_reset_while_condition_active_does_not_clear_latch():
    safety = SafetyLayer()
    safety.evaluate(**_ok(lt_tank=0.37))
    state = safety.evaluate(**_ok(lt_tank=0.37), reset=True)
    assert state.trip_active is True
    assert TripCode.HH_TANK in state.trip_codes


def test_start_after_reset_restarts():
    safety = SafetyLayer()
    safety.evaluate(**_ok(), start=True)
    safety.evaluate(**_ok(lt_tank=0.37))
    safety.evaluate(**_ok(lt_tank=0.15), reset=True)
    state = safety.evaluate(**_ok(lt_tank=0.15), start=True)
    assert state.mode is Mode.RUNNING


def test_custom_limits():
    safety = SafetyLayer(SafetyConfig(lim_level_hh=0.30, lim_res_ll=0.08))
    state = safety.evaluate(**_ok(lt_tank=0.31))
    assert TripCode.HH_TANK in state.trip_codes
