"""Unit tests for I/O image quality, last-good, and scan IN/OUT seams (SWD-95)."""

from __future__ import annotations

import pytest

from plcassistant.io import (
    IoImage,
    QualityStatus,
    ReasonCode,
    TagQuality,
    collapse_quality,
    is_good,
)


def _image_with_level(default: float = 0.0) -> IoImage:
    image = IoImage()
    image.declare("LT_TANK", default=default)
    return image


def test_initial_bad_default_before_first_good():
    image = _image_with_level(default=0.05)
    value, quality = image.get("LT_TANK")
    assert value == 0.05
    assert quality.status is QualityStatus.BAD
    assert quality.reason is ReasonCode.UNAVAILABLE
    assert is_good(quality) is False
    snap = image.snapshot()["LT_TANK"]
    assert snap.last_good is None
    assert snap.default == 0.05


def test_good_updates_value_and_last_good():
    image = _image_with_level(default=0.0)
    image.apply_input("LT_TANK", 0.22, QualityStatus.GOOD)
    value, quality = image.get("LT_TANK")
    assert value == 0.22
    assert quality.status is QualityStatus.GOOD
    assert quality.reason is None
    assert is_good(quality) is True
    assert image.snapshot()["LT_TANK"].last_good == 0.22


@pytest.mark.parametrize(
    "status,reason",
    [
        (QualityStatus.BAD, ReasonCode.FAULT),
        (QualityStatus.BAD, ReasonCode.STALE),
        (QualityStatus.UNCERTAIN, ReasonCode.UNKNOWN),
        (QualityStatus.UNCERTAIN, ReasonCode.STALE),
    ],
)
def test_non_good_keeps_last_good_with_updated_quality(status, reason):
    image = _image_with_level(default=0.0)
    image.apply_input("LT_TANK", 0.18, QualityStatus.GOOD)
    image.apply_input("LT_TANK", 999.0, status, reason)
    value, quality = image.get("LT_TANK")
    assert value == 0.18
    assert quality.status is status
    assert quality.reason is reason
    assert is_good(quality) is False
    assert image.snapshot()["LT_TANK"].last_good == 0.18


def test_non_good_before_first_good_keeps_default():
    image = _image_with_level(default=0.07)
    image.apply_input("LT_TANK", 1.23, QualityStatus.BAD, ReasonCode.FAULT)
    value, quality = image.get("LT_TANK")
    assert value == 0.07
    assert quality.status is QualityStatus.BAD
    assert quality.reason is ReasonCode.FAULT
    assert image.snapshot()["LT_TANK"].last_good is None


def test_is_good_and_collapse_helper():
    good = TagQuality(QualityStatus.GOOD)
    bad = TagQuality(QualityStatus.BAD, ReasonCode.UNAVAILABLE)
    uncertain = TagQuality(QualityStatus.UNCERTAIN, ReasonCode.STALE)
    assert is_good(good) is True
    assert is_good(QualityStatus.GOOD) is True
    assert is_good(bad) is False
    assert is_good(uncertain) is False
    assert is_good(QualityStatus.BAD) is False
    assert collapse_quality(good) is True
    assert collapse_quality(uncertain) is False


def test_tag_quality_validation():
    with pytest.raises(ValueError):
        TagQuality(QualityStatus.GOOD, ReasonCode.FAULT)
    with pytest.raises(ValueError):
        TagQuality(QualityStatus.BAD)
    with pytest.raises(ValueError):
        TagQuality(QualityStatus.UNCERTAIN)


def test_scan_start_end_api_without_bindings():
    """Scan-oriented seams: IN at start, OUT snapshot at end."""
    image = IoImage()
    image.declare("LT_TANK", default=0.0)
    image.declare("CMD_SPEED", default=0.0)

    image.begin_inputs()
    image.apply_input("LT_TANK", 0.20, QualityStatus.GOOD)

    level = image.get_value("LT_TANK")
    assert level == 0.20
    assert is_good(image.get_quality("LT_TANK"))

    image.set_output("CMD_SPEED", 42.5)
    flush = image.snapshot_outputs()
    assert flush == {"CMD_SPEED": 42.5}
    assert "LT_TANK" not in flush

    full = image.snapshot()
    assert set(full) == {"LT_TANK", "CMD_SPEED"}
    assert full["CMD_SPEED"].quality.status is QualityStatus.GOOD


def test_declare_duplicate_and_unknown_tag_errors():
    image = _image_with_level()
    with pytest.raises(ValueError, match="already declared"):
        image.declare("LT_TANK", default=1.0)
    with pytest.raises(KeyError, match="unknown tag"):
        image.apply_input("NOPE", 1.0, QualityStatus.GOOD)


def test_apply_input_non_finite_good_demotes_to_bad_fault():
    image = _image_with_level(default=0.0)
    image.apply_input("LT_TANK", 0.25, QualityStatus.GOOD)
    image.apply_input("LT_TANK", float("nan"), QualityStatus.GOOD)
    value, quality = image.get("LT_TANK")
    assert value == 0.25
    assert quality.status is QualityStatus.BAD
    assert quality.reason is ReasonCode.FAULT

    image.apply_input("LT_TANK", float("inf"), QualityStatus.GOOD)
    value, quality = image.get("LT_TANK")
    assert value == 0.25
    assert quality.status is QualityStatus.BAD
    assert quality.reason is ReasonCode.FAULT


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_set_output_non_finite_demotes_to_bad_fault(bad):
    """Non-finite set_output matches apply_input: BAD/fault, not published GOOD."""
    image = IoImage()
    image.declare("CMD_SPEED", default=0.0)
    image.set_output("CMD_SPEED", 42.5)
    assert image.get_quality("CMD_SPEED").status is QualityStatus.GOOD
    assert image.snapshot_outputs() == {"CMD_SPEED": 42.5}

    image.set_output("CMD_SPEED", bad)
    value, quality = image.get("CMD_SPEED")
    assert value == 42.5
    assert quality.status is QualityStatus.BAD
    assert quality.reason is ReasonCode.FAULT
    # Still marked written, but value retained last-good (not nan/inf)
    assert image.snapshot_outputs() == {"CMD_SPEED": 42.5}


def test_set_output_non_finite_before_first_good_keeps_default():
    image = IoImage()
    image.declare("CMD_SPEED", default=7.0)
    image.set_output("CMD_SPEED", float("nan"))
    value, quality = image.get("CMD_SPEED")
    assert value == 7.0
    assert quality.status is QualityStatus.BAD
    assert quality.reason is ReasonCode.FAULT
    assert image.snapshot()["CMD_SPEED"].last_good is None
    assert "CMD_SPEED" in image.snapshot_outputs()
