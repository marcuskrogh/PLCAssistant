"""Shared HA-config bridge between Soft-PLC App and thin integration (SWD-139+).

Both sides mount the Home Assistant config directory. Soft-PLC writes a runtime
snapshot; the integration polls it when MQTT is silent. Operator cmds and IN
request tags (e.g. ``SP_LEVEL_REQ``) travel the other way via shared files.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

RUNTIME_REL = "plcassistant/runtime.json"
CMD_REL = "plcassistant/cmd.json"
INPUTS_REL = "plcassistant/inputs.json"
VALID_CMDS = frozenset({"start", "stop", "reset"})


def ha_config_root(explicit: str | None = None) -> Path | None:
    """Return HA config root when available (App mount or env)."""
    raw = explicit or os.environ.get("PLCASSISTANT_HA_CONFIG") or ""
    if not raw:
        # Default Supervisor mount for homeassistant_config.
        raw = "/homeassistant"
    path = Path(raw)
    if not path.is_dir():
        return None
    return path


def runtime_path(root: Path | None = None) -> Path | None:
    base = root if root is not None else ha_config_root()
    if base is None:
        return None
    return base / RUNTIME_REL


def cmd_path(root: Path | None = None) -> Path | None:
    base = root if root is not None else ha_config_root()
    if base is None:
        return None
    return base / CMD_REL


def inputs_path(root: Path | None = None) -> Path | None:
    base = root if root is not None else ha_config_root()
    if base is None:
        return None
    return base / INPUTS_REL


def write_runtime_snapshot(snapshot: dict[str, Any], root: Path | None = None) -> bool:
    """Atomically write Soft-PLC snapshot for the thin integration. True on success."""
    path = runtime_path(root)
    if path is None:
        return False
    body = dict(snapshot)
    body.setdefault("ts", time.time())
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(body, separators=(",", ":")), encoding="utf-8")
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def read_runtime_snapshot(root: Path | None = None) -> dict[str, Any] | None:
    """Read Soft-PLC snapshot written under HA config, or None."""
    path = runtime_path(root)
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_cmd(name: str, root: Path | None = None) -> bool:
    """Queue a one-shot operator command for Soft-PLC. True on success."""
    cmd = str(name).lower().strip()
    if cmd not in VALID_CMDS:
        return False
    path = cmd_path(root)
    if path is None:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"cmd": cmd, "ts": time.time()}, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def drain_cmd(root: Path | None = None) -> str | None:
    """Return and clear a pending operator command, or None."""
    path = cmd_path(root)
    if path is None or not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        path.unlink(missing_ok=True)
    except OSError:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    cmd = str(data.get("cmd") or "").lower().strip()
    return cmd if cmd in VALID_CMDS else None


def write_input_tag(
    tag: str,
    value: Any,
    status: str = "GOOD",
    reason: str | None = None,
    root: Path | None = None,
) -> bool:
    """Merge one operator IN tag into the retained inputs file (SWD-141)."""
    name = str(tag or "").strip()
    if not name:
        return False
    path = inputs_path(root)
    if path is None:
        return False
    existing: dict[str, Any] = {}
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            existing = {}
    tags = existing.get("tags") if isinstance(existing.get("tags"), dict) else {}
    tags = dict(tags)
    tags[name] = {"value": value, "status": status, "reason": reason}
    body = {"tags": tags, "ts": time.time()}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(body, separators=(",", ":")), encoding="utf-8")
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def read_inputs(root: Path | None = None) -> dict[str, Any] | None:
    """Read retained operator IN tags under HA config, or None."""
    path = inputs_path(root)
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


__all__ = [
    "CMD_REL",
    "INPUTS_REL",
    "RUNTIME_REL",
    "VALID_CMDS",
    "cmd_path",
    "drain_cmd",
    "ha_config_root",
    "inputs_path",
    "read_inputs",
    "read_runtime_snapshot",
    "runtime_path",
    "write_cmd",
    "write_input_tag",
    "write_runtime_snapshot",
]
