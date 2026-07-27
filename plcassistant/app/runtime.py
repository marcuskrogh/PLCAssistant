"""HA App runtime: HTTP editor + optional MQTT scan loop (SWD-84)."""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Callable

from plcassistant.app.server import AppState, run_app
from plcassistant.io.image import IoImage
from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttBus, MqttIoBridge
from plcassistant.io.mqtt_entity_bridge import default_wedge_binding_config
from plcassistant.io.mqtt_topics import DEFAULT_INSTANCE_ID


def load_options(path: str | None) -> dict[str, Any]:
    """Load Supervisor ``/data/options.json`` (or empty dict)."""
    if not path or not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def declare_default_image(image: IoImage | None = None) -> IoImage:
    """Declare default packaging tags on an image."""
    if image is None:
        image = IoImage()
    cfg = default_wedge_binding_config()
    for name, meta in cfg["tags"].items():
        if name not in image.names():
            image.declare(name, default=meta.get("default", 0.0))
    return image


def default_scan_logic(image: IoImage) -> None:
    """Demo logic: CMD_SPEED = LT_TANK * 100 when both tags exist."""
    names = image.names()
    if "LT_TANK" in names and "CMD_SPEED" in names:
        try:
            level = float(image.get_value("LT_TANK"))
        except (TypeError, ValueError):
            level = 0.0
        image.set_output("CMD_SPEED", level * 100.0)


def build_bus_from_options(options: dict[str, Any]) -> MqttBus | None:
    """Return a live paho bus when MQTT is configured; None to skip."""
    # Explicit disable for tests / editor-only.
    if os.environ.get("PLCASSISTANT_MQTT", "1") in ("0", "false", "no"):
        return None
    if os.environ.get("PLCASSISTANT_MQTT_BUS") == "memory":
        return InMemoryMqttBus()
    host = str(options.get("mqtt_broker") or os.environ.get("PLCASSISTANT_MQTT_BROKER") or "")
    if not host:
        # HA App default when options present without broker key.
        host = "core-mosquitto" if options else ""
    if not host:
        return None
    port = int(options.get("mqtt_port") or os.environ.get("PLCASSISTANT_MQTT_PORT") or 1883)
    username = options.get("mqtt_username") or os.environ.get("PLCASSISTANT_MQTT_USERNAME") or ""
    password = options.get("mqtt_password") or os.environ.get("PLCASSISTANT_MQTT_PASSWORD") or ""
    try:
        from plcassistant.io.mqtt_paho import PahoMqttBus
    except ImportError:
        return None
    try:
        return PahoMqttBus(
            host,
            port,
            username=str(username) or None,
            password=str(password) or None,
        )
    except Exception:
        # Broker unreachable at start — editor still runs; MQTT optional retry later.
        return None


class MqttScanLoop:
    """Background Soft-PLC scan driving ``MqttIoBridge``."""

    def __init__(
        self,
        bridge: MqttIoBridge,
        image: IoImage,
        *,
        logic: Callable[[IoImage], None] = default_scan_logic,
        period_s: float = 0.1,
    ) -> None:
        self.bridge = bridge
        self.image = image
        self.logic = logic
        self.period_s = period_s
        self.running = False
        self.commands: list[str] = []
        self._thread: threading.Thread | None = None
        self.bridge.on_command("start", lambda: self.commands.append("start"))
        self.bridge.on_command("stop", lambda: self.commands.append("stop"))
        self.bridge.on_command("reset", lambda: self.commands.append("reset"))

    def start(self) -> None:
        if self._thread is not None:
            return
        self.running = True
        self.bridge.start()
        self.bridge.publish_status("running")
        self._thread = threading.Thread(target=self._run, name="mqtt-scan", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self.bridge.publish_status("stopped")

    def scan_once(self) -> None:
        self.bridge.apply_inputs(self.image, clear=True)
        drained = self.bridge.drain_commands()
        if drained:
            self.commands.extend(drained)
        self.logic(self.image)
        self.bridge.publish_outputs(self.image)

    def _run(self) -> None:
        while self.running:
            t0 = time.monotonic()
            try:
                self.scan_once()
            except Exception:
                # Keep the loop alive; editor remains reachable.
                pass
            elapsed = time.monotonic() - t0
            time.sleep(max(0.0, self.period_s - elapsed))


def run_ha_runtime(
    *,
    host: str = "0.0.0.0",
    port: int = 8099,
    program_path: str | None = None,
    options_path: str | None = None,
    bus: MqttBus | None = None,
    serve_forever: bool = True,
) -> tuple[Any, MqttScanLoop | None]:
    """Start editor HTTP server and optional MQTT scan loop.

    Returns ``(HTTPServer, scan_loop_or_None)``.
    """
    options = load_options(options_path or os.environ.get("PLCASSISTANT_OPTIONS_PATH"))
    instance_id = str(
        options.get("instance_id")
        or os.environ.get("PLCASSISTANT_INSTANCE_ID")
        or DEFAULT_INSTANCE_ID
    )
    state = AppState(program_path=program_path)
    server = run_app(host=host, port=port, state=state)

    if bus is None:
        bus = build_bus_from_options(options)

    loop: MqttScanLoop | None = None
    if bus is not None:
        image = declare_default_image()
        bridge = MqttIoBridge(bus, instance_id=instance_id)
        loop = MqttScanLoop(bridge, image)
        loop.start()

    if serve_forever:
        try:
            server.serve_forever()
        finally:
            if loop is not None:
                loop.stop()
    return server, loop


__all__ = [
    "MqttScanLoop",
    "build_bus_from_options",
    "declare_default_image",
    "default_scan_logic",
    "load_options",
    "run_ha_runtime",
]
