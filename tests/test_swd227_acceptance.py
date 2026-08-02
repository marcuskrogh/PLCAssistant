"""SWD-227: PID card Set SP must not hit data-mode click hijack."""

from __future__ import annotations

from pathlib import Path

ROOT = Path("custom_components/plcassistant")
CARD = ROOT / "www" / "pid-loop-card.js"


def test_unit_pid_card_mode_click_targets_buttons_only() -> None:
    text = CARD.read_text(encoding="utf-8")
    assert 'closest("button[data-mode]")' in text
    assert 'closest("[data-mode]")' not in text
    assert "data-pid-mode" in text
    # Card root must not reuse data-mode (that hijacked Set → NaN).
    assert 'class="pid-card" data-mode=' not in text
    assert 'setAttribute("data-pid-mode"' in text


def test_unit_pid_card_set_number_rejects_non_finite() -> None:
    text = CARD.read_text(encoding="utf-8")
    set_number = text.split("async _setNumber", 1)[1].split("async _setMode", 1)[0]
    assert "Number.isFinite(numeric)" in set_number
    assert "parseFloat" in set_number
    set_mode = text.split("async _setMode", 1)[1].split("_inputValue", 1)[0]
    assert 'Number.isFinite(numeric)' in set_mode
    assert "never pass label strings" in set_mode


def test_system_app_version_0_1_47() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.47"' in manifest
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.47"' in config
    docker = Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.47" in docker
    dash = (ROOT / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 26" in dash
