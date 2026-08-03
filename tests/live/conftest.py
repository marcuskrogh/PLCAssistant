"""Pytest fixtures for live Mosquitto + HA Core + Soft-PLC stack (SWD-232)."""

from __future__ import annotations

import os

import pytest

from tests.live.clients import (
    DEFAULT_HA_URL,
    DEFAULT_SOFT_PLC_URL,
    HaClient,
    SoftPlcClient,
    load_ha_auth,
    tcp_open,
    wait_until,
)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "live: requires cloud HA stack (Mosquitto + HA Core + Soft-PLC)"
    )
    config.addinivalue_line(
        "markers", "live_integration: live App ↔ thin-integration tests"
    )
    config.addinivalue_line(
        "markers", "live_system: live end-to-end system tests"
    )


def _stack_ready() -> tuple[bool, str]:
    if not tcp_open("127.0.0.1", 1883):
        return False, "Mosquitto not listening on :1883"
    if not tcp_open("127.0.0.1", 8123):
        return False, "Home Assistant not listening on :8123"
    if not tcp_open("127.0.0.1", 8099):
        return False, "Soft-PLC not listening on :8099"
    auth = load_ha_auth()
    if auth is None:
        return False, f"HA token missing (run bootstrap); expected {os.environ.get('HA_TOKEN_PATH', '.cursor/ha/data/ha_token.json')}"
    return True, "ok"


@pytest.fixture(scope="session")
def live_stack():
    """Skip the session unless the cloud HA stack is already up and bootstrapped."""
    ok, reason = _stack_ready()
    if not ok:
        pytest.skip(f"live stack not ready: {reason}")
    # Soft-PLC may still be connecting MQTT — wait for runtime mqtt=true.
    soft = SoftPlcClient(DEFAULT_SOFT_PLC_URL)
    try:
        wait_until(
            lambda: bool(soft.runtime().get("mqtt")),
            timeout=90.0,
            desc="Soft-PLC MQTT attach",
        )
    except TimeoutError as exc:
        pytest.skip(f"live stack Soft-PLC MQTT not attached: {exc}")
    auth = load_ha_auth()
    assert auth is not None
    return {
        "ha": HaClient(auth.base_url or DEFAULT_HA_URL, auth.access_token),
        "soft": soft,
        "auth": auth,
    }


@pytest.fixture
def ha(live_stack) -> HaClient:
    return live_stack["ha"]


@pytest.fixture
def soft(live_stack) -> SoftPlcClient:
    return live_stack["soft"]
