"""Live system tests: full stack App ↔ integration path (SWD-235)."""

from __future__ import annotations

import pytest

from tests.live.clients import tcp_open, wait_until

pytestmark = [pytest.mark.live, pytest.mark.live_system]


def test_stack_ports_healthy() -> None:
    assert tcp_open("127.0.0.1", 1883), "MQTT :1883"
    assert tcp_open("127.0.0.1", 8123), "HA :8123"
    assert tcp_open("127.0.0.1", 8099), "Soft-PLC :8099"


def test_softplc_editor_apis(soft) -> None:
    runtime = soft.runtime()
    assert "status" in runtime
    assert "tags" in runtime
    project = soft.project()
    assert "programs" in project or "tasks" in project or "version" in project


def test_start_path_updates_ha_status_and_plant(ha, soft) -> None:
    ha.call_service("plcassistant", "stop")
    wait_until(
        lambda: soft.runtime().get("status") == "stopped",
        timeout=45.0,
        desc="Soft-PLC stopped before Start",
    )

    ha.call_service("plcassistant", "start")
    wait_until(
        lambda: soft.runtime().get("status") == "running",
        timeout=60.0,
        desc="Soft-PLC running",
    )

    wait_until(
        lambda: (ha.get_state("sensor.plcassistant_status") or {}).get("state")
        in {"running", "online"},
        timeout=60.0,
        desc="HA status shows running",
    )

    plant_candidates = (
        "sensor.plcassistant_lt_tank_in",
        "sensor.plcassistant_lt_res_in",
        "sensor.plcassistant_ft_inlet_in",
        "sensor.plcassistant_cmd_speed",
    )
    available = []
    for eid in plant_candidates:
        st = ha.get_state(eid)
        if st is not None and str(st.get("state")) not in {"unavailable", "unknown", ""}:
            available.append(eid)
    assert available, f"expected plant sensors available; checked {plant_candidates}"

    # Soft-PLC tags should include plant / mode after start.
    tags = soft.runtime().get("tags") or {}
    assert any(k in tags for k in ("LT_TANK", "MODE", "CMD_SPEED", "FT_INLET"))

    ha.call_service("plcassistant", "stop")


def test_level_man_sp_write_visible_on_softplc(ha, soft) -> None:
    entity = "number.plcassistant_sp_level_man"
    st = ha.get_state(entity)
    if st is None:
        pytest.skip(f"{entity} not present in this bootstrap")

    target = 0.31
    ha.set_number(entity, target)

    def tag_near() -> bool:
        val = soft.tag_value("SP_LEVEL_MAN")
        if val is None:
            # Some builds mirror as SP_LEVEL_MAN via MODE flip path; try SP_LEVEL too.
            val = soft.tag_value("SP_LEVEL")
        if val is None:
            return False
        try:
            return abs(float(val) - target) < 0.05
        except (TypeError, ValueError):
            return False

    wait_until(tag_near, timeout=45.0, desc="Soft-PLC sees level MAN SP write")


def test_button_start_path(ha, soft) -> None:
    ha.call_service("plcassistant", "stop")
    wait_until(
        lambda: soft.runtime().get("status") == "stopped",
        timeout=45.0,
        desc="stopped before button start",
    )
    ha.press_button("button.plcassistant_start")
    wait_until(
        lambda: soft.runtime().get("status") == "running",
        timeout=60.0,
        desc="Soft-PLC running after button press",
    )
    ha.press_button("button.plcassistant_stop")
    wait_until(
        lambda: soft.runtime().get("status") == "stopped",
        timeout=45.0,
        desc="Soft-PLC stopped after button stop",
    )
