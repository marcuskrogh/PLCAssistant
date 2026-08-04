"""Shared HA-config bridge between Soft-PLC App and thin integration (SWD-139+).

Both sides mount the Home Assistant config directory. Soft-PLC writes a runtime
snapshot; the integration polls it when MQTT is silent. Operator cmds, IN
request tags (e.g. ``SP_LEVEL_REQ``), and plant IN PVs (SWD-171 MQTT-silent
fallback) travel via shared files.
"""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Any, Mapping

RUNTIME_REL = "plcassistant/runtime.json"
CMD_REL = "plcassistant/cmd.json"
INPUTS_REL = "plcassistant/inputs.json"
PLANT_CAPACITY_REL = "plcassistant/plant_capacity.json"
VALID_CMDS = frozenset({"start", "stop", "reset"})
DEFAULT_Q_PUMP_MAX = 8.0

# Plant PVs on the file bridge expire when the simulator stops flushing (SWD-171).
# Operator requests (SP_LEVEL_REQ) stay retained indefinitely.
PLANT_FILE_INPUT_TAGS = frozenset({"LT_TANK", "LT_RES", "FT_INLET"})
PLANT_FILE_STALE_S = 5.0


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


def plant_capacity_path(root: Path | None = None) -> Path | None:
    base = root if root is not None else ha_config_root()
    if base is None:
        return None
    return base / PLANT_CAPACITY_REL


def write_plant_capacity(
    q_pump_max: float,
    *,
    root: Path | None = None,
    source: str | None = None,
) -> bool:
    """Persist plant max pump flow for Soft-PLC cascade sync (SWD-251)."""
    path = plant_capacity_path(root)
    if path is None:
        return False
    try:
        q = float(q_pump_max)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(q) or q <= 0.0:
        return False
    body: dict[str, Any] = {
        "q_pump_max": q,
        "ts": time.time(),
    }
    if source:
        body["source"] = str(source)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(body, separators=(",", ":")), encoding="utf-8")
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def read_plant_capacity(root: Path | None = None) -> float | None:
    """Return ``q_pump_max`` from the capacity bridge, or None if unavailable."""
    path = plant_capacity_path(root)
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        q = float(data.get("q_pump_max"))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(q) or q <= 0.0:
        return None
    return q


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
    """Merge one operator / plant IN tag into the retained inputs file (SWD-141/171)."""
    name = str(tag or "").strip()
    if not name:
        return False
    return write_input_tags(
        {name: {"value": value, "status": status, "reason": reason}},
        root=root,
    )


def write_input_tags(
    tags: Mapping[str, Any],
    root: Path | None = None,
) -> bool:
    """Merge multiple IN tags into ``inputs.json`` in one atomic write (SWD-171).

    Each value may be a raw engineering value or a dict with ``value`` /
    ``status`` / ``reason`` keys. Writers serialize via an advisory lock so
    plant flush and operator SP writes cannot lose each other's merges.
    """
    if not tags:
        return False
    path = inputs_path(root)
    if path is None:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False

    lock_path = path.with_suffix(".lock")
    try:
        lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
    except OSError:
        return False
    try:
        _lock_file(lock_fd)
        existing: dict[str, Any] = {}
        if path.is_file():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    existing = loaded
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                existing = {}
        merged = existing.get("tags") if isinstance(existing.get("tags"), dict) else {}
        merged = dict(merged)
        now = time.time()
        for raw_name, body in tags.items():
            name = str(raw_name or "").strip()
            if not name:
                continue
            if isinstance(body, Mapping) and "value" in body:
                entry = {
                    "value": body.get("value"),
                    "status": body.get("status") or "GOOD",
                    "reason": body.get("reason"),
                    "ts": float(body["ts"]) if body.get("ts") is not None else now,
                }
            else:
                entry = {"value": body, "status": "GOOD", "reason": None, "ts": now}
            merged[name] = entry
        if not merged:
            return False
        payload = {"tags": merged, "ts": now}
        tmp = path.with_name(f"{path.name}.{os.getpid()}.{now}.tmp")
        try:
            tmp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
            os.replace(tmp, path)
            return True
        except OSError:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            return False
    finally:
        try:
            _unlock_file(lock_fd)
        finally:
            os.close(lock_fd)


def read_inputs(root: Path | None = None) -> dict[str, Any] | None:
    """Read retained operator / plant IN tags under HA config, or None."""
    path = inputs_path(root)
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _lock_file(fd: int) -> None:
    try:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_EX)
    except (ImportError, OSError):
        # Best-effort on platforms without flock; unique tmp still helps.
        return


def _unlock_file(fd: int) -> None:
    try:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_UN)
    except (ImportError, OSError):
        return


__all__ = [
    "CMD_REL",
    "DEFAULT_Q_PUMP_MAX",
    "INPUTS_REL",
    "PLANT_CAPACITY_REL",
    "PLANT_FILE_INPUT_TAGS",
    "PLANT_FILE_STALE_S",
    "RUNTIME_REL",
    "VALID_CMDS",
    "cmd_path",
    "drain_cmd",
    "ha_config_root",
    "inputs_path",
    "plant_capacity_path",
    "read_inputs",
    "read_plant_capacity",
    "read_runtime_snapshot",
    "runtime_path",
    "write_cmd",
    "write_input_tag",
    "write_input_tags",
    "write_plant_capacity",
    "write_runtime_snapshot",
]
