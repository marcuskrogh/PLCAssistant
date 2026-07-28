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

    def slow_build(options):
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

    def delayed_bus(options):
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
