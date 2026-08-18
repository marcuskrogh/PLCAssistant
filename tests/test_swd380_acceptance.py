"""SWD-380: paned PID settings for all standardised parameters."""

from __future__ import annotations

from pathlib import Path

from plcassistant.io.pid_loop import (
    FLOW_LOOP,
    LEVEL_LOOP,
    PID_OPERATOR_PARAM_KEYS,
    all_operator_param_tag_names,
)
from tests.pid_faceplate_chrome import ELEMENTS, faceplate_chrome_source

ROOT = Path("custom_components/plcassistant")
NUMBER = ROOT / "number.py"


def test_unit_operator_param_keys_match_standardised_pid() -> None:
    assert PID_OPERATOR_PARAM_KEYS == (
        "kp",
        "ki",
        "kd",
        "u0",
        "beta",
        "direct_acting",
        "cv_min",
        "cv_max",
        "hold_when_stopped",
        "ts",
        "tf_ts",
    )
    assert "td" not in PID_OPERATOR_PARAM_KEYS
    assert "gamma" not in PID_OPERATOR_PARAM_KEYS
    assert "form" not in PID_OPERATOR_PARAM_KEYS
    tags = all_operator_param_tag_names()
    assert LEVEL_LOOP.tf_ts in tags
    assert FLOW_LOOP.hold_when_stopped in tags
    assert LEVEL_LOOP.operator_param_tags()["beta"] == "LEVEL_BETA"


def test_unit_settings_dialog_has_panes_and_standardised_fields() -> None:
    chrome = faceplate_chrome_source()
    for pane in ("gains", "structure", "output", "filter"):
        assert f'data-pane="{pane}"' in chrome
        assert f'data-pane-panel="{pane}"' in chrome
    for key in PID_OPERATOR_PARAM_KEYS:
        assert f'data-tune="{key}"' in chrome
    assert 'data-tune-readonly="form"' in chrome
    assert "Parallel" in chrome
    assert 'data-tune="td"' not in chrome
    assert 'data-tune="gamma"' not in chrome
    assert "applyPidSettingsPane" in ELEMENTS.read_text(encoding="utf-8")


def test_unit_ha_numbers_exist_for_operator_params() -> None:
    text = NUMBER.read_text(encoding="utf-8")
    for tag in all_operator_param_tag_names():
        assert f'"{tag}"' in text
        assert tag in (
            ROOT / "datablocks" / "catalog.py"
        ).read_text(encoding="utf-8")


def test_unit_sandbox_edits_all_operator_params() -> None:
    js = Path("tools/pid-faceplate/sandbox.js").read_text(encoding="utf-8")
    assert "PID_TUNE_KEYS" in js
    assert "hold_when_stopped" in js
    assert "applyPidSettingsPane" in js
    assert "SWD-380" not in js
