"""Pending Core restart after thin-integration sync (SWD-168)."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CC = ROOT / "custom_components" / "plcassistant"


def _load_version_sync(tmp_manifest: pathlib.Path | None = None):
    """Load version_sync without Home Assistant (CI has no HA package)."""
    path = CC / "version_sync.py"
    # Isolate module state per test when we mutate LOADED_VERSION.
    name = f"plcassistant_version_sync_{id(tmp_manifest)}_{len(sys.modules)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_loaded_matches_manifest_when_fresh():
    mod = _load_version_sync()
    assert mod.LOADED_VERSION == json.loads(
        (CC / "manifest.json").read_text(encoding="utf-8")
    )["version"]
    assert mod.pending_core_restart() is False
    assert mod.disk_version() == mod.LOADED_VERSION


def test_pending_restart_when_disk_version_differs(tmp_path):
    mod = _load_version_sync()
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps({"domain": "plcassistant", "version": "9.9.9"}), encoding="utf-8")
    assert mod.pending_core_restart(loaded_version="0.1.0", manifest_path=man) is True
    assert mod.pending_core_restart(loaded_version="9.9.9", manifest_path=man) is False
    loaded, on_disk = mod.pending_versions(loaded_version="0.1.0", manifest_path=man)
    assert loaded == "0.1.0"
    assert on_disk == "9.9.9"


def test_corrupt_manifest_shapes_raise_or_pending_false(tmp_path):
    mod = _load_version_sync()
    bad_list = tmp_path / "list.json"
    bad_list.write_text("[]", encoding="utf-8")
    try:
        mod.read_manifest_version(bad_list)
        raised = False
    except ValueError:
        raised = True
    assert raised
    assert mod.pending_core_restart(loaded_version="0.1.0", manifest_path=bad_list) is False

    missing = tmp_path / "missing.json"
    assert mod.pending_core_restart(loaded_version="0.1.0", manifest_path=missing) is False

    blank = tmp_path / "blank.json"
    blank.write_text(json.dumps({"version": "  "}), encoding="utf-8")
    assert mod.pending_core_restart(loaded_version="0.1.0", manifest_path=blank) is False


def test_restart_required_summary_is_hacs_style_alert():
    mod = _load_version_sync()
    assert "ha-alert" in mod.RESTART_REQUIRED_SUMMARY
    assert "Restart of Home Assistant required" in mod.RESTART_REQUIRED_SUMMARY
    assert mod.ISSUE_RESTART_REQUIRED == "restart_required"


def test_update_platform_wiring():
    init_text = (CC / "__init__.py").read_text(encoding="utf-8")
    assert "Platform.UPDATE" in init_text
    update_text = (CC / "update.py").read_text(encoding="utf-8")
    assert "PlcAssistantRestartUpdateEntity" in update_text
    assert "RESTART_REQUIRED_SUMMARY" in update_text
    assert "async_sync_restart_required_issue" in update_text
    assert "async_create_issue" in update_text
    assert "async_delete_issue" in update_text
    assert "Do not clear a pending restart alert" in update_text
    assert "restart_pending_snapshot" not in update_text
    repairs = (CC / "repairs.py").read_text(encoding="utf-8")
    assert "RestartRequiredRepairFlow" in repairs
    assert 'async_call("homeassistant", "restart")' in repairs
    assert "description_placeholders" in repairs
    assert "ConfirmRepairFlow" in repairs
    strings = json.loads((CC / "strings.json").read_text(encoding="utf-8"))
    assert "restart_required" in strings["issues"]
    assert "{loaded}" in strings["issues"]["restart_required"]["description"]
    assert "{disk}" in strings["issues"]["restart_required"]["description"]


def test_updates_doc_mentions_restart_required_ui():
    text = (ROOT / "docs" / "packaging" / "04-updates.md").read_text(encoding="utf-8")
    assert "Restart of Home Assistant required" in text
    assert "0.1.27" in text
    assert "Settings → System → Updates" in text or "System → Updates" in text
    assert "first upgrade" in text.lower() or "later App sync" in text
