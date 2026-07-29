"""Operator Soft-PLC port for the App HTTP layer.

Owns runtime snapshot / cmd routing so ``AppState`` stays an editor container
and does not import ``runtime`` (scan loop) directly.
"""

from __future__ import annotations

from typing import Any

from plcassistant.app.default_image import declare_default_image
from plcassistant.io.mqtt_entity_bridge import default_wedge_binding_config
from plcassistant.io.mqtt_topics import DEFAULT_INSTANCE_ID


class OperatorRuntime:
    """Read Soft-PLC tags and issue start/stop/reset without owning the scan loop."""

    def __init__(self) -> None:
        self.instance_id: str = DEFAULT_INSTANCE_ID
        self._mqtt_life: Any = None
        self._fallback_image = declare_default_image()

    def attach(self, lifecycle: Any) -> None:
        """Attach MQTT scan lifecycle so the UI can read tags and issue cmds."""
        self._mqtt_life = lifecycle

    def _scan_loop(self) -> Any | None:
        life = self._mqtt_life
        if life is None:
            return None
        return getattr(life, "loop", None)

    def snapshot(self) -> dict[str, Any]:
        """JSON-serialisable Soft-PLC status for the operator dashboard.

        Status vocabulary for the dashboard chip:
        - ``running`` / ``stopped`` — MQTT scan loop attached
        - ``offline`` — no MQTT loop yet (never claim scan active here)
        Scan-thread faults publish on the MQTT status topic; they are not a
        separate chip enum until the UI reads that topic.
        """
        loop = self._scan_loop()
        units = {
            name: meta.get("unit")
            for name, meta in default_wedge_binding_config()["tags"].items()
        }
        if loop is not None:
            image = loop.image
            snap_all = image.snapshot()
            scanning = bool(loop.scanning)
            status = "running" if scanning else "stopped"
            mqtt = True
        else:
            image = self._fallback_image
            snap_all = image.snapshot()
            scanning = False
            status = "offline"
            mqtt = False
        tags: dict[str, Any] = {}
        for name in image.names():
            snap = snap_all[name]
            reason = snap.quality.reason.value if snap.quality.reason else None
            tags[name] = {
                "value": snap.value,
                "status": snap.quality.status.value,
                "reason": reason,
                "unit": units.get(name),
            }
        return {
            "instance_id": self.instance_id,
            "status": status,
            "scanning": scanning,
            "mqtt": mqtt,
            "tags": tags,
        }

    def issue_cmd(self, name: str) -> dict[str, Any]:
        """Start / stop / reset via scan loop (enqueued), or defer while offline."""
        cmd = str(name).lower().strip()
        if cmd not in ("start", "stop", "reset"):
            raise ValueError(f"Unknown command {name!r}")
        life = self._mqtt_life
        if life is not None and hasattr(life, "enqueue_command"):
            life.enqueue_command(cmd)
        elif self._scan_loop() is not None:
            self._scan_loop().issue_command(cmd)
        else:
            if cmd == "reset":
                self._fallback_image = declare_default_image()
        return self.snapshot()


__all__ = ["OperatorRuntime"]
