"""SWD-251 acceptance: one Max pump flow knob + Soft-PLC cascade sync."""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CC = ROOT / "custom_components" / "plcassistant"
if str(CC) not in sys.path:
    sys.path.insert(0, str(CC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_normalize_pump_capacity_write_through() -> None:
    from dynamics.store import extract_q_pump_max, normalize_pump_capacity

    bundled = CC / "dynamics" / "models" / "skid_composed.json"
    doc = json.loads(bundled.read_text(encoding="utf-8"))
    pump = next(op for op in doc["ops"] if op["type"] == "pump")
    pump["params"]["q_max"] = 20.0
    doc["params"]["q_pump_max"] = 8.0

    out = normalize_pump_capacity(doc)
    assert out["params"]["q_pump_max"] == pytest.approx(20.0)
    pump_out = next(op for op in out["ops"] if op["type"] == "pump")
    assert pump_out["params"]["q_max"] == "q_pump_max"
    assert extract_q_pump_max(out) == pytest.approx(20.0)


def test_save_user_model_normalizes_pump_alias(tmp_path: pathlib.Path) -> None:
    from dynamics.store import load_user_model, save_user_model

    bundled = CC / "dynamics" / "models" / "skid_composed.json"
    doc = json.loads(bundled.read_text(encoding="utf-8"))
    pump = next(op for op in doc["ops"] if op["type"] == "pump")
    pump["params"]["q_max"] = 15.5
    save_user_model(tmp_path, "skid_cap", doc)
    reloaded = load_user_model(tmp_path, "skid_cap")
    assert reloaded["params"]["q_pump_max"] == pytest.approx(15.5)
    pump = next(op for op in reloaded["ops"] if op["type"] == "pump")
    assert pump["params"]["q_max"] == "q_pump_max"


def test_plant_capacity_bridge_round_trip(tmp_path: pathlib.Path) -> None:
    from plcassistant.io.ha_config_bridge import (
        read_plant_capacity,
        write_plant_capacity,
    )

    assert write_plant_capacity(12.5, root=tmp_path, source="test") is True
    assert read_plant_capacity(root=tmp_path) == pytest.approx(12.5)
    assert write_plant_capacity(-1.0, root=tmp_path) is False
    assert write_plant_capacity(float("nan"), root=tmp_path) is False


def test_repair_cascade_tracks_plant_capacity(tmp_path: pathlib.Path, monkeypatch) -> None:
    from plcassistant.io import ha_config_bridge as bridge
    from plcassistant.surface.builtin import (
        CASCADE_CMD_SPEED_MAX,
        wedge_cascade_program,
    )
    from plcassistant.surface.schema import program_from_dict, repair_cascade_pid_limits

    monkeypatch.setenv("PLCASSISTANT_HA_CONFIG", str(tmp_path))
    assert bridge.write_plant_capacity(14.0, root=tmp_path) is True

    prog = program_from_dict(wedge_cascade_program())
    prog.instances["level_pi"].params["cv_max"] = 6.0
    prog.instances["flow_pi"].params["cv_max"] = 6.0
    assert repair_cascade_pid_limits(prog) is True
    assert prog.instances["level_pi"].params["cv_max"] == pytest.approx(14.0)
    assert prog.instances["flow_pi"].params["cv_max"] == pytest.approx(
        CASCADE_CMD_SPEED_MAX
    )


def test_cascade_default_sp_flow_matches_q_pump_max() -> None:
    from plcassistant.surface.builtin import CASCADE_SP_FLOW_MAX, wedge_cascade_program
    from plcassistant.surface.schema import program_from_dict
    from plcassistant.wedge.control import CascadeConfig
    from plcassistant.wedge.process import ProcessConfig

    assert CASCADE_SP_FLOW_MAX == pytest.approx(8.0)
    assert CascadeConfig().sp_flow_max == pytest.approx(8.0)
    assert ProcessConfig().q_pump_max == pytest.approx(8.0)
    prog = program_from_dict(wedge_cascade_program())
    assert prog.instances["level_pi"].params["cv_max"] == pytest.approx(8.0)
    assert prog.instances["flow_pi"].params["cv_max"] == pytest.approx(100.0)


def test_appstate_syncs_level_cv_from_capacity(tmp_path: pathlib.Path, monkeypatch) -> None:
    from plcassistant.app.server import AppState
    from plcassistant.io.ha_config_bridge import write_plant_capacity
    from plcassistant.surface.builtin import wedge_softplc_project

    monkeypatch.setenv("PLCASSISTANT_HA_CONFIG", str(tmp_path))
    write_plant_capacity(18.0, root=tmp_path, source="dynamics")
    path = tmp_path / "program.json"
    path.write_text(json.dumps(wedge_softplc_project()), encoding="utf-8")
    state = AppState(program_path=str(path))
    tank = state.saved_project.programs["tank"]
    assert tank.instances["level_pi"].params["cv_max"] == pytest.approx(18.0)
    assert tank.instances["flow_pi"].params["cv_max"] == pytest.approx(100.0)

    write_plant_capacity(22.0, root=tmp_path, source="dynamics")
    assert state.sync_plant_capacity_limits() is True
    assert tank.instances["level_pi"].params["cv_max"] == pytest.approx(22.0)


def test_normalize_pump_capacity_string_numeric() -> None:
    from dynamics.store import normalize_pump_capacity

    bundled = CC / "dynamics" / "models" / "skid_composed.json"
    doc = json.loads(bundled.read_text(encoding="utf-8"))
    pump = next(op for op in doc["ops"] if op["type"] == "pump")
    pump["params"]["q_max"] = "17"
    out = normalize_pump_capacity(doc)
    assert out["params"]["q_pump_max"] == pytest.approx(17.0)
    pump_out = next(op for op in out["ops"] if op["type"] == "pump")
    assert pump_out["params"]["q_max"] == "q_pump_max"


def test_publish_uses_normalized_capacity(tmp_path: pathlib.Path) -> None:
    """Bridge value follows pump-block write-through, not a stale global."""
    from dynamics.store import extract_q_pump_max, normalize_pump_capacity

    bundled = CC / "dynamics" / "models" / "skid_composed.json"
    doc = json.loads(bundled.read_text(encoding="utf-8"))
    doc["params"]["q_pump_max"] = 8.0
    pump = next(op for op in doc["ops"] if op["type"] == "pump")
    pump["params"]["q_max"] = 21.0
    # Raw extract would still see 8; publish path must normalize first.
    assert extract_q_pump_max(doc) == pytest.approx(8.0)
    assert extract_q_pump_max(normalize_pump_capacity(doc)) == pytest.approx(21.0)


def test_runtime_snapshot_syncs_capacity(tmp_path: pathlib.Path, monkeypatch) -> None:
    from plcassistant.app.server import AppState
    from plcassistant.io.ha_config_bridge import write_plant_capacity
    from plcassistant.surface.builtin import wedge_softplc_project

    monkeypatch.setenv("PLCASSISTANT_HA_CONFIG", str(tmp_path))
    write_plant_capacity(10.0, root=tmp_path)
    path = tmp_path / "program.json"
    path.write_text(json.dumps(wedge_softplc_project()), encoding="utf-8")
    state = AppState(program_path=str(path))
    write_plant_capacity(19.0, root=tmp_path)
    state.runtime_snapshot()
    tank = state.saved_project.programs["tank"]
    assert tank.instances["level_pi"].params["cv_max"] == pytest.approx(19.0)


def test_editor_html_capacity_write_through_markers() -> None:
    html = (CC / "www" / "dynamics_editor.html").read_text(encoding="utf-8")
    assert "data-capacity-global" in html
    assert "Writes through to global" in html
    assert "single plant capacity knob" in html
    assert 'op.params.q_max = "q_pump_max"' in html


def test_canvas_cascade_labels() -> None:
    canvas = (ROOT / "plcassistant" / "app" / "_canvas.py").read_text(encoding="utf-8")
    assert "Max flow SP (L/min)" in canvas
    assert "Max pump command (%)" in canvas
    assert "not L/min" in canvas
    dual = ROOT / "plc_assistant" / "plcassistant" / "app" / "_canvas.py"
    assert dual.is_file()
    assert "Max flow SP (L/min)" in dual.read_text(encoding="utf-8")


def test_catalog_exposes_pump_capacity_meta() -> None:
    from dynamics.store import catalog_payload

    payload = catalog_payload()
    pump = next(op for op in payload["ops"] if op["type"] == "pump")
    assert pump["param_capacity_keys"]["q_max"] == "q_pump_max"
    assert "Max pump flow" in pump["param_labels"]["q_max"]


def test_dual_tree_swd251_synced() -> None:
    pairs = [
        (
            "custom_components/plcassistant/dynamics/store.py",
            "plc_assistant/custom_components/plcassistant/dynamics/store.py",
        ),
        (
            "custom_components/plcassistant/www/dynamics_editor.html",
            "plc_assistant/custom_components/plcassistant/www/dynamics_editor.html",
        ),
        (
            "custom_components/plcassistant/ha_config_bridge.py",
            "plc_assistant/custom_components/plcassistant/ha_config_bridge.py",
        ),
        (
            "plcassistant/io/ha_config_bridge.py",
            "plc_assistant/plcassistant/io/ha_config_bridge.py",
        ),
        (
            "plcassistant/surface/schema.py",
            "plc_assistant/plcassistant/surface/schema.py",
        ),
        (
            "plcassistant/app/server.py",
            "plc_assistant/plcassistant/app/server.py",
        ),
    ]
    for left, right in pairs:
        a = (ROOT / left).read_text(encoding="utf-8")
        b = (ROOT / right).read_text(encoding="utf-8")
        assert a == b, f"dual tree drift: {left} vs {right}"
    assert "write_plant_capacity" in (
        ROOT / "plcassistant" / "io" / "ha_config_bridge.py"
    ).read_text(encoding="utf-8")
    assert "normalize_pump_capacity" in (
        ROOT / "custom_components" / "plcassistant" / "dynamics" / "store.py"
    ).read_text(encoding="utf-8")


def test_version_lock_0_1_54() -> None:
    cfg = (ROOT / "plc_assistant" / "config.yaml").read_text(encoding="utf-8")
    man = (CC / "manifest.json").read_text(encoding="utf-8")
    dual_man = (
        ROOT / "plc_assistant" / "custom_components" / "plcassistant" / "manifest.json"
    ).read_text(encoding="utf-8")
    assert 'version: "0.1.56"' in cfg
    assert '"version": "0.1.56"' in man
    assert '"version": "0.1.56"' in dual_man
