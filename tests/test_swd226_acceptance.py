"""SWD-226: PID card SP edit stability + climate-inspired faceplate."""

from __future__ import annotations

from pathlib import Path

ROOT = Path("custom_components/plcassistant")
CARD = ROOT / "www" / "pid-loop-card.js"


def test_unit_pid_card_uses_text_sp_inputs() -> None:
    text = CARD.read_text(encoding="utf-8")
    assert 'type="text"' in text
    assert 'inputmode="decimal"' in text
    assert 'type="number"' not in text
    assert "_dirty" in text
    assert "_parseSp" in text
    assert 'key === "Enter"' in text
    assert 'key === "Escape"' in text


def test_unit_pid_card_preserves_dirty_drafts_across_hass() -> None:
    text = CARD.read_text(encoding="utf-8")
    # Live hass must not rewrite focused/dirty drafts (caret / "0." → 30 bug).
    assert "Never rewrite a focused or dirty draft" in text
    assert "this._dirty[key]" in text
    assert "_captureFocusedDrafts" in text
    # Focus alone must not freeze the field after blur.
    assert "do not mark dirty on focus alone" in text
    # Blur must not discard drafts (prior SWD-222 cleared on focusout).
    assert "focusout" not in text
    assert "@supports (background: color-mix" in text


def test_unit_pid_card_climate_visual_cues() -> None:
    text = CARD.read_text(encoding="utf-8")
    assert "pid-badge" in text
    assert "pid-hero" in text
    assert "active-source" in text
    assert "--pid-man" in text
    assert "--pid-auto" in text
    assert "--pid-rem" in text
    assert "Active SP" in text
    assert "data-cv-bar" in text
    assert 'data-mode="' in text


def test_system_app_version_tracks_current() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.49"' in manifest
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.49"' in config
    docker = Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.49" in docker
    dash = (ROOT / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 28" in dash
    assert "custom:plcassistant-pid-card" in dash


def test_system_dashboard_upgrade_includes_prior_versions() -> None:
    dash_py = (ROOT / "lovelace_dashboard.py").read_text(encoding="utf-8")
    assert "2[0-7]" in dash_py
    run = Path("plc_assistant/run.sh").read_text(encoding="utf-8")
    assert "2[0-7]" in run
