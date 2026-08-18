"""SWD-382: PID faceplate settings fields must not reset while editing."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tests.pid_faceplate_chrome import CARD, ELEMENTS, faceplate_chrome_source

ROOT = Path("custom_components/plcassistant")
JS_ELEMENTS = Path("tests/js/pid_faceplate_elements.test.mjs")
FACEPLATE = Path("docs/io/06-pid-faceplate.md")


def test_unit_settings_fields_freeze_while_dialog_open() -> None:
    chrome = faceplate_chrome_source()
    card = CARD.read_text(encoding="utf-8")
    elements = ELEMENTS.read_text(encoding="utf-8")
    assert "pidSettingsDialogOpen" in elements
    assert "freezeTune" in elements
    assert "data-dirty" in elements
    assert "_captureTuneDrafts" in card
    assert "_restoreTuneDrafts" in card
    assert "_clearTuneDrafts" in card
    assert 'input[data-tune]' in card
    assert "Never rewrite a focused or dirty draft" in chrome
    assert "settings fields freeze" in card.lower() or "Settings fields freeze" in card


def test_unit_settings_drafts_do_not_clear_on_blur() -> None:
    card = CARD.read_text(encoding="utf-8")
    assert "focusout" not in card
    assert "Do not clear dirty drafts on blur" in card
    assert "_onEditorInput" in card


def test_unit_faceplate_doc_mentions_settings_drafts() -> None:
    text = FACEPLATE.read_text(encoding="utf-8")
    assert "settings" in text.lower()
    assert "data-tune" in text or "Controller settings" in text
    assert "freeze" in text.lower() or "draft" in text.lower()


def test_system_settings_draft_js_contract() -> None:
    proc = subprocess.run(
        [
            "node",
            "--experimental-default-type=module",
            str(JS_ELEMENTS),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )
    if proc.returncode != 0:
        raise AssertionError(
            "pid faceplate element JS contract failed:\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    assert "open settings dialog freezes Kp" in proc.stdout
    assert "data-dirty settings draft survives" in proc.stdout


def test_system_app_version_is_0_1_65() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.65"' in manifest
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.65"' in config
    docker = Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.65" in docker
    dual = Path("plc_assistant/custom_components/plcassistant/manifest.json")
    assert '"0.1.65"' in dual.read_text(encoding="utf-8")


def test_dual_tree_elements_and_card_synced() -> None:
    dual = Path("plc_assistant/custom_components/plcassistant/www")
    assert CARD.read_bytes() == (dual / "pid-loop-card.js").read_bytes()
    assert ELEMENTS.read_bytes() == (dual / "pid-faceplate-elements.js").read_bytes()
