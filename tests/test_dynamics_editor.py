"""SWD-166: dynamics model store + editor packaging contracts (HA-free)."""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CC = ROOT / "custom_components" / "plcassistant"

if str(CC) not in sys.path:
    sys.path.insert(0, str(CC))


def test_catalog_payload_lists_unit_ops() -> None:
    from dynamics.store import catalog_payload

    payload = catalog_payload()
    types = {op["type"] for op in payload["ops"]}
    assert types == {"tank", "pump", "orifice", "lag", "custom_ode"}
    pump = next(op for op in payload["ops"] if op["type"] == "pump")
    assert "cmd" in pump["binds"]
    assert "q_max" in pump["params"]


def test_validate_and_save_user_model(tmp_path: pathlib.Path) -> None:
    from dynamics.registry import add_model_dir, clear_extra_model_dirs, get_preset, list_presets
    from dynamics.store import save_user_model, validate_document

    bundled = CC / "dynamics" / "models" / "skid_composed.json"
    doc = json.loads(bundled.read_text(encoding="utf-8"))
    validated = validate_document(doc)
    assert validated["name"] == "skid_composed"

    clear_extra_model_dirs()
    path = save_user_model(tmp_path, "toy_skid", doc)
    assert path.is_file()
    add_model_dir(tmp_path / "plcassistant" / "models")
    assert "toy_skid" in list_presets()
    model = get_preset("toy_skid")
    assert "h_tank" in model.state
    clear_extra_model_dirs()


def test_validate_rejects_unknown_op() -> None:
    from dynamics.store import validate_document

    with pytest.raises(ValueError):
        validate_document(
            {
                "version": "1.0",
                "name": "bad",
                "inputs": [],
                "outputs": {},
                "ops": [{"id": "x", "type": "not_an_op", "bind": {}}],
            }
        )


def test_seed_skid_composed(tmp_path: pathlib.Path) -> None:
    from dynamics.store import load_user_model, seed_skid_composed

    bundled = CC / "dynamics" / "models" / "skid_composed.json"
    created = seed_skid_composed(tmp_path, bundled)
    assert created is not None and created.is_file()
    assert seed_skid_composed(tmp_path, bundled) is None  # idempotent
    doc = load_user_model(tmp_path, "skid_composed")
    assert doc["name"] == "skid_composed"


def test_editor_and_api_packaging() -> None:
    www = CC / "www" / "dynamics_editor.html"
    assert www.is_file()
    html = www.read_text(encoding="utf-8")
    assert "Dynamics block editor" in html
    assert "/api/plcassistant/dynamics" in html
    assert "Add block" in html
    assert "Soft-PLC tags" in html

    api = (CC / "dynamics" / "http_api.py").read_text(encoding="utf-8")
    assert "DynamicsEditorView" in api
    assert "DynamicsApplyView" in api
    assert "homeassistant" in api

    store = (CC / "dynamics" / "store.py").read_text(encoding="utf-8")
    assert "homeassistant" not in store

    init = (CC / "__init__.py").read_text(encoding="utf-8")
    assert "async_setup_dynamics_api" in init

    lovelace = (CC / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 13" in lovelace
    assert "path: dynamics" in lovelace
    assert "/api/plcassistant/dynamics/ui" in lovelace
    assert "title: Operate" in lovelace

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Toy example setup" in readme
    assert "Dynamics" in readme
    assert "0.1.25" in readme
