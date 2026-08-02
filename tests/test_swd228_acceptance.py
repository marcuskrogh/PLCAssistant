"""SWD-228: compact PID faceplate — 2dp KPIs, single-row mobile, edit popup."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path("custom_components/plcassistant")
CARD = ROOT / "www" / "pid-loop-card.js"
JS_CONTRACT = Path("tests/js/pid_faceplate_contract.test.mjs")


def test_unit_pid_card_display_precision_two_decimals() -> None:
    text = CARD.read_text(encoding="utf-8")
    assert "PID_DISPLAY_DIGITS = 2" in text
    assert "export function formatPidValue" in text
    assert "_fmt(value, digits = PID_DISPLAY_DIGITS)" in text
    # Default display path must not use 3dp.
    assert "_fmt(value, digits = 3)" not in text


def test_unit_pid_card_kpi_row_never_wraps() -> None:
    text = CARD.read_text(encoding="utf-8")
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in text
    # Prior SWD-226 media query collapsed CV onto a second row — must be gone.
    assert "grid-column: 1 / -1" not in text
    assert "@media (max-width: 420px)" not in text


def test_unit_pid_card_compact_popup_editors() -> None:
    text = CARD.read_text(encoding="utf-8")
    assert "data-open-editor" in text
    assert "data-close-editor" in text
    assert "pid-dialog" in text
    assert "pid-dialog-panel" in text
    assert "pid-shell" in text
    assert "_dialogOpen" in text
    assert 'getCardSize() {\n    return 2;' in text or "return 2;" in text
    # Editors live in the dialog, not as always-visible faceplate rows alone.
    assert "pid-editors" in text
    assert "Tap to adjust" in text
    # Faceplate surface opens dialog; Set/mode stay on button[data-mode]/data-apply.
    assert 'closest("button[data-mode]")' in text
    assert "data-pid-mode" in text
    # Dialog must be a sibling of .pid-card (not nested under overflow:hidden).
    assert "pid-shell" in text
    card_idx = text.find('<div class="pid-card">')
    dialog_idx = text.find('<div class="pid-dialog"')
    assert card_idx != -1 and dialog_idx != -1 and dialog_idx > card_idx
    # Explicit: overflow:hidden stays on .pid-card, not on .pid-shell.
    assert ".pid-card {\n          position: relative;\n          overflow: hidden;" in text
    assert "overflow: hidden;" not in text.split(".pid-shell", 1)[1].split(".pid-card", 1)[0]


def test_unit_pid_dialog_not_nested_under_overflow_clip() -> None:
    """Regression for review-fix iter 1: fixed dialog must escape face clip."""
    text = CARD.read_text(encoding="utf-8")
    # Extract the available-entity HTML template region.
    start = text.find('<div class="pid-shell"')
    end = text.find("`\n      }", start)
    assert start != -1 and end != -1
    tpl = text[start:end]
    # Dialog is inside pid-shell but outside pid-card.
    assert '<div class="pid-card">' in tpl
    assert '<div class="pid-dialog"' in tpl
    # Close the pid-card before the dialog opens.
    card_open = tpl.find('<div class="pid-card">')
    dialog_open = tpl.find('<div class="pid-dialog"')
    # Count div depth between card open and dialog: after closing pid-card
    # there should be a literal </div> that ends pid-card before dialog.
    between = tpl[card_open:dialog_open]
    assert between.count("<div") >= 1
    assert "</div>" in between
    # Ensure dialog is not inside an overflow:hidden ancestor in CSS ownership.
    assert "overflow: hidden" in text
    shell_css = text.split(".pid-shell {", 1)[1].split(".pid-card {", 1)[0]
    assert "overflow: hidden" not in shell_css


def test_unit_dual_tree_pid_card_synced() -> None:
    app_card = Path("plc_assistant/custom_components/plcassistant/www/pid-loop-card.js")
    assert CARD.read_bytes() == app_card.read_bytes()


def test_system_faceplate_js_compact_contract() -> None:
    assert JS_CONTRACT.is_file()
    proc = subprocess.run(
        [
            "node",
            "--experimental-default-type=module",
            str(JS_CONTRACT),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )
    if proc.returncode != 0:
        pytest.fail(
            "pid faceplate JS contract failed:\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )


def test_system_app_version_0_1_48() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.48"' in manifest
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.48"' in config
    docker = Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.48" in docker
    dash = (ROOT / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 27" in dash
    assert "0.1.48+" in dash


def test_system_dashboard_upgrade_includes_26() -> None:
    dash_py = (ROOT / "lovelace_dashboard.py").read_text(encoding="utf-8")
    assert "|26)" in dash_py or "|26\\" in dash_py or "25|26" in dash_py
    run = Path("plc_assistant/run.sh").read_text(encoding="utf-8")
    assert "25|26" in run
