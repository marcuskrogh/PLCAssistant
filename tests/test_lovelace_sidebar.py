"""Soft-PLC Lovelace sidebar dashboard registration (SWD-134).

These tests stay import-safe without a running Home Assistant core: they
assert packaging, URL-path rules, and that the install path no longer
depends on copy/paste.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CC = ROOT / "custom_components" / "plcassistant"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_manifest_depends_on_frontend_and_lovelace() -> None:
    manifest = json.loads((CC / "manifest.json").read_text(encoding="utf-8"))
    deps = set(manifest.get("dependencies") or [])
    assert "frontend" in deps
    assert "lovelace" in deps
    assert "mqtt" in deps
    assert manifest["version"] == "0.1.49"


def test_app_version_locked_to_integration() -> None:
    text = (ROOT / "plc_assistant" / "config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.49"' in text
    docker = (ROOT / "plc_assistant" / "Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.49" in docker


def test_url_path_contains_hyphen() -> None:
    """HA Lovelace rejects url_path values without a hyphen."""
    mod = _load("plcassistant_lovelace_dashboard", CC / "lovelace_dashboard.py")
    assert "-" in mod.URL_PATH
    assert mod.URL_PATH == "plcassistant-skid"
    assert mod.REL_FILENAME == "dashboards/plcassistant.yaml"
    assert mod.TITLE == "PLCAssistant"
    conf = mod.default_dashboard_config()
    assert conf["show_in_sidebar"] is True
    assert conf["mode"] == "yaml"
    assert conf["filename"] == mod.REL_FILENAME


def test_bundled_yaml_exists() -> None:
    mod = _load("plcassistant_lovelace_dashboard2", CC / "lovelace_dashboard.py")
    bundled = mod.bundled_dashboard_yaml()
    assert bundled.is_file()
    text = bundled.read_text(encoding="utf-8")
    assert "title: PLCAssistant" in text
    assert "button.plcassistant_start" in text
    assert "button.plcassistant_stop" in text
    assert "button.plcassistant_reset" in text
    assert "sensor.plcassistant_lt_tank_in" in text
    assert "sensor.plcassistant_lt_res_in" in text
    assert "sensor.plcassistant_ft_inlet_in" in text
    assert "sensor.plcassistant_status" in text
    assert "sensor.plcassistant_mode" in text
    assert "type: glance" in text
    assert "custom:plcassistant-pid-card" in text
    assert text.lstrip().startswith("# plcassistant_dashboard_version:")
    assert "plcassistant_dashboard_version: 28" in text
    # Process display is sensors (SWD-170); Numbers remain for nudges only.
    assert "entity: number.plcassistant_lt_tank_in" not in text
    assert "entity: sensor.plcassistant_ft_inlet_in" in text
    # SCADA: no always-on history graph — tap glance entities for more-info/history.
    assert "type: history-graph" not in text
    assert "type: markdown" not in text
    assert "custom:plcassistant-block-list-card" not in text


def test_setup_entry_calls_sidebar_dashboard() -> None:
    src = (CC / "__init__.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_setup_entry":
            body = ast.unparse(node)
            assert "async_setup_sidebar_dashboard" in body
            found = True
    assert found


def test_lovelace_readme_is_auto_not_paste() -> None:
    text = (CC / "lovelace" / "README.md").read_text(encoding="utf-8")
    lower = text.lower()
    assert "sidebar" in lower
    assert "automatic" in lower or "registers" in lower or "no copy/paste" in lower
    assert "Settings → Dashboards → Add dashboard" not in text
    # Must not instruct users to paste YAML as the install path
    assert "paste the contents" not in lower
    assert "open the yaml and paste" not in lower


def test_root_readme_mentions_sidebar_not_manual_paste() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "sidebar" in text.lower()
    assert "registers it in the HA sidebar" in text
    assert "Settings → Dashboards → Add dashboard" not in text
    assert "paste the contents" not in text.lower()


def test_ensure_does_not_overwrite_custom(tmp_path) -> None:
    mod = _load("plcassistant_lovelace_dashboard3", CC / "lovelace_dashboard.py")

    class FakeConfig:
        def path(self, *parts: str) -> str:
            return str(tmp_path.joinpath(*parts))

    class FakeHass:
        config = FakeConfig()

    dest = tmp_path / "dashboards" / "plcassistant.yaml"
    dest.parent.mkdir(parents=True)
    dest.write_text("# operator edit\nviews: []\n", encoding="utf-8")

    out = mod.ensure_dashboard_yaml(FakeHass())  # type: ignore[arg-type]
    assert out == dest
    assert dest.read_text(encoding="utf-8").startswith("# operator edit")


def test_ensure_refreshes_stock_board_missing_status(tmp_path) -> None:
    """SWD-135: prior stock Lovelace without status card is upgraded."""
    mod = _load("plcassistant_lovelace_dashboard3b", CC / "lovelace_dashboard.py")

    class FakeConfig:
        def path(self, *parts: str) -> str:
            return str(tmp_path.joinpath(*parts))

    class FakeHass:
        config = FakeConfig()

    dest = tmp_path / "dashboards" / "plcassistant.yaml"
    dest.parent.mkdir(parents=True)
    dest.write_text(
        "title: PLCAssistant\nviews:\n"
        "  - cards:\n"
        "      - type: entities\n"
        "        entities:\n"
        "          - entity: button.plcassistant_start\n",
        encoding="utf-8",
    )
    out = mod.ensure_dashboard_yaml(FakeHass())  # type: ignore[arg-type]
    text = out.read_text(encoding="utf-8")
    assert "sensor.plcassistant_status" in text
    assert "sensor.plcassistant_mode" in text
    assert "plcassistant_dashboard_version: 28" in text


def test_ensure_refreshes_stock_board_old_dashboard_version(tmp_path) -> None:
    """SWD-170: stock boards on version 14 get plant IN sensors on Process card."""
    mod = _load("plcassistant_lovelace_dashboard3c", CC / "lovelace_dashboard.py")

    class FakeConfig:
        def path(self, *parts: str) -> str:
            return str(tmp_path.joinpath(*parts))

    class FakeHass:
        config = FakeConfig()

    dest = tmp_path / "dashboards" / "plcassistant.yaml"
    dest.parent.mkdir(parents=True)
    dest.write_text(
        "# plcassistant_dashboard_version: 14\n"
        "title: PLCAssistant\nviews:\n"
        "  - cards:\n"
        "      - type: entities\n"
        "        entities:\n"
        "          - entity: sensor.plcassistant_status\n"
        "          - entity: button.plcassistant_start\n"
        "          - entity: number.plcassistant_lt_tank_in\n",
        encoding="utf-8",
    )
    out = mod.ensure_dashboard_yaml(FakeHass())  # type: ignore[arg-type]
    text = out.read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 28" in text
    assert "path: dynamics" in text
    assert "/api/plcassistant/dynamics/ui" in text
    assert "path: datablocks" in text
    assert "/api/plcassistant/datablocks/ui" in text
    assert "sensor.plcassistant_lt_tank_in" in text
    assert "entity: number.plcassistant_lt_tank_in" not in text
    assert "type: glance" in text
    assert "custom:plcassistant-pid-card" in text


def test_ensure_refreshes_stock_board_version_27_to_28(tmp_path) -> None:
    """SWD-229: stock boards on dashboard version 27 refresh to SCADA v28."""
    mod = _load("plcassistant_lovelace_dashboard3e", CC / "lovelace_dashboard.py")

    class FakeConfig:
        def path(self, *parts: str) -> str:
            return str(tmp_path.joinpath(*parts))

    class FakeHass:
        config = FakeConfig()

    dest = tmp_path / "dashboards" / "plcassistant.yaml"
    dest.parent.mkdir(parents=True)
    dest.write_text(
        "# plcassistant_dashboard_version: 27\n"
        "title: PLCAssistant\nviews:\n"
        "  - cards:\n"
        "      - type: markdown\n"
        "        content: changelog\n"
        "      - type: history-graph\n"
        "        entities:\n"
        "          - entity: sensor.plcassistant_lt_tank_in\n"
        "      - type: entities\n"
        "        entities:\n"
        "          - entity: sensor.plcassistant_status\n"
        "          - entity: button.plcassistant_start\n"
        "          - entity: custom:plcassistant-block-list-card\n",
        encoding="utf-8",
    )
    out = mod.ensure_dashboard_yaml(FakeHass())  # type: ignore[arg-type]
    text = out.read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 28" in text
    assert "type: glance" in text
    assert "custom:plcassistant-pid-card" in text
    assert "type: markdown" not in text
    assert "type: history-graph" not in text
    assert "custom:plcassistant-block-list-card" not in text


def test_ensure_preserves_stock_board_version_28(tmp_path) -> None:
    """SWD-229: current stock v28 must not be rewritten on ensure."""
    mod = _load("plcassistant_lovelace_dashboard3f", CC / "lovelace_dashboard.py")

    class FakeConfig:
        def path(self, *parts: str) -> str:
            return str(tmp_path.joinpath(*parts))

    class FakeHass:
        config = FakeConfig()

    dest = tmp_path / "dashboards" / "plcassistant.yaml"
    dest.parent.mkdir(parents=True)
    original = (
        "# plcassistant_dashboard_version: 28\n"
        "title: PLCAssistant\nviews:\n"
        "  - cards:\n"
        "      - type: entities\n"
        "        entities:\n"
        "          - entity: sensor.plcassistant_status\n"
        "          - entity: button.plcassistant_start\n"
        "          - entity: button.plcassistant_operator_note\n"
    )
    dest.write_text(original, encoding="utf-8")
    out = mod.ensure_dashboard_yaml(FakeHass())  # type: ignore[arg-type]
    assert out.read_text(encoding="utf-8") == original


def test_ensure_preserves_status_board_without_version_marker(tmp_path) -> None:
    """SWD-137: status present + no version marker must not be clobbered."""
    mod = _load("plcassistant_lovelace_dashboard3d", CC / "lovelace_dashboard.py")

    class FakeConfig:
        def path(self, *parts: str) -> str:
            return str(tmp_path.joinpath(*parts))

    class FakeHass:
        config = FakeConfig()

    dest = tmp_path / "dashboards" / "plcassistant.yaml"
    dest.parent.mkdir(parents=True)
    original = (
        "title: PLCAssistant\nviews:\n"
        "  - cards:\n"
        "      - type: entities\n"
        "        entities:\n"
        "          - entity: sensor.plcassistant_status\n"
        "          - entity: button.plcassistant_start\n"
        "          - entity: button.plcassistant_operator_note\n"
    )
    dest.write_text(original, encoding="utf-8")
    out = mod.ensure_dashboard_yaml(FakeHass())  # type: ignore[arg-type]
    assert out.read_text(encoding="utf-8") == original


def test_ensure_writes_when_missing(tmp_path) -> None:
    mod = _load("plcassistant_lovelace_dashboard4", CC / "lovelace_dashboard.py")

    class FakeConfig:
        def path(self, *parts: str) -> str:
            return str(tmp_path.joinpath(*parts))

    class FakeHass:
        config = FakeConfig()

    out = mod.ensure_dashboard_yaml(FakeHass())  # type: ignore[arg-type]
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "title: PLCAssistant" in text
    assert "button.plcassistant_start" in text


def test_run_sh_refreshes_stock_missing_status_not_custom() -> None:
    """App Start refreshes stock boards lacking status; still no -nt clobber."""
    text = (ROOT / "plc_assistant" / "run.sh").read_text(encoding="utf-8")
    assert "install_lovelace_dashboard()" in text
    assert "sensor.plcassistant_status" in text
    assert "button.plcassistant_start" in text
    assert "seeded default" in text or "mqtt_broker=core-mosquitto" in text
    # Explicit old versions only — refresh 1–27 stock boards to v28 (SWD-229).
    assert "plcassistant_dashboard_version:[[:space:]]*([1-9]|1[0-9]|2[0-7])" in text
    assert "title: PLCAssistant" in text or "PLCAssistant" in text
    assert "request_core_restart_after_sync" in text
    assert "supervisor/core/restart" in text
    assert "PLCASSISTANT_AUTO_CORE_RESTART" in text
    assert "PLCASSISTANT_HA_CONFIG" in text
    assert "! grep -q 'plcassistant_dashboard_version: 17'" not in text
    # Regression: never refresh-on-newer (would clobber operator edits).
    assert 'src_dash}" -nt' not in text
    assert "[ \"${src_dash}\" -nt" not in text


def test_panel_exists_helper_degrades_without_ha() -> None:
    mod = _load("plcassistant_lovelace_dashboard5", CC / "lovelace_dashboard.py")

    class FakeHass:
        data = {"frontend_panels": {"plcassistant-skid": object()}}

    assert mod._panel_exists(FakeHass(), "plcassistant-skid") is True  # type: ignore[arg-type]
    assert mod._panel_exists(FakeHass(), "other-panel") is False  # type: ignore[arg-type]