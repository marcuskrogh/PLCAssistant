"""SWD-144: unit-ops, expression sandbox, composed-skid oracle."""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CC = ROOT / "custom_components" / "plcassistant"
DYN = CC / "dynamics"

if str(CC) not in sys.path:
    sys.path.insert(0, str(CC))


def test_dynamics_modules_remain_ha_free() -> None:
    for name in (
        "core.py",
        "skid.py",
        "plant.py",
        "expr.py",
        "ops.py",
        "compile.py",
        "registry.py",
        "__init__.py",
    ):
        text = (DYN / name).read_text(encoding="utf-8")
        assert "homeassistant" not in text
    assert (DYN / "models" / "skid_composed.json").is_file()


def test_expression_sandbox_allow_and_deny() -> None:
    from dynamics.expr import ExpressionError, compile_expr, eval_expr

    assert eval_expr("1 + 2 * 3", {}) == pytest.approx(7.0)
    assert eval_expr("sqrt(h_tank)", {"h_tank": 0.25}) == pytest.approx(0.5)
    assert eval_expr("clamp(x, 0, 1)", {"x": 1.5}) == pytest.approx(1.0)
    assert eval_expr("min(a, b) + max(a, b)", {"a": 1.0, "b": 3.0}) == pytest.approx(4.0)

    for bad in (
        "__import__('os')",
        "os.system('x')",
        "(lambda x: x)(1)",
        "[x for x in [1]]",
        "a.b",
        "open('x')",
        "sin(1)",
    ):
        with pytest.raises(ExpressionError):
            compile_expr(bad)


def test_catalog_ops_registered() -> None:
    from dynamics.ops import OP_CATALOG

    assert set(OP_CATALOG) >= {"tank", "pump", "orifice", "lag", "custom_ode"}


def test_skid_composed_oracle_matches_code_skid() -> None:
    from dynamics.registry import get_preset
    from dynamics.skid import SkidModel

    code = SkidModel()
    composed = get_preset("skid_composed")
    cmds = [0.0, 40.0, 40.0, 80.0, 0.0, 0.0]
    dt = 0.1
    for cmd in cmds * 5:
        code.set_input("cmd_speed", cmd)
        composed.set_input("cmd_speed", cmd)
        s = code.step(dt)
        c = composed.step(dt)
        assert c["h_tank"] == pytest.approx(s["h_tank"], abs=1e-9)
        assert c["h_res"] == pytest.approx(s["h_res"], abs=1e-9)
        assert c["ft_inlet"] == pytest.approx(s["ft_inlet"], abs=1e-9)
        assert c["sc_pump"] == pytest.approx(s["sc_pump"], abs=1e-9)


def test_loader_rejects_bad_documents() -> None:
    from dynamics.compile import parse_model_document
    from dynamics.expr import ExpressionError

    with pytest.raises(ExpressionError):
        parse_model_document({"version": "9.9", "name": "x", "ops": []})
    with pytest.raises(ExpressionError):
        parse_model_document(
            {
                "version": "1.0",
                "name": "x",
                "inputs": [],
                "outputs": {"LT_TANK": "h"},
                "params": {},
                "initial": {"h": 0.1},
                "ops": [{"id": "a", "type": "nope", "bind": {}}],
            }
        )
    with pytest.raises(ExpressionError):
        parse_model_document(
            {
                "version": "1.0",
                "name": "x",
                "inputs": ["u"],
                "outputs": {"Y": "x"},
                "params": {},
                "initial": {"x": 0.0},
                "ops": [
                    {
                        "id": "c",
                        "type": "custom_ode",
                        "params": {"derivatives": {"x": "__import__('os')"}},
                        "bind": {},
                    }
                ],
            }
        )


def test_custom_ode_integrates() -> None:
    from dynamics.compile import document_to_model, parse_model_document

    doc = parse_model_document(
        {
            "version": "1.0",
            "name": "decay",
            "inputs": [],
            "outputs": {"X": "x"},
            "params": {"k": 1.0},
            "initial": {"x": 1.0},
            "ops": [
                {
                    "id": "ode",
                    "type": "custom_ode",
                    "params": {"derivatives": {"x": "-k * x"}},
                    "bind": {},
                }
            ],
        }
    )
    model = document_to_model(doc)
    model.step(0.1)
    assert model.state["x"] == pytest.approx(0.9, abs=1e-12)


def test_plant_simulator_accepts_composed_preset() -> None:
    from dynamics.plant import PlantSimulator

    published: dict[str, dict] = {}

    def publish(tag: str, payload: str) -> None:
        published[tag] = json.loads(payload)

    plant = PlantSimulator.for_preset(publish, preset="skid_composed")
    plant.apply_status_payload({"state": "running", "scan_period_s": 0.1})
    plant.apply_cmd_speed(50.0)
    for _ in range(20):
        plant.tick(0.1)
    assert published["FT_INLET"]["value"] > 0.1
    assert "LT_TANK" in plant.owned_tags


def test_list_presets_includes_skid_and_composed() -> None:
    from dynamics.registry import list_presets

    names = set(list_presets())
    assert "skid" in names
    assert "skid_composed" in names


def test_default_live_preset_remains_code_skid() -> None:
    from dynamics.registry import get_preset
    from dynamics.skid import SkidModel

    assert isinstance(get_preset("skid"), SkidModel)
