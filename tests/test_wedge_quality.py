"""Unit tests for wedge PV quality bridging to plcassistant.io TagQuality."""

from __future__ import annotations

import pytest

from plcassistant.io.quality import QualityStatus, ReasonCode, TagQuality, is_good
from plcassistant.wedge.quality import (
    coerce_tag_quality,
    pv_ok,
    quality_from_pv,
    resolve_tag_quality,
)
from plcassistant.wedge.safety import Mode, TripCode
from plcassistant.wedge.skid import OperatorCommand, Skid


def test_pv_ok_rejects_none_nan_inf_negative():
    assert pv_ok(0.0) is True
    assert pv_ok(0.15) is True
    assert pv_ok(None) is False
    assert pv_ok(float("nan")) is False
    assert pv_ok(float("inf")) is False
    assert pv_ok(-0.01) is False


def test_quality_from_pv_maps_failures():
    assert quality_from_pv(0.2) == TagQuality(QualityStatus.GOOD)
    assert quality_from_pv(None) == TagQuality(QualityStatus.BAD, ReasonCode.UNAVAILABLE)
    assert quality_from_pv(float("nan")).status is QualityStatus.BAD
    assert quality_from_pv(float("nan")).reason is ReasonCode.FAULT
    assert quality_from_pv(-1.0).reason is ReasonCode.FAULT


def test_resolve_tag_quality_forced_non_good_wins():
    forced = TagQuality(QualityStatus.BAD, ReasonCode.FAULT)
    assert resolve_tag_quality(0.20, forced) is forced
    uncertain = TagQuality(QualityStatus.UNCERTAIN, ReasonCode.STALE)
    assert resolve_tag_quality(0.20, uncertain) is uncertain
    assert is_good(resolve_tag_quality(0.20, QualityStatus.UNCERTAIN)) is False


def test_resolve_tag_quality_good_still_checks_pv():
    assert resolve_tag_quality(None, QualityStatus.GOOD).status is QualityStatus.BAD
    assert resolve_tag_quality(0.15, QualityStatus.GOOD).status is QualityStatus.GOOD


def test_coerce_tag_quality():
    assert coerce_tag_quality(QualityStatus.GOOD) == TagQuality(QualityStatus.GOOD)
    bad = coerce_tag_quality(QualityStatus.BAD)
    assert bad.status is QualityStatus.BAD
    assert bad.reason is ReasonCode.FAULT


def test_skid_force_quality_uncertain_trips_los():
    skid = Skid()
    skid.process.set_levels(lt_tank=0.15, lt_res=0.20)
    skid.step(0.1, command=OperatorCommand.START)
    skid.force_quality("LT_TANK", QualityStatus.UNCERTAIN, ReasonCode.STALE)
    snap = skid.step(0.1)
    assert snap.mode is Mode.TRIPPED
    assert TripCode.LOS_LT_TANK in snap.trip_codes
    assert snap.lt_tank_quality.status is QualityStatus.UNCERTAIN
    assert snap.lt_tank is None


def test_skid_force_quality_rejects_unknown_tag():
    skid = Skid()
    with pytest.raises(ValueError, match="force_quality"):
        skid.force_quality("CMD_SPEED", QualityStatus.BAD, ReasonCode.FAULT)
