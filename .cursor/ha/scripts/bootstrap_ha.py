#!/usr/bin/env python3
"""Bootstrap local Home Assistant for PLCAssistant integration testing.

Completes onboarding, creates a long-lived token, configures MQTT → 127.0.0.1,
and adds the PLCAssistant integration (mock mode).
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

BASE = os.environ.get("HA_URL", "http://127.0.0.1:8123").rstrip("/")
USER = {
    "client_id": f"{BASE}/",
    "name": "PLC Assistant Dev",
    "username": "dev",
    "password": "devpass123",
    "language": "en",
}
TOKEN_PATH = os.environ.get(
    "HA_TOKEN_PATH", "/workspace/.cursor/ha/data/ha_token.json"
)


def http(
    method: str,
    path: str,
    body: Any | None = None,
    token: str | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode() or "null"
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            parsed: Any = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw
        return exc.code, parsed


def wait_ready(timeout: float = 180) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            code, _ = http("GET", "/api/onboarding")
            if code == 200:
                return
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2)
    raise SystemExit("Home Assistant onboarding API never became ready")


def onboarding_steps() -> list[dict[str, Any]]:
    code, data = http("GET", "/api/onboarding")
    if code != 200:
        raise SystemExit(f"onboarding status failed: {code} {data}")
    assert isinstance(data, list)
    return data


def step_done(name: str) -> bool:
    for step in onboarding_steps():
        if step.get("step") == name:
            return bool(step.get("done"))
    return True


def complete_onboarding() -> str:
    """Finish onboarding; return a usable access token."""
    token: str | None = None
    if not step_done("user"):
        code, data = http("POST", "/api/onboarding/users", USER)
        if code not in (200, 201):
            raise SystemExit(f"create user failed: {code} {data}")
        auth_code = data.get("auth_code") if isinstance(data, dict) else None
        if not auth_code:
            raise SystemExit(f"user step missing auth_code: {data}")
        token = token_from_auth_code(auth_code)
        print("created owner user", USER["username"])
    else:
        token = login_token()

    if not step_done("core_config"):
        code, data = http(
            "POST",
            "/api/onboarding/core_config",
            {
                "location_name": "PLCAssistant Dev",
                "language": "en",
                "country": "US",
                "time_zone": "UTC",
                "unit_system": "metric",
                "currency": "USD",
            },
            token=token,
        )
        if code not in (200, 201):
            raise SystemExit(f"core_config failed: {code} {data}")
        print("core_config done")
    if not step_done("analytics"):
        code, data = http("POST", "/api/onboarding/analytics", {}, token=token)
        if code not in (200, 201):
            raise SystemExit(f"analytics failed: {code} {data}")
        print("analytics done")
    if not step_done("integration"):
        code, data = http(
            "POST",
            "/api/onboarding/integration",
            {"client_id": USER["client_id"]},
            token=token,
        )
        print(f"integration step response: {code} {data}")
    return token


def token_from_auth_code(auth_code: str) -> str:
    code, data = http(
        "POST",
        "/auth/token",
        None,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    # Use form body via raw request
    form = (
        f"grant_type=authorization_code&code={auth_code}"
        f"&client_id={urllib.request.quote(USER['client_id'], safe='')}"
    ).encode()
    req = urllib.request.Request(
        f"{BASE}/auth/token",
        data=form,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data["access_token"]


def login_token() -> str:
    """Password login → access token via auth flow."""
    code, data = http(
        "POST",
        "/auth/login_flow",
        {
            "client_id": USER["client_id"],
            "handler": ["homeassistant", None],
            "redirect_uri": f"{BASE}/?auth_callback=1",
        },
    )
    if code != 200:
        raise SystemExit(f"login_flow start failed: {code} {data}")
    flow_id = data["flow_id"]
    code, data = http(
        "POST",
        f"/auth/login_flow/{flow_id}",
        {
            "client_id": USER["client_id"],
            "username": USER["username"],
            "password": USER["password"],
        },
    )
    if code != 200 or "result" not in data:
        raise SystemExit(f"login_flow finish failed: {code} {data}")
    return token_from_auth_code(data["result"])


def wait_ha_api(token: str, timeout: float = 180) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            code, data = http("GET", "/api/", token=token)
            if code == 200:
                print("HA API ready:", data)
                return
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2)
    raise SystemExit("HA API never became authenticated-ready")


def config_flow(
    token: str, handler: str, user_input: dict[str, Any] | None = None
) -> dict[str, Any]:
    code, data = http(
        "POST",
        "/api/config/config_entries/flow",
        {"handler": handler, "show_advanced_options": True},
        token=token,
    )
    if code not in (200, 201):
        raise SystemExit(f"start flow {handler} failed: {code} {data}")
    # Advance until create_entry / abort
    for _ in range(10):
        if data.get("type") in ("create_entry", "abort"):
            return data
        flow_id = data.get("flow_id")
        step = data.get("step_id")
        payload = user_input or {}
        if handler == "mqtt" and step in ("broker", "user"):
            payload = {
                "broker": "127.0.0.1",
                "port": 1883,
                "username": "",
                "password": "",
            }
        if handler == "plcassistant" and step in ("user",):
            payload = {
                "instance_id": "default",
                "mqtt_broker": "127.0.0.1",
                "mqtt_port": 1883,
                "mock_mode": True,
            }
        code, data = http(
            "POST",
            f"/api/config/config_entries/flow/{flow_id}",
            payload,
            token=token,
        )
        if code not in (200, 201):
            raise SystemExit(f"advance flow {handler}/{step} failed: {code} {data}")
    return data


def already_configured(token: str, domain: str) -> bool:
    code, data = http("GET", "/api/config/config_entries/entry", token=token)
    if code != 200 or not isinstance(data, list):
        return False
    return any(e.get("domain") == domain for e in data)


def main() -> None:
    wait_ready()
    token = complete_onboarding()
    wait_ha_api(token)

    if not already_configured(token, "mqtt"):
        result = config_flow(token, "mqtt")
        print("mqtt flow:", result.get("type"), result.get("reason") or result.get("title"))
    else:
        print("mqtt already configured")

    # Give MQTT a moment to connect
    time.sleep(3)

    if not already_configured(token, "plcassistant"):
        result = config_flow(token, "plcassistant")
        print(
            "plcassistant flow:",
            result.get("type"),
            result.get("reason") or result.get("title"),
        )
    else:
        print("plcassistant already configured")

    # Probe entities
    time.sleep(5)
    code, states = http("GET", "/api/states", token=token)
    if code != 200:
        raise SystemExit(f"states failed: {code} {states}")
    plc = sorted(
        s["entity_id"]
        for s in states
        if str(s.get("entity_id", "")).startswith(
            ("sensor.plcassistant", "number.plcassistant", "button.plcassistant")
        )
    )
    print(f"plcassistant entities ({len(plc)}):")
    for eid in plc:
        print(" ", eid)

    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "access_token": token,
                "base_url": BASE,
                "username": USER["username"],
                "password": USER["password"],
            },
            fh,
            indent=2,
        )
    print("wrote", TOKEN_PATH)
    if len(plc) < 3:
        raise SystemExit("expected PLCAssistant entities after setup")


if __name__ == "__main__":
    main()
