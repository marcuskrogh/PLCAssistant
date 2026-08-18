"""SWD-373: isolate PID faceplate elements + developer sandbox."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tests.pid_faceplate_chrome import CARD, ELEMENTS, faceplate_chrome_source

ROOT = Path("custom_components/plcassistant")
SANDBOX = Path("tools/pid-faceplate")
JS_ELEMENTS = Path("tests/js/pid_faceplate_elements.test.mjs")
FACEPLATE = Path("docs/io/06-pid-faceplate.md")


def test_unit_named_elements_are_mountable() -> None:
    text = ELEMENTS.read_text(encoding="utf-8")
    for element_id in ("isa-glyph", "kpi-row", "analog-bars", "mode-row"):
        assert f'id: "{element_id}"' in text
    assert "export function mountPidFaceplateElement" in text
    assert "export function applyPidFaceplateState" in text
    assert "export const PID_FACEPLATE_ELEMENT_IDS" in text


def test_unit_lovelace_card_imports_shared_module() -> None:
    card = CARD.read_text(encoding="utf-8")
    assert 'from "./pid-faceplate-elements.js"' in card
    assert "pidFaceplateRootHtml" in card
    assert "applyPidFaceplateState" in card
    chrome = faceplate_chrome_source()
    assert 'data-bar="pv"' in chrome
    assert "pid-err-between" in chrome
    assert "data-value-min" in chrome
    assert "data-value-max" in chrome
    assert "data-value-current" in chrome
    assert "pointer-events: none" not in chrome
    assert "data-nudge" in chrome
    assert 'data-settings="open"' in chrome
    assert "pid-settings-dialog" in chrome
    assert "[data-pane-panel][hidden]" in chrome
    assert 'data-pane="gains"' in chrome
    assert 'data-tune="tf_ts"' in chrome
    assert 'data-tune-readonly="form"' in chrome
    assert ".pid-vbar-fill[data-writable=\"1\"]" in chrome
    assert "--pid-active" in chrome
    assert 'data-pid-hi="abnormal"] .pid-vbar-fill[data-writable="1"]' not in chrome
    assert "_applyBarClick" not in chrome


def test_unit_sandbox_is_developer_only() -> None:
    html = (SANDBOX / "index.html").read_text(encoding="utf-8")
    js = (SANDBOX / "sandbox.js").read_text(encoding="utf-8")
    readme = (SANDBOX / "README.md").read_text(encoding="utf-8")
    serve = (SANDBOX / "serve.sh").read_text(encoding="utf-8")
    assert "PID faceplate" in html
    assert "pid-faceplate-elements.js" in js
    assert "PID_FACEPLATE_ELEMENT_CATALOG" in js
    assert "No Home Assistant" in html or "no Home Assistant" in html.lower()
    assert "serve.sh" in readme
    assert "python3 -m http.server" in serve
    assert "SWD-373" not in html
    assert "SWD-373" not in js


def test_system_faceplate_element_js_contract() -> None:
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


def test_unit_faceplate_doc_points_at_sandbox() -> None:
    text = FACEPLATE.read_text(encoding="utf-8")
    assert "tools/pid-faceplate" in text
    assert "pid-faceplate-elements.js" in text


def test_system_app_version_is_0_1_63() -> None:
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
