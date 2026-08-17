"""SWD-366: Lovelace PID cards ISA-5.1 look and ISA-101 highlighting."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path("custom_components/plcassistant")
CARD = ROOT / "www" / "pid-loop-card.js"
FACEPLATE = Path("docs/io/06-pid-faceplate.md")
ITERATE = Path("docs/ITERATE.md")
JS_CONTRACT = Path("tests/js/pid_faceplate_contract.test.mjs")


def test_unit_pid_card_isa_chrome_and_error_kpi() -> None:
    text = CARD.read_text(encoding="utf-8")
    assert "pid-isa-eps" in text
    assert "pid-isa-p" in text
    assert "pid-isa-i" in text
    assert "pid-isa-d" in text
    assert 'data-role="err"' in text
    assert "<span>ε</span>" in text
    assert "pid-sub" not in text
    assert "export function pidHighlightSeverity" in text
    assert "export function pidCvBarPct" in text
    assert "PID_CV_MAX_LEVEL = 8" in text
    assert "PID_ERR_CAUTION_FRAC = 0.02" in text
    assert "PID_ERR_ABNORMAL_FRAC = 0.1" in text


def test_unit_pid_card_isa101_colour_not_mode_hues() -> None:
    text = CARD.read_text(encoding="utf-8")
    assert "--pid-man" not in text
    assert "--pid-auto" not in text
    assert "--pid-rem" not in text
    assert "#c47800" not in text
    assert "#0d9488" not in text
    assert "#3b6ea5" not in text
    assert "--warning-color" in text
    assert "--error-color" in text
    assert 'data-pid-hi="normal"' in text
    assert ".pid-modes button.active" in text
    assert "background: var(--primary-text-color)" in text
    assert ".pid-cv-fill[data-hi=\"caution\"]" in text
    assert ".pid-cv-fill[data-hi=\"abnormal\"]" not in text
    # SP value is not permanently accent-coloured.
    assert '.pid-metric[data-role="sp"] strong { color: var(--pid-accent); }' not in text
    assert "climate-inspired" not in text


def test_unit_faceplate_doc_isa_not_climate() -> None:
    text = FACEPLATE.read_text(encoding="utf-8")
    assert "ISA-5.1" in text
    assert "ISA-101" in text
    assert "climate-inspired" not in text
    assert "8 L/min" in text


def test_unit_iterate_tracks_swd366() -> None:
    text = ITERATE.read_text(encoding="utf-8")
    assert "SWD-366" in text
    assert "SWD-360" in text
    assert "pidHighlightSeverity" in text
    assert "`/review-fix SWD-366`" in text


def test_system_faceplate_js_highlight_contract() -> None:
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


def test_system_app_version_is_0_1_56() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.56"' in manifest
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.56"' in config
    docker = Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.56" in docker
    dual = Path("plc_assistant/custom_components/plcassistant/manifest.json")
    assert '"0.1.56"' in dual.read_text(encoding="utf-8")


def test_dual_tree_pid_card_synced() -> None:
    app_card = Path("plc_assistant/custom_components/plcassistant/www/pid-loop-card.js")
    assert CARD.read_bytes() == app_card.read_bytes()
