"""HA App runtime: HTTP editor + optional MQTT scan loop (SWD-84)."""

from __future__ import annotations

import json
import math
import os
import threading
import time
from typing import Any, Callable, Mapping

from plcassistant.app.default_image import declare_default_image
from plcassistant.app.server import AppState, run_app
from plcassistant.app.skid_scan import SkidImageLogic
from plcassistant.io.ha_config_bridge import (
    PLANT_FILE_INPUT_TAGS,
    PLANT_FILE_STALE_S,
    drain_cmd,
    read_inputs,
    write_runtime_snapshot,
)
from plcassistant.io.image import IoImage
from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttBus, MqttIoBridge
from plcassistant.io.mqtt_topics import DEFAULT_INSTANCE_ID, MqttTagPayload
from plcassistant.io.pid_loop import all_operator_param_tag_names
from plcassistant.io.quality import QualityStatus, ReasonCode


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


def default_scan_logic(image: IoImage) -> None:
    """Legacy demo mirror (tests). Prefer ``SkidImageLogic`` for HA runtime."""
    names = image.names()
    if "SP_LEVEL_REQ" in names and "SP_LEVEL" in names:
        try:
            image.set_output("SP_LEVEL", float(image.get_value("SP_LEVEL_REQ")))
        except (TypeError, ValueError):
            pass
    if "LT_TANK" in names and "CMD_SPEED" in names:
        try:
            level = float(image.get_value("LT_TANK"))
        except (TypeError, ValueError):
            level = 0.0
        image.set_output("CMD_SPEED", level * 100.0)
    if "FT_INLET" in names and "SP_FLOW" in names:
        try:
            image.set_output("SP_FLOW", float(image.get_value("FT_INLET")))
        except (TypeError, ValueError):
            pass


def build_bus_from_options(
    options: dict[str, Any],
    *,
    instance_id: str | None = None,
    ha_runtime: bool | None = None,
    period_s: float = 0.1,
) -> MqttBus | None:
    """Return a live paho bus when MQTT is configured; None to skip."""
    if os.environ.get("PLCASSISTANT_MQTT", "1") in ("0", "false", "no"):
        return None
    if os.environ.get("PLCASSISTANT_MQTT_BUS") == "memory":
        return InMemoryMqttBus()
    host = str(
        options.get("mqtt_broker") or os.environ.get("PLCASSISTANT_MQTT_BROKER") or ""
    )
    if not host:
        # HA App runtime must always try Supervisor Mosquitto — empty options.json
        # is falsy in Python and previously skipped MQTT forever (SWD-137).
        if ha_runtime is None:
            ha_runtime = os.environ.get("PLCASSISTANT_HA_RUNTIME", "") == "1"
        host = "core-mosquitto" if ha_runtime else ""
    if not host:
        return None
    port = int(options.get("mqtt_port") or os.environ.get("PLCASSISTANT_MQTT_PORT") or 1883)
    username = options.get("mqtt_username") or os.environ.get("PLCASSISTANT_MQTT_USERNAME") or ""
    password = options.get("mqtt_password") or os.environ.get("PLCASSISTANT_MQTT_PASSWORD") or ""
    iid = str(
        instance_id
        or options.get("instance_id")
        or os.environ.get("PLCASSISTANT_INSTANCE_ID")
        or DEFAULT_INSTANCE_ID
    )
    try:
        from plcassistant.io.mqtt_paho import PahoMqttBus
        from plcassistant.io.mqtt_topics import status_topic
    except ImportError:
        print("PLCAssistant: paho-mqtt not installed; MQTT scan disabled", flush=True)
        return None
    will_topic = status_topic(iid)
    # Keep scan_period_s on retained LWT so observe still works when offline (SWD-145).
    will_payload = json.dumps(
        {"state": "offline", "scan_period_s": float(period_s)}
    ).encode("utf-8")
    try:
        return PahoMqttBus(
            host,
            port,
            username=str(username) or None,
            password=str(password) or None,
            will_topic=will_topic,
            will_payload=will_payload,
        )
    except Exception as exc:  # noqa: BLE001 — keep editor up; retry in background
        print(
            f"PLCAssistant: MQTT connect to {host}:{port} failed: {exc!s}",
            flush=True,
        )
        return None


class MqttLifecycle:
    """Owns optional MQTT scan loop + background connect retry (stoppable)."""

    def __init__(self) -> None:
        self._loop: MqttScanLoop | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._pending_cmds: list[str] = []
        self._on_attach: Callable[[MqttScanLoop], None] | None = None

    @property
    def loop(self) -> MqttScanLoop | None:
        with self._lock:
            return self._loop

    def set_on_attach(self, callback: Callable[[MqttScanLoop], None] | None) -> None:
        """Register a callback invoked once when the scan loop attaches."""
        with self._lock:
            self._on_attach = callback
            loop = self._loop
        if callback is not None and loop is not None:
            callback(loop)

    def attach(self, loop: MqttScanLoop) -> None:
        with self._lock:
            if self._stop.is_set():
                # Shutdown already requested — do not publish a live loop.
                return
            pending = tuple(self._pending_cmds)
            self._pending_cmds.clear()
            # Flush under the lock before publishing ``loop`` so a concurrent
            # HTTP cmd cannot race ahead of deferred connect-window intent.
            for name in pending:
                loop.issue_command(name)
            self._loop = loop
            callback = self._on_attach
        if callback is not None:
            callback(loop)

    def enqueue_command(self, name: str) -> None:
        """Queue a cmd for the scan loop; defer until attach if not connected."""
        cmd = str(name).lower().strip()
        if cmd not in ("start", "stop", "reset"):
            raise ValueError(f"Unknown command {name!r}")
        with self._lock:
            loop = self._loop
            if loop is None:
                self._pending_cmds.append(cmd)
                return
        loop.issue_command(cmd)

    def wait(self, timeout: float) -> bool:
        """Block until stop requested or *timeout* seconds. True if stopped."""
        return self._stop.wait(timeout)

    def stopped(self) -> bool:
        return self._stop.is_set()

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            loop = self._loop
            self._loop = None
            self._pending_cmds.clear()
        if loop is not None:
            loop.stop()


class MqttScanLoop:
    """Background Soft-PLC scan driving ``MqttIoBridge``."""

    # Republish retained status so HA sensors that missed the boot retain still
    # recover without an operator Start/Stop (SWD-136).
    STATUS_HEARTBEAT_S = 2.0
    FILE_BRIDGE_PERIOD_S = 1.0
    # Operator request + plant IN fallback when MQTT plant→App is silent (SWD-171).
    # Live MQTT still wins on the same scan for plant PVs (applied after file hydrate).
    # Operator tags are re-applied from file after MQTT so HA seed beats stale retain
    # (SWD-222).
    _FILE_INPUT_TAGS = frozenset(
        {
            "SP_LEVEL_REQ",
            "SP_LEVEL_MAN",
            "SP_LEVEL_AUTO",
            "SP_LEVEL_REM",
            "LEVEL_MODE",
            "SP_FLOW_MAN",
            "SP_FLOW_REQ",
            "SP_FLOW_REM",
            "FLOW_MODE",
            "CO_LEVEL_MAN",
            "CO_FLOW_MAN",
            *all_operator_param_tag_names(),
            "LT_TANK",
            "LT_RES",
            "FT_INLET",
        }
    )
    _OPERATOR_FILE_TAGS = frozenset(
        {
            "SP_LEVEL_REQ",
            "SP_LEVEL_MAN",
            "SP_LEVEL_AUTO",
            "SP_LEVEL_REM",
            "LEVEL_MODE",
            "SP_FLOW_MAN",
            "SP_FLOW_REQ",
            "SP_FLOW_REM",
            "FLOW_MODE",
            "CO_LEVEL_MAN",
            "CO_FLOW_MAN",
            *all_operator_param_tag_names(),
        }
    )

    def __init__(
        self,
        bridge: MqttIoBridge,
        image: IoImage,
        *,
        logic: Callable[[IoImage], None] | None = None,
        period_s: float = 0.1,
    ) -> None:
        self.bridge = bridge
        self.image = image
        self.period_s = period_s
        self.logic: Callable[[IoImage], None] = (
            logic if logic is not None else SkidImageLogic(period_s=period_s)
        )
        # Boot stopped — operator Start (HMI / MQTT cmd) begins control.
        self.scanning = False
        self.commands: list[str] = []
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._alive = False
        self._last_status_heartbeat = 0.0
        self._last_file_bridge = 0.0
        # Handlers optional; scan_once applies drained cmds on the scan thread.
        self.bridge.on_command("start", lambda: None)
        self.bridge.on_command("stop", lambda: None)
        self.bridge.on_command("reset", lambda: None)
    def _scan_period_s(self) -> float:
        """Configured period — prefer active project on the skid loader."""
        logic = self.logic
        skid = getattr(logic, "skid", None)
        if skid is not None:
            return float(skid.config.scan.scan_period_s)
        return float(self.period_s)

    def _status_extras(self) -> dict[str, Any]:
        """MODE / scan period extras for the retained status topic (HMI / SWD-145)."""
        extra: dict[str, Any] = {"scan_period_s": self._scan_period_s()}
        mode = getattr(self.logic, "mode", None)
        if mode is not None:
            value = getattr(mode, "value", mode)
            if value is not None:
                extra["mode"] = str(value)
        return extra

    def _publish_scan_status(self, state: str, **extra: Any) -> None:
        merged = {**self._status_extras(), **extra}
        self.bridge.publish_status(state, **merged)
        self._write_ha_config_runtime(state)

    def _write_ha_config_runtime(self, state: str | None = None) -> None:
        """Mirror Soft-PLC status/tags into HA config for MQTT-silent HMI (SWD-139)."""
        status = state
        if status is None:
            status = "running" if self.scanning else "stopped"
        tags: dict[str, Any] = {}
        # Soft-PLC control/status OUT only (SWD-145: plant PVs are IN, not mirrored).
        for name in (
            "MODE",
            "PERM_OK",
            "TRIP_ACTIVE",
            "CMD_SPEED",
            "SP_LEVEL",
            "SP_FLOW",
            "SP_FLOW_AUTO",
        ):
            if name not in self.image.names():
                continue
            try:
                tags[name] = {"value": self.image.get_value(name)}
            except Exception:  # noqa: BLE001 — best-effort snapshot
                continue
        if write_runtime_snapshot(
            {
                "instance_id": getattr(self.bridge, "instance_id", DEFAULT_INSTANCE_ID),
                "status": status,
                "scanning": bool(self.scanning),
                "mqtt": True,
                "tags": tags,
                **self._status_extras(),
            }
        ):
            self._last_file_bridge = time.monotonic()

    def _apply_file_inputs(self, *, only_tags: frozenset[str] | None = None) -> None:
        """Apply retained HA-config IN tags (SP_LEVEL_REQ + plant PVs) (SWD-141/171).

        ``only_tags`` restricts which file tags are applied (SWD-222 operator
        re-apply after MQTT so seed/modes beat stale broker retain).
        """
        snap = read_inputs()
        if not snap:
            return
        tags = snap.get("tags") if isinstance(snap.get("tags"), dict) else {}
        allowed = self._FILE_INPUT_TAGS if only_tags is None else only_tags
        known = set(self.image.names())
        now = time.time()
        for name, body in tags.items():
            if name not in allowed:
                continue
            if name not in known or not isinstance(body, dict) or "value" not in body:
                continue
            status_raw = str(body.get("status") or "GOOD").upper()
            try:
                status = QualityStatus[status_raw]
            except KeyError:
                status = QualityStatus.GOOD
            reason = None
            reason_raw = body.get("reason")
            if reason_raw:
                try:
                    reason = ReasonCode(str(reason_raw))
                except ValueError:
                    try:
                        reason = ReasonCode[str(reason_raw).upper()]
                    except KeyError:
                        reason = None
            # Plant PVs: stale/missing ts on GOOD → hold last good (skip apply).
            # Do NOT demote to BAD/UNAVAILABLE (that latches LOS; SWD-173).
            # Explicit non-GOOD (BAD/FAULT/…) always applies regardless of age —
            # real LOS must still trip on the file path.
            if name in PLANT_FILE_INPUT_TAGS and status is QualityStatus.GOOD:
                try:
                    tag_ts = float(body["ts"]) if body.get("ts") is not None else None
                except (TypeError, ValueError):
                    tag_ts = None
                if tag_ts is None or (now - tag_ts) > PLANT_FILE_STALE_S:
                    continue
            value: Any = body.get("value")
            if status is QualityStatus.GOOD:
                try:
                    numeric = float(value)
                    if not math.isfinite(numeric):
                        raise ValueError("non-finite")
                    value = numeric
                except (TypeError, ValueError):
                    status = QualityStatus.BAD
                    reason = ReasonCode.FAULT
                    value = None
            try:
                self.image.apply_input(name, value, status, reason)
            except Exception:  # noqa: BLE001 — best-effort IN hydrate
                continue

    def _reapply_fresher_operator_file(
        self, mqtt_samples: Mapping[str, MqttTagPayload]
    ) -> None:
        """Re-apply operator file tags that are fresher than same-scan MQTT (SWD-222).

        Stale broker retain (old/missing ``ts``) loses to HA ``inputs.json`` seed.
        A live MQTT operator write with a newer ``ts`` is not stomped by file.
        """
        if not mqtt_samples:
            return
        snap = read_inputs()
        if not snap:
            return
        tags = snap.get("tags") if isinstance(snap.get("tags"), dict) else {}
        known = set(self.image.names())
        for name, sample in mqtt_samples.items():
            if name not in self._OPERATOR_FILE_TAGS or name not in known:
                continue
            body = tags.get(name)
            if not isinstance(body, dict) or "value" not in body:
                continue
            try:
                file_ts = float(body["ts"]) if body.get("ts") is not None else None
            except (TypeError, ValueError):
                file_ts = None
            mqtt_ts = sample.ts
            # Prefer file when MQTT has no ts (legacy retain) or file is newer.
            if mqtt_ts is not None and file_ts is not None and file_ts < mqtt_ts:
                continue
            status_raw = str(body.get("status") or "GOOD").upper()
            try:
                status = QualityStatus[status_raw]
            except KeyError:
                status = QualityStatus.GOOD
            reason = None
            reason_raw = body.get("reason")
            if reason_raw:
                try:
                    reason = ReasonCode(str(reason_raw))
                except ValueError:
                    try:
                        reason = ReasonCode[str(reason_raw).upper()]
                    except KeyError:
                        reason = None
            value: Any = body.get("value")
            if status is QualityStatus.GOOD:
                try:
                    numeric = float(value)
                    if not math.isfinite(numeric):
                        raise ValueError("non-finite")
                    value = numeric
                except (TypeError, ValueError):
                    status = QualityStatus.BAD
                    reason = ReasonCode.FAULT
                    value = None
            try:
                self.image.apply_input(name, value, status, reason)
            except Exception:  # noqa: BLE001 — best-effort
                continue

    def _apply_commands(self, cmds: tuple[str, ...]) -> None:
        """Enqueue Start/Stop/Reset only — no optimistic status (SWD-222).

        Publishing ``running`` before Skid ``PERM_OK`` accepts Start made the HMI
        bounce and Start feel broken. ``scan_once`` aligns ``scanning`` + status
        from Skid MODE after logic runs.
        """
        enqueue = getattr(self.logic, "enqueue_operator", None)
        for name in cmds:
            with self._lock:
                self.commands.append(name)
            if callable(enqueue):
                enqueue(name)
            # reset: latch-clear only — do not publish a sticky "reset" state;
            # ``scan_once`` republishes running/stopped from Skid MODE after logic.

    def start(self) -> None:
        if self._thread is not None:
            return
        self.scanning = False
        self.bridge.start()
        self._publish_scan_status("stopped")
        self._last_status_heartbeat = time.monotonic()
        self._alive = True
        thread = threading.Thread(target=self._run, name="mqtt-scan", daemon=True)
        self._thread = thread
        # stop() may clear self._thread between assign and .start() (SWD-137).
        if self._thread is not thread:
            self._alive = False
            return
        thread.start()
        if self._thread is not thread:
            self._alive = False
            if thread.ident is not None:
                thread.join(timeout=2.0)

    def stop(self) -> None:
        self.scanning = False
        self._alive = False
        thread = self._thread
        self._thread = None
        # Join only if start() completed — life.stop() can race attach (SWD-137).
        if thread is not None and thread.ident is not None:
            thread.join(timeout=2.0)
        self._publish_scan_status("stopped")
        self._last_status_heartbeat = time.monotonic()

    def scan_once(self) -> None:
        # Shared HA-config cmd file (Start when MQTT cmds never arrive) — SWD-139.
        file_cmd = drain_cmd()
        if file_cmd:
            self.bridge.enqueue_command(file_cmd)
        # File IN tags (SP_LEVEL_REQ + plant PV fallback, SWD-141/171) when MQTT
        # is silent. Apply before MQTT so live plant MQTT still wins same-scan.
        self._apply_file_inputs()
        mqtt_pending = self.bridge.pending_inputs
        self.bridge.apply_inputs(self.image, clear=True)
        # Operator modes/SPs: fresher file (HA seed) beats stale MQTT retain
        # without stomping a newer live MQTT operator write (SWD-222).
        self._reapply_fresher_operator_file(mqtt_pending)
        drained = self.bridge.drain_commands()
        if drained:
            self._apply_commands(drained)
        # Always run logic so Skid observes Start/Stop/Reset pulses.
        self.logic(self.image)
        # Align scan gate with Skid MODE (Reset→STOP after trip; Start→RUNNING).
        is_running = getattr(self.logic, "is_running", None)
        if callable(is_running):
            running = bool(is_running())
        elif isinstance(is_running, bool):
            running = is_running
        else:
            running = self.scanning
        if running != self.scanning or drained:
            self.scanning = running
            self._publish_scan_status("running" if running else "stopped")
            self._last_status_heartbeat = time.monotonic()
            self._last_file_bridge = time.monotonic()
        self.bridge.publish_outputs(self.image)
        # Heartbeat retained status so late HA listeners recover (SWD-136).
        now = time.monotonic()
        if now - self._last_status_heartbeat >= self.STATUS_HEARTBEAT_S:
            self._publish_scan_status("running" if self.scanning else "stopped")
            self._last_status_heartbeat = now
            self._last_file_bridge = now
        elif self.scanning or now - self._last_file_bridge >= self.FILE_BRIDGE_PERIOD_S:
            # While RUNNING, refresh file every scan so HMI/plant see rising
            # CVs (Start's first write is bumpless-zero) (SWD-225).
            self._write_ha_config_runtime()
            self._last_file_bridge = now

    def set_scan_period_s(self, period_s: float) -> None:
        """Align scan sleep, tick ``dt``, and MQTT status with project rate."""
        if period_s <= 0:
            raise ValueError("scan_period_s must be positive")
        self.period_s = period_s
        logic = self.logic
        if hasattr(logic, "set_scan_period_s"):
            logic.set_scan_period_s(period_s)
        else:
            logic.period_s = period_s
        # Republish retained status so observers see the new rate immediately.
        self._publish_scan_status("running" if self.scanning else "stopped")
        self._last_status_heartbeat = time.monotonic()

    def issue_command(self, name: str) -> None:
        """Enqueue an operator command for the scan thread (same as MQTT cmds)."""
        self.bridge.enqueue_command(str(name).lower())

    def _run(self) -> None:
        # Do not resurrect a scan that stop() already cleared (SWD-137 race).
        # ``_alive`` is set in start() — never flip it True here.
        if self._thread is not threading.current_thread() or not self._alive:
            return
        while self._alive:
            t0 = time.monotonic()
            try:
                self.scan_once()
            except Exception as exc:  # noqa: BLE001 — keep editor reachable
                self._publish_scan_status("fault", error=str(exc)[:200])
                self._last_status_heartbeat = time.monotonic()
            elapsed = time.monotonic() - t0
            time.sleep(max(0.0, self._scan_period_s() - elapsed))


def _mqtt_supervisor(
    options: dict[str, Any],
    instance_id: str,
    *,
    bus: MqttBus | None,
    period_s: float = 0.1,
    ha_runtime: bool | None = None,
) -> MqttLifecycle:
    """Start scan loop immediately when bus given; else retry connect in background.

    Always returns a ``MqttLifecycle`` so callers can ``stop()`` even when connect
    is deferred (live App must never block the HTTP thread on broker TCP).
    """
    life = MqttLifecycle()
    if ha_runtime is None:
        ha_runtime = os.environ.get("PLCASSISTANT_HA_RUNTIME", "") == "1"

    def _start_with(bus_obj: MqttBus) -> MqttScanLoop | None:
        if life.stopped():
            return None
        image = declare_default_image()
        bridge = MqttIoBridge(bus_obj, instance_id=instance_id)
        loop = MqttScanLoop(
            bridge,
            image,
            logic=SkidImageLogic(period_s=period_s),
            period_s=period_s,
        )
        # Attach before start so deferred cmds flush into the bridge queue first.
        life.attach(loop)
        if life.stopped() or life.loop is not loop:
            # stop() raced attach — tear down without leaving a live scan.
            loop.stop()
            return None
        loop.start()
        if life.stopped() or life.loop is not loop:
            loop.stop()
            return None
        return loop

    if bus is not None:
        _start_with(bus)
        return life

    # Want MQTT — retry until broker is up. HA App runtime always retries even
    # when options.json is missing/empty (defaults to core-mosquitto, SWD-137).
    host = str(options.get("mqtt_broker") or "")
    if not host and not options and not ha_runtime:
        return life

    def _retry() -> None:
        delay = 2.0
        broker = str(options.get("mqtt_broker") or "") or "core-mosquitto"
        port = int(options.get("mqtt_port") or 1883)
        print(
            f"PLCAssistant: Soft-PLC MQTT connecting to {broker}:{port} "
            f"(instance_id={instance_id})",
            flush=True,
        )
        while not life.stopped() and life.loop is None:
            new_bus = build_bus_from_options(
                options,
                instance_id=instance_id,
                ha_runtime=ha_runtime,
                period_s=period_s,
            )
            # Re-check after a potentially blocking connect/build.
            if life.stopped():
                return
            if new_bus is not None:
                loop = _start_with(new_bus)
                if loop is not None:
                    print(
                        "PLCAssistant: Soft-PLC MQTT scan attached "
                        f"(status=stopped, instance_id={instance_id})",
                        flush=True,
                    )
                return
            if life.wait(delay):
                return
            delay = min(delay * 1.5, 30.0)

    threading.Thread(target=_retry, name="mqtt-retry", daemon=True).start()
    return life


def run_ha_runtime(
    *,
    host: str = "0.0.0.0",
    port: int = 8099,
    program_path: str | None = None,
    options_path: str | None = None,
    bus: MqttBus | None = None,
    serve_forever: bool = True,
) -> tuple[Any, MqttLifecycle]:
    """Start editor HTTP server and optional MQTT scan loop.

    Returns ``(HTTPServer, MqttLifecycle)``.
    Live App never blocks this thread on broker TCP connect — background retry
    owns connect; ``lifecycle.stop()`` cancels retry and stops a late loop.
    """
    # Authoritative HA path — do not rely on env alone for Soft-PLC MQTT attach
    # when options.json is empty (SWD-137).
    os.environ["PLCASSISTANT_HA_RUNTIME"] = "1"
    options = load_options(options_path or os.environ.get("PLCASSISTANT_OPTIONS_PATH"))
    instance_id = str(
        options.get("instance_id")
        or os.environ.get("PLCASSISTANT_INSTANCE_ID")
        or DEFAULT_INSTANCE_ID
    )
    state = AppState(program_path=program_path)
    state.instance_id = instance_id
    period_s = (
        state.loader.project.scan_period_s
        if state.loader.project is not None
        else 0.1
    )
    # Bind the editor first so Ingress / host port respond even if MQTT is slow.
    server = run_app(host=host, port=port, state=state)

    lifecycle = _mqtt_supervisor(
        options,
        instance_id,
        bus=bus,
        period_s=period_s,
        ha_runtime=True,
    )
    state.attach_runtime(lifecycle)

    if serve_forever:
        try:
            server.serve_forever()
        finally:
            lifecycle.stop()
    return server, lifecycle


__all__ = [
    "MqttLifecycle",
    "MqttScanLoop",
    "build_bus_from_options",
    "declare_default_image",
    "default_scan_logic",
    "load_options",
    "run_ha_runtime",
]
