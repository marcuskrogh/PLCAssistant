"""HTTP API smoke tests for the App (SWD-120).

Tests use urllib.request directly against a real HTTPServer on a random port.
No Selenium / browser required.

Covers:
- GET / returns HTML canvas
- GET /api/program returns JSON program dict
- GET /api/library returns builtin + user templates
- PUT /api/program round-trip
- POST /api/place places block, returns updated program
- POST /api/reset_instance resets params to library defaults
- POST /api/apply restart: accepted
- POST /api/apply hot without superuser: 403 PermissionError
- POST /api/apply hot with superuser=True: accepted
- POST /api/library/user: create/update user template
- DELETE /api/library/user/<tid>: delete user template
- 404 for unknown route
"""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer
from typing import Any

import pytest

from plcassistant.app.server import AppState, make_handler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app_server(monkeypatch):
    """Start a test App server on a random port; yield (server, url); stop after test."""
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    state = AppState()
    handler = make_handler(state)
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    base_url = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, base_url, state
    server.shutdown()


def _get(url: str) -> tuple[int, bytes, str]:
    try:
        with urllib.request.urlopen(url) as r:
            return r.status, r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), ""


def _json_get(url: str) -> tuple[int, Any]:
    status, body, _ = _get(url)
    return status, json.loads(body)


def _json_request(url: str, method: str, data: Any = None) -> tuple[int, Any]:
    body_bytes = json.dumps(data).encode() if data is not None else b""
    req = urllib.request.Request(
        url,
        data=body_bytes,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


def test_get_root_returns_html(app_server):
    _, base_url, _ = app_server
    status, body, ct = _get(base_url + "/")
    assert status == 200
    assert b"PLC Assistant" in body
    assert "text/html" in ct


# ---------------------------------------------------------------------------
# GET /api/program
# ---------------------------------------------------------------------------


def test_get_program_returns_json(app_server):
    _, base_url, _ = app_server
    status, data = _json_get(base_url + "/api/program")
    assert status == 200
    assert "instances" in data
    assert "wires" in data
    assert "execution_order" in data


# ---------------------------------------------------------------------------
# PUT /api/program round-trip
# ---------------------------------------------------------------------------


def test_put_program_round_trip(app_server):
    _, base_url, _ = app_server
    prog = {
        "version": "1.0",
        "instances": {
            "level_pi": {
                "template_id": "level_pi",
                "library": "builtin",
                "params": {"kp": 99.0, "ki": 5.0, "cv_min": 0.0, "cv_max": 6.0},
            }
        },
        "wires": [],
        "execution_order": ["level_pi"],
    }
    status, resp = _json_request(base_url + "/api/program", "PUT", prog)
    assert status == 200
    assert resp["instances"]["level_pi"]["params"]["kp"] == pytest.approx(99.0)

    # GET should return the updated program
    status2, data2 = _json_get(base_url + "/api/program")
    assert status2 == 200
    assert data2["instances"]["level_pi"]["params"]["kp"] == pytest.approx(99.0)


def test_put_program_invalid_json_returns_400(app_server):
    _, base_url, _ = app_server
    # Send a list instead of a dict (invalid program structure)
    status, resp = _json_request(base_url + "/api/program", "PUT", [1, 2, 3])
    assert status == 400


# ---------------------------------------------------------------------------
# GET /api/library
# ---------------------------------------------------------------------------


def test_get_library_returns_builtins(app_server):
    _, base_url, _ = app_server
    status, data = _json_get(base_url + "/api/library")
    assert status == 200
    assert isinstance(data, list)
    ids = [t["template_id"] for t in data]
    assert "level_pi" in ids
    assert "flow_pi" in ids


# ---------------------------------------------------------------------------
# POST /api/place
# ---------------------------------------------------------------------------


def test_place_builtin_block(app_server):
    _, base_url, _ = app_server
    payload = {
        "template_id": "level_pi",
        "library": "builtin",
        "instance_id": "lpi_test",
        "x": 100.0,
        "y": 200.0,
    }
    status, resp = _json_request(base_url + "/api/place", "POST", payload)
    assert status == 200
    assert "lpi_test" in resp["instances"]
    assert resp["instances"]["lpi_test"]["template_id"] == "level_pi"
    assert resp["instances"]["lpi_test"]["params"]["kp"] == pytest.approx(40.0)
    assert "lpi_test" in resp["execution_order"]


def test_place_unknown_template_returns_404(app_server):
    _, base_url, _ = app_server
    payload = {"template_id": "ghost_block", "library": "builtin", "instance_id": "g1"}
    status, resp = _json_request(base_url + "/api/place", "POST", payload)
    assert status == 404


# ---------------------------------------------------------------------------
# POST /api/reset_instance
# ---------------------------------------------------------------------------


def test_reset_instance_restores_defaults(app_server):
    _, base_url, state = app_server
    # First place a block
    _json_request(base_url + "/api/place", "POST", {
        "template_id": "level_pi", "library": "builtin", "instance_id": "lpi_r"
    })
    # Modify the program's instance params
    prog = state.loader.program
    prog.instances["lpi_r"].params["kp"] = 999.0
    # Reset
    status, resp = _json_request(
        base_url + "/api/reset_instance", "POST", {"instance_id": "lpi_r"}
    )
    assert status == 200
    assert resp["instances"]["lpi_r"]["params"]["kp"] == pytest.approx(40.0)


def test_reset_instance_unknown_returns_404(app_server):
    _, base_url, _ = app_server
    status, resp = _json_request(
        base_url + "/api/reset_instance", "POST", {"instance_id": "ghost"}
    )
    assert status == 404


# ---------------------------------------------------------------------------
# POST /api/apply
# ---------------------------------------------------------------------------


def test_apply_restart(app_server):
    _, base_url, _ = app_server
    status, resp = _json_request(base_url + "/api/apply", "POST", {"mode": "restart"})
    assert status == 200
    assert resp["applied"] == "restart"


def test_apply_hot_without_superuser_returns_403(app_server):
    _, base_url, _ = app_server
    status, resp = _json_request(
        base_url + "/api/apply", "POST", {"mode": "hot", "superuser": False}
    )
    assert status == 403
    assert "superuser" in resp.get("error", "").lower()


def test_apply_hot_client_superuser_flag_ignored(app_server):
    """Client-supplied superuser=True must be ignored; still returns 403 when env unset."""
    _, base_url, _ = app_server
    status, resp = _json_request(
        base_url + "/api/apply", "POST", {"mode": "hot", "superuser": True}
    )
    assert status == 403, (
        "Server must not honour client-supplied superuser field; "
        "authority comes from server-side env var only"
    )


def test_apply_hot_with_env_var(monkeypatch):
    """PLCASSISTANT_SUPERUSER_HOT_APPLY=1 env var at AppState construction → hot allowed."""
    monkeypatch.setenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", "1")
    state = AppState()
    handler = make_handler(state)
    import threading
    from http.server import HTTPServer
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    base_url = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, resp = _json_request(base_url + "/api/apply", "POST", {"mode": "hot"})
        assert status == 200
        assert resp["applied"] == "hot"
    finally:
        server.shutdown()


def test_apply_unknown_mode_returns_400(app_server):
    _, base_url, _ = app_server
    status, resp = _json_request(base_url + "/api/apply", "POST", {"mode": "invalid_mode"})
    assert status == 400


# ---------------------------------------------------------------------------
# POST /api/library/user (create/update user template)
# ---------------------------------------------------------------------------


def test_create_user_template(app_server):
    _, base_url, _ = app_server
    payload = {
        "template_id": "my_gain",
        "description": "Multiply x by gain",
        "library": "user",
        "pins": [
            {"name": "x", "direction": "IN", "data_type": "float", "default": 0.0},
            {"name": "out", "direction": "OUT", "data_type": "float"},
        ],
        "params": {"gain": 2.0},
        "body": "out = x * gain",
    }
    status, resp = _json_request(base_url + "/api/library/user", "POST", payload)
    assert status == 200
    assert resp["template_id"] == "my_gain"

    # Library should include the new template
    _, lib_data = _json_get(base_url + "/api/library")
    ids = [t["template_id"] for t in lib_data]
    assert "my_gain" in ids

    # Program user_templates should include it
    _, prog_data = _json_get(base_url + "/api/program")
    assert "my_gain" in (prog_data.get("user_templates") or {})


def test_create_user_template_missing_tid_returns_400(app_server):
    _, base_url, _ = app_server
    payload = {"body": "pass"}
    status, resp = _json_request(base_url + "/api/library/user", "POST", payload)
    assert status == 400


# ---------------------------------------------------------------------------
# DELETE /api/library/user/<tid>
# ---------------------------------------------------------------------------


def test_delete_user_template(app_server):
    _, base_url, _ = app_server
    # Create first
    _json_request(base_url + "/api/library/user", "POST", {
        "template_id": "to_delete", "body": "pass", "pins": [], "params": {}
    })
    # Delete
    status, resp = _json_request(
        base_url + "/api/library/user/to_delete", "DELETE"
    )
    assert status == 200
    assert resp["deleted"] == "to_delete"

    # Library should no longer list it
    _, lib_data = _json_get(base_url + "/api/library")
    ids = [t["template_id"] for t in lib_data]
    assert "to_delete" not in ids


def test_delete_nonexistent_user_template_returns_404(app_server):
    _, base_url, _ = app_server
    status, resp = _json_request(
        base_url + "/api/library/user/ghost_block", "DELETE"
    )
    assert status == 404


# ---------------------------------------------------------------------------
# 404 for unknown route
# ---------------------------------------------------------------------------


def test_unknown_route_returns_404(app_server):
    _, base_url, _ = app_server
    status, _ = _json_get(base_url + "/api/this_does_not_exist")
    assert status == 404


# ---------------------------------------------------------------------------
# Full round-trip: PUT program → place → apply restart → GET
# ---------------------------------------------------------------------------


def test_full_round_trip(app_server):
    """PUT a program, place a block, apply restart, verify GET returns it."""
    _, base_url, _ = app_server
    # PUT empty program
    status, _ = _json_request(base_url + "/api/program", "PUT", {
        "version": "1.0", "instances": {}, "wires": [], "execution_order": []
    })
    assert status == 200

    # Place a block
    status, prog = _json_request(base_url + "/api/place", "POST", {
        "template_id": "flow_pi",
        "library": "builtin",
        "instance_id": "fpi_1",
    })
    assert status == 200
    assert "fpi_1" in prog["instances"]

    # Apply restart
    status, apply_resp = _json_request(base_url + "/api/apply", "POST", {"mode": "restart"})
    assert status == 200
    assert apply_resp["applied"] == "restart"

    # GET should return updated program
    status, final = _json_get(base_url + "/api/program")
    assert status == 200
    assert "fpi_1" in final["instances"]
