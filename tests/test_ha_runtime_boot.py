"""HA App runtime boot must not block the editor on MQTT connect (SWD-128)."""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path

from plcassistant.app.runtime import run_ha_runtime
from plcassistant.io.mqtt_bridge import InMemoryMqttBus


def test_run_ha_runtime_serves_http_while_mqtt_connect_is_slow(tmp_path: Path, monkeypatch):
    """Broker TCP connect stays off the HTTP thread so Ingress can come up."""
    options_path = tmp_path / "options.json"
    options_path.write_text(
        json.dumps(
            {
                "instance_id": "default",
                "mqtt_broker": "core-mosquitto",
                "mqtt_port": 1883,
            }
        ),
        encoding="utf-8",
    )

    started = threading.Event()
    release = threading.Event()

    def slow_build(options, **_kwargs):
        started.set()
        # Hold the retry worker; HTTP must still answer.
        release.wait(timeout=5.0)
        return None

    monkeypatch.setattr(
        "plcassistant.app.runtime.build_bus_from_options",
        slow_build,
    )

    server, life = run_ha_runtime(
        host="127.0.0.1",
        port=0,
        program_path=str(tmp_path / "program.json"),
        options_path=str(options_path),
        serve_forever=False,
    )
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert started.wait(timeout=2.0), "MQTT connect worker did not start"
        t0 = time.monotonic()
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2.0) as resp:
            body = resp.read()
        assert time.monotonic() - t0 < 1.5
        assert resp.status == 200
        assert b"PLC Assistant" in body
        assert life.loop is None  # connect still deferred
    finally:
        release.set()
        life.stop()
        server.shutdown()


def test_run_ha_runtime_stops_deferred_mqtt_loop(tmp_path: Path, monkeypatch):
    """Lifecycle.stop() cancels retry and stops a loop created after boot."""
    options_path = tmp_path / "options.json"
    options_path.write_text(
        json.dumps({"instance_id": "default", "mqtt_broker": "core-mosquitto"}),
        encoding="utf-8",
    )
    release = threading.Event()

    def delayed_bus(options, **_kwargs):
        release.wait(timeout=2.0)
        return InMemoryMqttBus()

    monkeypatch.setattr(
        "plcassistant.app.runtime.build_bus_from_options",
        delayed_bus,
    )

    _server, life = run_ha_runtime(
        host="127.0.0.1",
        port=0,
        program_path=str(tmp_path / "program.json"),
        options_path=str(options_path),
        serve_forever=False,
    )
    try:
        assert life.loop is None
        release.set()
        deadline = time.monotonic() + 3.0
        while life.loop is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert life.loop is not None
        loop = life.loop
        life.stop()
        assert life.loop is None
        assert loop._thread is None  # noqa: SLF001 — stopped joins scan thread
    finally:
        release.set()
        life.stop()


def test_stop_during_blocking_connect_does_not_start_loop(tmp_path: Path, monkeypatch):
    """If stop() wins during a slow bus build, never leave a live scan loop."""
    options_path = tmp_path / "options.json"
    options_path.write_text(
        json.dumps({"instance_id": "default", "mqtt_broker": "core-mosquitto"}),
        encoding="utf-8",
    )
    entered = threading.Event()
    release = threading.Event()

    def blocking_bus(options, **_kwargs):
        entered.set()
        release.wait(timeout=3.0)
        return InMemoryMqttBus()

    monkeypatch.setattr(
        "plcassistant.app.runtime.build_bus_from_options",
        blocking_bus,
    )

    _server, life = run_ha_runtime(
        host="127.0.0.1",
        port=0,
        program_path=str(tmp_path / "program.json"),
        options_path=str(options_path),
        serve_forever=False,
    )
    try:
        assert entered.wait(timeout=2.0)
        life.stop()
        release.set()
        # Give the retry worker a moment to attempt _start_with after build.
        time.sleep(0.3)
        assert life.stopped()
        assert life.loop is None
    finally:
        release.set()
        life.stop()


def test_deferred_stop_during_connect_applies_on_attach(tmp_path: Path, monkeypatch):
    """Start+Stop while loop is None must survive and leave the scan stopped."""
    options_path = tmp_path / "options.json"
    options_path.write_text(
        json.dumps({"instance_id": "default", "mqtt_broker": "core-mosquitto"}),
        encoding="utf-8",
    )
    release = threading.Event()

    def delayed_bus(options, **_kwargs):
        release.wait(timeout=2.0)
        return InMemoryMqttBus()

    monkeypatch.setattr(
        "plcassistant.app.runtime.build_bus_from_options",
        delayed_bus,
    )

    server, life = run_ha_runtime(
        host="127.0.0.1",
        port=0,
        program_path=str(tmp_path / "program.json"),
        options_path=str(options_path),
        serve_forever=False,
    )
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert life.loop is None
        # Connect window: operator start then stop before MQTT attaches.
        for name in ("start", "stop"):
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/cmd",
                data=json.dumps({"name": name}).encode(),
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                body = json.loads(resp.read())
            assert body["status"] == "offline"
            assert body["scanning"] is False
            assert body["mqtt"] is False

        release.set()
        deadline = time.monotonic() + 3.0
        while life.loop is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert life.loop is not None

        # Wait until deferred stop is drained by the scan thread.
        deadline = time.monotonic() + 2.0
        while life.loop.scanning and time.monotonic() < deadline:
            time.sleep(0.05)
        assert life.loop.scanning is False

        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/runtime", timeout=2.0
        ) as resp:
            snap = json.loads(resp.read())
        assert snap["mqtt"] is True
        assert snap["status"] == "stopped"
        assert snap["scanning"] is False
    finally:
        release.set()
        life.stop()
        server.shutdown()


def test_app_cmd_enqueues_for_scan_thread():
    """App issue_command must not mutate scanning on the caller thread."""
    from plcassistant.app.runtime import MqttScanLoop, declare_default_image
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge

    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.1)
    bridge.start()
    assert loop.scanning is False

    loop.issue_command("start")
    # Still False until the scan thread drains the bridge queue.
    assert loop.scanning is False
    assert bridge.pending_commands == ("start",)

    loop.scan_once()
    assert loop.scanning is True
    assert bridge.pending_commands == ()

    loop.issue_command("stop")
    assert loop.scanning is True
    loop.scan_once()
    assert loop.scanning is False


def test_memory_bus_runtime_cmd_via_http(tmp_path: Path):
    """Live memory bus: /api/cmd start/stop observed after scan drain."""
    bus = InMemoryMqttBus()
    server, life = run_ha_runtime(
        host="127.0.0.1",
        port=0,
        program_path=str(tmp_path / "program.json"),
        bus=bus,
        serve_forever=False,
    )
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert life.loop is not None
        assert life.loop.scanning is False

        def post_cmd(name: str) -> dict:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/cmd",
                data=json.dumps({"name": name}).encode(),
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return json.loads(resp.read())

        post_cmd("start")
        deadline = time.monotonic() + 2.0
        while (not life.loop.scanning) and time.monotonic() < deadline:
            time.sleep(0.05)
        assert life.loop.scanning is True

        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/runtime", timeout=2.0
        ) as resp:
            snap = json.loads(resp.read())
        assert snap["mqtt"] is True
        assert snap["status"] == "running"

        post_cmd("stop")
        deadline = time.monotonic() + 2.0
        while life.loop.scanning and time.monotonic() < deadline:
            time.sleep(0.05)
        assert life.loop.scanning is False
    finally:
        life.stop()
        server.shutdown()


def test_ha_runtime_empty_options_defaults_mosquitto_and_retries(monkeypatch):
    """SWD-137: missing/empty options must not skip Mosquitto forever."""
    from plcassistant.app.runtime import _mqtt_supervisor, build_bus_from_options

    monkeypatch.setenv("PLCASSISTANT_HA_RUNTIME", "1")
    monkeypatch.delenv("PLCASSISTANT_MQTT_BUS", raising=False)

    seen: dict[str, object] = {}

    class FakeBus:
        def __init__(self, host, port, **kwargs):
            seen["host"] = host
            seen["port"] = port

        def publish(self, *args, **kwargs):
            return None

        def subscribe(self, *args, **kwargs):
            return None

    monkeypatch.setattr("plcassistant.io.mqtt_paho.PahoMqttBus", FakeBus)
    bus = build_bus_from_options({})
    assert bus is not None
    assert seen["host"] == "core-mosquitto"
    assert seen["port"] == 1883

    attached = threading.Event()

    def capture(options, **_kwargs):
        attached.set()
        return InMemoryMqttBus()

    monkeypatch.setattr(
        "plcassistant.app.runtime.build_bus_from_options",
        capture,
    )
    life = _mqtt_supervisor({}, "default", bus=None)
    try:
        assert attached.wait(timeout=2.0), "MQTT retry never started for empty options"
        deadline = time.monotonic() + 2.0
        while life.loop is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert life.loop is not None
    finally:
        life.stop()


def test_mqtt_scan_loop_start_stop_race_safe():
    """SWD-137: stop() between Thread assign and .start() must not AttributeError."""
    from plcassistant.app.runtime import MqttScanLoop, declare_default_image
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge

    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    loop = MqttScanLoop(bridge, image, period_s=0.05)

    errors: list[BaseException] = []

    def starter() -> None:
        try:
            for _ in range(20):
                if loop._thread is None:
                    loop.start()
                time.sleep(0.001)
        except BaseException as exc:  # noqa: BLE001 — collect for assert
            errors.append(exc)

    def stopper() -> None:
        try:
            for _ in range(40):
                loop.stop()
                time.sleep(0.001)
        except BaseException as exc:  # noqa: BLE001 — collect for assert
            errors.append(exc)

    t1 = threading.Thread(target=starter)
    t2 = threading.Thread(target=stopper)
    t1.start()
    t2.start()
    t1.join(timeout=5.0)
    t2.join(timeout=5.0)
    loop.stop()
    assert not errors, errors
    assert loop._thread is None
    assert loop._alive is False


def test_mqtt_docs_note_hmi_state_retain():
    """SWD-137: packaging + README must document retained MODE/PERM/TRIP OUT."""
    root = Path(__file__).resolve().parents[1]
    topics = (root / "docs" / "packaging" / "02-mqtt-topics.md").read_text(encoding="utf-8")
    assert "MODE" in topics and "PERM_OK" in topics and "TRIP_ACTIVE" in topics
    assert "retain **true**" in topics.lower()
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "MODE" in readme and "PERM_OK" in readme and "TRIP_ACTIVE" in readme
