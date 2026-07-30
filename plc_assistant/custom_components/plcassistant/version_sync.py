"""Detect thin-integration disk vs loaded version (SWD-168).

After App Update, ``run.sh`` syncs ``custom_components/plcassistant`` onto the
HA config share. Core keeps the previously imported modules until restart.
Comparing the version captured at import time to ``manifest.json`` on disk is
the pending-restart signal — same idea as HACS ``pending_restart``.
"""

from __future__ import annotations

import json
from pathlib import Path

_INTEGRATION_ROOT = Path(__file__).resolve().parent
_MANIFEST_PATH = _INTEGRATION_ROOT / "manifest.json"

# Captured once when Core imports this package (before any later App sync).
LOADED_VERSION: str = "0.0.0"

# Shown on Settings → System → Updates (HACS-compatible markup).
RESTART_REQUIRED_SUMMARY = (
    "<ha-alert alert-type='error'>Restart of Home Assistant required</ha-alert>"
)

ISSUE_RESTART_REQUIRED = "restart_required"


def read_manifest_version(manifest_path: Path | None = None) -> str:
    """Return the ``version`` field from a manifest.json path."""
    path = manifest_path if manifest_path is not None else _MANIFEST_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"manifest must be a JSON object: {path}")
    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError(f"manifest missing version: {path}")
    return version.strip()


def disk_version(manifest_path: Path | None = None) -> str:
    """Current on-disk integration version (re-read; may change after App sync)."""
    return read_manifest_version(manifest_path)


def pending_core_restart(
    loaded_version: str | None = None,
    *,
    manifest_path: Path | None = None,
) -> bool:
    """True when files on disk are a different version than Core has loaded."""
    loaded = LOADED_VERSION if loaded_version is None else loaded_version
    try:
        on_disk = disk_version(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError, TypeError, AttributeError):
        return False
    return on_disk != loaded


def pending_versions(
    loaded_version: str | None = None,
    *,
    manifest_path: Path | None = None,
) -> tuple[str, str]:
    """Return ``(loaded_version, disk_version)`` for UI placeholders."""
    loaded = LOADED_VERSION if loaded_version is None else loaded_version
    return loaded, disk_version(manifest_path)


def _init_loaded_version() -> str:
    try:
        return read_manifest_version()
    except (OSError, ValueError, json.JSONDecodeError, TypeError, AttributeError):
        return "0.0.0"


LOADED_VERSION = _init_loaded_version()

__all__ = [
    "ISSUE_RESTART_REQUIRED",
    "LOADED_VERSION",
    "RESTART_REQUIRED_SUMMARY",
    "disk_version",
    "pending_core_restart",
    "pending_versions",
    "read_manifest_version",
]
