"""SWD-227: PID card Set SP must not hit data-mode click hijack.

Also locks the integration ↔ HMI communication contract:
- faceplate Set/mode must send finite floats to ``number.set_value``
- click routing must not confuse accent/mode attributes with Set
- compound PID sensor exposes writable ``number.*`` SP/mode entity ids
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path("custom_components/plcassistant")
CARD = ROOT / "www" / "pid-loop-card.js"
JS_CONTRACT = Path("tests/js/pid_faceplate_contract.test.mjs")


def test_unit_pid_card_mode_click_targets_buttons_only() -> None:
    text = CARD.read_text(encoding="utf-8")
    assert 'closest("button[data-mode]")' in text
    assert 'closest("[data-mode]")' not in text
    assert "data-pid-mode" in text
    # Card root must not reuse data-mode (that hijacked Set → NaN).
    assert 'class="pid-card" data-mode=' not in text
    assert 'setAttribute("data-pid-mode"' in text


def test_unit_pid_card_exports_communication_helpers() -> None:
    text = CARD.read_text(encoding="utf-8")
    assert "export function parseSpValue" in text
    assert "export function numberServiceValue" in text
    assert "export function resolveFaceplateClick" in text
    assert "resolveFaceplateClick(ev.target)" in text
    assert "numberServiceValue(value)" in text


def test_unit_pid_card_set_number_rejects_non_finite() -> None:
    text = CARD.read_text(encoding="utf-8")
    set_number = text.split("async _setNumber", 1)[1].split("async _setMode", 1)[0]
    assert "numberServiceValue(value)" in set_number
    assert "numeric === null" in set_number
    # entity_id must stay in serviceData (legacy-compatible Lovelace target).
    assert "entity_id: entityId" in set_number
    assert "value: numeric" in set_number
    assert 'callService("number", "set_value"' in set_number
    set_mode = text.split("async _setMode", 1)[1].split("_inputValue", 1)[0]
    assert "numberServiceValue(code)" in set_mode
    assert "never pass label strings" in set_mode


def test_unit_dual_tree_pid_card_synced() -> None:
    app_card = Path("plc_assistant/custom_components/plcassistant/www/pid-loop-card.js")
    assert CARD.read_bytes() == app_card.read_bytes()


def test_system_faceplate_js_float_service_contract() -> None:
    """Behavioral Node regression for Set/mode → number.set_value float path."""
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


def test_unit_pid_loop_faceplate_entities_are_writable_numbers() -> None:
    """Compound PID attrs used by Set/mode must point at number.* (not sensors).

    Static parse — CI has no ``homeassistant``, so we do not import the package.
    """
    src = (ROOT / "pid_loop.py").read_text(encoding="utf-8")
    # Level loop: Man/Rem/mode are numbers; Auto is number (REQ).
    assert '"sp_man_entity": "number.plcassistant_sp_level_man"' in src
    assert '"sp_auto_entity": "number.plcassistant_sp_level_req"' in src
    assert '"sp_rem_entity": "number.plcassistant_sp_level_rem"' in src
    assert '"mode_entity": "number.plcassistant_level_mode"' in src
    # Flow Auto is the cascade CV sensor (card skips sensor.* on Set).
    assert '"sp_man_entity": "number.plcassistant_sp_flow_man"' in src
    assert '"sp_auto_entity": "sensor.plcassistant_sp_flow_auto"' in src
    assert '"sp_rem_entity": "number.plcassistant_sp_flow_rem"' in src
    assert '"mode_entity": "number.plcassistant_flow_mode"' in src
    # Card must refuse writing sensors (integration↔HMI guard).
    card = CARD.read_text(encoding="utf-8")
    assert 'startsWith("sensor.")' in card


def test_unit_number_set_native_value_requires_float() -> None:
    """HA number platform entry point must accept a float (vol.Coerce(float) path)."""
    src = (ROOT / "number.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_set_native_value":
            args = [a.arg for a in node.args.args]
            assert "value" in args
            ann = node.args.args[args.index("value")].annotation
            assert ann is not None
            assert ast.unparse(ann).strip() == "float"
            body = ast.unparse(node)
            assert "float(value)" in body
            found = True
            break
    assert found, "async_set_native_value not found"


def test_unit_sp_mode_flip_codes_are_floats() -> None:
    """Writing an SP must flip mode with numeric codes 0/1/2 — never strings."""
    src = (ROOT / "number.py").read_text(encoding="utf-8")
    # Fallback map uses float literals; Soft-PLC path uses float(SpSourceMode.*.code).
    assert '("LEVEL_MODE", 0.0)' in src
    assert '("LEVEL_MODE", 1.0)' in src
    assert '("LEVEL_MODE", 2.0)' in src
    assert "float(SpSourceMode.MANUAL.code)" in src
    assert "float(SpSourceMode.AUTOMATIC.code)" in src
    assert "float(SpSourceMode.REMOTE.code)" in src
    assert 'await self._publish_in_tag(mode_tag, float(mode_code))' in src
    # Must never publish mode labels.
    assert '"man"' not in src.split("_sp_mode_flip_map", 1)[1].split("def ", 1)[0]


def test_system_app_version_0_1_48() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.48"' in manifest
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.48"' in config
    docker = Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.48" in docker
    dash = (ROOT / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 27" in dash


if __name__ == "__main__":
    # Allow ``python tests/test_swd227_acceptance.py`` smoke for the Node harness.
    sys.exit(
        subprocess.call(
            ["node", "--experimental-default-type=module", str(JS_CONTRACT)]
        )
    )
