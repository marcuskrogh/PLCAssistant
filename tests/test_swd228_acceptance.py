"""SWD-228: compact PID faceplate — 2dp KPIs, single-row mobile, edit popup."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.pid_faceplate_chrome import faceplate_chrome_source

ROOT = Path("custom_components/plcassistant")
CARD = ROOT / "www" / "pid-loop-card.js"
JS_CONTRACT = Path("tests/js/pid_faceplate_contract.test.mjs")


def test_unit_pid_card_display_precision_two_decimals() -> None:
    text = faceplate_chrome_source()
    assert "PID_DISPLAY_DIGITS = 2" in text
    assert "export function formatPidValue" in text
    assert "_fmt(value, digits = PID_DISPLAY_DIGITS)" in text
    # Default display path must not use 3dp.
    assert "_fmt(value, digits = 3)" not in text


def test_unit_pid_card_kpi_row_never_wraps() -> None:
    text = faceplate_chrome_source()
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in text
    # Four KPIs (PV / SP / ε / CO) stay on one row; no mobile wrap.
    assert "grid-column: 1 / -1" not in text
    assert "@media (max-width: 420px)" not in text


def test_unit_pid_card_compact_popup_editors() -> None:
    text = faceplate_chrome_source()
    assert "data-open-editor" in text
    assert "data-close-editor" in text
    assert "pid-dialog" in text
    assert "pid-dialog-panel" in text
    assert "pid-shell" in text
    assert "_dialogOpen" in text
    assert 'getCardSize() {\n    return 4;' in text or "return 4;" in text
    # Editors live in the dialog, not as always-visible faceplate rows alone.
    assert "pid-editors" in text
    assert "Tap to adjust" in text
    # Faceplate surface opens dialog; Set/mode stay on button[data-mode]/data-apply.
    assert 'closest("button[data-mode]")' in text
    assert "data-pid-mode" in text
    # Dialog is assembled as a sibling of .pid-card inside pidFaceplateMarkup
    # (pidDialogHtml is interpolated after the card, not nested in it).
    markup = text.split("export function pidFaceplateMarkup", 1)[1].split(
        "export function pidFaceplateRootHtml", 1
    )[0]
    assert '<div class="pid-card">' in markup
    assert "${dialog}" in markup
    assert "pidDialogHtml" in markup
    card_idx = markup.find('<div class="pid-card">')
    dialog_idx = markup.find("${dialog}")
    assert card_idx != -1 and dialog_idx > card_idx
    # Explicit: overflow:hidden stays on .pid-card, not on .pid-shell.
    assert "overflow: hidden;" in text.split(".pid-card {", 1)[1].split("}", 1)[0]
    assert "overflow: hidden;" not in text.split(".pid-shell", 1)[1].split(".pid-card", 1)[0]


def test_unit_pid_dialog_not_nested_under_overflow_clip() -> None:
    """Regression for review-fix iter 1: fixed dialog must escape face clip."""
    text = faceplate_chrome_source()
    markup = text.split("export function pidFaceplateMarkup", 1)[1].split(
        "export function pidFaceplateRootHtml", 1
    )[0]
    assert '<div class="pid-shell"' in markup
    assert '<div class="pid-card">' in markup
    assert "${dialog}" in markup
    card_open = markup.find('<div class="pid-card">')
    dialog_ref = markup.find("${dialog}")
    between = markup[card_open:dialog_ref]
    assert "</div>" in between
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


def test_system_app_version_tracks_current() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.63"' in manifest
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.63"' in config
    docker = Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.63" in docker
    dash = (ROOT / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 28" in dash
    assert "custom:plcassistant-pid-card" in dash


def test_system_dashboard_upgrade_includes_prior_versions() -> None:
    dash_py = (ROOT / "lovelace_dashboard.py").read_text(encoding="utf-8")
    assert "2[0-7]" in dash_py
    run = Path("plc_assistant/run.sh").read_text(encoding="utf-8")
    assert "2[0-7]" in run
