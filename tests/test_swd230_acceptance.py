"""SWD-230: PID card Lovelace typography + 2dp everywhere."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.pid_faceplate_chrome import faceplate_chrome_source

ROOT = Path("custom_components/plcassistant")
CARD = ROOT / "www" / "pid-loop-card.js"
PID = ROOT / "pid_loop.py"
SENSOR = ROOT / "sensor.py"
NUMBER = ROOT / "number.py"
JS_CONTRACT = Path("tests/js/pid_faceplate_contract.test.mjs")


def test_unit_pid_card_uses_ha_font_tokens() -> None:
    text = faceplate_chrome_source()
    assert "--ha-font-family-body" in text
    assert "--ha-card-header-font-size" in text
    assert "--ha-font-size-l" in text
    assert "--ha-font-size-xs" in text
    assert "--ha-font-size-m" in text
    # Must not force a foreign stack that fights the HA theme.
    assert '"Segoe UI", Roboto' not in text
    assert "clamp(0.95rem, 3.8vw, 1.35rem)" not in text
    assert "border-radius: 999px" not in text


def test_unit_pid_card_formats_all_numerics_via_helper() -> None:
    text = faceplate_chrome_source()
    assert "PID_DISPLAY_DIGITS = 2" in text
    assert "export function formatPidValue" in text
    assert "n.toFixed(digits)" in text
    # Committed SP editors and KPI path both go through formatPidValue.
    assert "formatPidValue(value, PID_DISPLAY_DIGITS)" in text
    assert "formatPidValue(pv)" in text
    # No leftover 3dp default path.
    assert "_fmt(value, digits = 3)" not in text


def test_unit_pid_attributes_rounded_to_two_decimals() -> None:
    text = PID.read_text(encoding="utf-8")
    assert "from .const import DOMAIN, round_display" in text or "round_display" in text
    assert "round_display(_cache_value" in text
    refresh = text.split("def _refresh_from_store", 1)[1].split(
        "async def async_added_to_hass", 1
    )[0]
    for key in ("pv", "sp", "sp_man", "sp_auto", "sp_rem", "cv"):
        assert "round_display" in refresh
        assert f'"{key}"' in refresh
    for key in ("kp", "ki", "kd", "u0", "beta", "tf_ts", "hold_when_stopped"):
        assert f'"{key}"' in text
    assert '"_round_display"' not in text
    assert "_round_display" not in text.split("__all__", 1)[-1]


def test_unit_round_display_helper() -> None:
    import importlib.util
    import math
    import sys
    from types import ModuleType

    if "homeassistant" not in sys.modules:
        ha = ModuleType("homeassistant")
        sys.modules["homeassistant"] = ha
        for name in (
            "homeassistant.config_entries",
            "homeassistant.components",
            "homeassistant.components.sensor",
            "homeassistant.core",
            "homeassistant.helpers",
            "homeassistant.helpers.entity_platform",
        ):
            sys.modules[name] = ModuleType(name)
        sys.modules["homeassistant.components.sensor"].SensorEntity = object
        sys.modules["homeassistant.helpers.entity_platform"].AddEntitiesCallback = object
        sys.modules["homeassistant.config_entries"].ConfigEntry = object
        sys.modules["homeassistant.core"].Event = object
        sys.modules["homeassistant.core"].HomeAssistant = object

    cc = Path("custom_components").resolve()
    if str(cc.parent) not in sys.path:
        sys.path.insert(0, str(cc.parent))
    if "custom_components" not in sys.modules:
        pkg = ModuleType("custom_components")
        pkg.__path__ = [str(cc)]  # type: ignore[attr-defined]
        sys.modules["custom_components"] = pkg
    if "custom_components.plcassistant" not in sys.modules:
        sub = ModuleType("custom_components.plcassistant")
        sub.__path__ = [str(ROOT.resolve())]  # type: ignore[attr-defined]
        sys.modules["custom_components.plcassistant"] = sub

    const_path = ROOT / "const.py"
    spec_c = importlib.util.spec_from_file_location(
        "custom_components.plcassistant.const",
        const_path,
    )
    assert spec_c and spec_c.loader
    const_mod = importlib.util.module_from_spec(spec_c)
    sys.modules["custom_components.plcassistant.const"] = const_mod
    spec_c.loader.exec_module(const_mod)
    assert const_mod.DISPLAY_PRECISION == 2
    round_display = const_mod.round_display
    assert round_display(1.23456) == 1.23
    assert round_display("0.2") == 0.2
    assert round_display(None) is None
    assert round_display("bad") is None
    assert math.isclose(round_display(0.20000000000000004), 0.2)


def test_unit_process_sensors_suggest_two_decimals() -> None:
    text = SENSOR.read_text(encoding="utf-8")
    assert "DISPLAY_PRECISION" in text
    assert "round_display" in text
    assert text.count("suggested_display_precision = DISPLAY_PRECISION") >= 2
    assert "SWD-230" in text
    num = NUMBER.read_text(encoding="utf-8")
    assert "suggested_display_precision = DISPLAY_PRECISION" in num
    assert 'meta.get("step", 0.01)' in num
    assert "round_display(value)" in num


def test_unit_dual_tree_pid_card_synced() -> None:
    dual = Path("plc_assistant/custom_components/plcassistant")
    for rel in (
        "www/pid-loop-card.js",
        "www/pid-faceplate-elements.js",
        "pid_loop.py",
        "sensor.py",
        "number.py",
        "const.py",
    ):
        assert (ROOT / rel).read_bytes() == (dual / rel).read_bytes(), rel


def test_unit_pid_card_null_safe_err_and_commit() -> None:
    text = faceplate_chrome_source()
    assert "export function isPresentFinite" in text
    assert "export function commitSpValue" in text
    assert "export function pidError" in text
    assert "isPresentFinite(sp) || !isPresentFinite(pv)" in text
    assert "pidError(sp, pv)" in text
    assert "commitSpValue(parsed)" in text
    assert "DISPLAY_PRECISION in const.py" in text


def test_system_faceplate_js_contract() -> None:
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


def test_system_app_version_0_1_50() -> None:
    assert '"0.1.63"' in (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert 'version: "0.1.63"' in Path("plc_assistant/config.yaml").read_text(
        encoding="utf-8"
    )
    assert "BUILD_VERSION=0.1.63" in Path("plc_assistant/Dockerfile").read_text(
        encoding="utf-8"
    )
    dual = Path("plc_assistant/custom_components/plcassistant")
    assert '"0.1.63"' in (dual / "manifest.json").read_text(encoding="utf-8")
    assert CARD.read_bytes() == (dual / "www" / "pid-loop-card.js").read_bytes()
