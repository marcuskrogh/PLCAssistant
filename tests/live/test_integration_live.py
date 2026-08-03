"""Live integration tests: Soft-PLC App ↔ thin HA integration (SWD-234)."""

from __future__ import annotations

import pytest

from tests.live.clients import wait_until

pytestmark = [pytest.mark.live, pytest.mark.live_integration]


def test_softplc_mqtt_attached(soft) -> None:
    snap = soft.runtime()
    assert snap.get("mqtt") is True
    assert snap.get("status") in {"running", "stopped"}
    assert isinstance(snap.get("tags"), dict)
    assert "MODE" in snap["tags"] or "LT_TANK" in snap["tags"]


def test_ha_plcassistant_entities_present(ha) -> None:
    entities = ha.plcassistant_entities()
    assert "sensor.plcassistant_status" in entities
    assert "button.plcassistant_start" in entities
    assert "button.plcassistant_stop" in entities
    assert len(entities) >= 5


def test_ha_start_stop_drives_softplc_scan(ha, soft) -> None:
    # Ensure stopped first.
    ha.call_service("plcassistant", "stop")
    wait_until(
        lambda: soft.runtime().get("status") == "stopped"
        or soft.runtime().get("scanning") is False,
        timeout=45.0,
        desc="Soft-PLC stopped",
    )

    ha.call_service("plcassistant", "start")
    wait_until(
        lambda: soft.runtime().get("status") == "running"
        or soft.runtime().get("scanning") is True,
        timeout=60.0,
        desc="Soft-PLC running after HA start",
    )
    running = soft.runtime()
    assert running.get("mqtt") is True

    ha.call_service("plcassistant", "stop")
    wait_until(
        lambda: soft.runtime().get("status") == "stopped"
        or soft.runtime().get("scanning") is False,
        timeout=45.0,
        desc="Soft-PLC stopped after HA stop",
    )


def test_ha_status_sensor_mirrors_softplc(ha, soft) -> None:
    ha.call_service("plcassistant", "start")
    wait_until(
        lambda: soft.runtime().get("status") == "running",
        timeout=60.0,
        desc="Soft-PLC running",
    )

    def status_matches() -> bool:
        state = ha.get_state("sensor.plcassistant_status")
        if not state:
            return False
        ha_status = str(state.get("state") or "").lower()
        soft_status = str(soft.runtime().get("status") or "").lower()
        return ha_status == soft_status or (
            soft_status == "running" and ha_status in {"running", "online"}
        )

    wait_until(status_matches, timeout=60.0, desc="HA status mirrors Soft-PLC")

    ha.call_service("plcassistant", "stop")
    wait_until(
        lambda: soft.runtime().get("status") == "stopped",
        timeout=45.0,
        desc="Soft-PLC stopped (cleanup)",
    )
