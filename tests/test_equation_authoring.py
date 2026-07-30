"""SWD-167: per-equation authoring + example processes (HA-free)."""

from __future__ import annotations

import math
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CC = ROOT / "custom_components" / "plcassistant"

if str(CC) not in sys.path:
    sys.path.insert(0, str(CC))


def _step(model, dt: float, n: int) -> None:
    for _ in range(n):
        model.step(dt)


def test_catalog_exposes_equation_templates() -> None:
    from dynamics.equations import describe_op_equations
    from dynamics.store import catalog_payload

    payload = catalog_payload()
    assert "measurement_help" in payload
    orifice = next(op for op in payload["ops"] if op["type"] == "orifice")
    assert orifice["equation_templates"]
    assert orifice["equations"]
    assert any(e["kind"] == "algebraic" for e in orifice["equations"])

    forms = describe_op_equations(
        "tank",
        {"h": "h_tank", "q_in": "qin", "q_out": "qout"},
        {"area": 0.05},
    )
    assert forms[0].kind == "state"
    assert "h_tank" in forms[0].left
    assert "0.05" in forms[0].right


def test_example_fo_lag() -> None:
    """Minimal custom state equation + identity measurement."""
    from dynamics.compile import document_to_model, parse_model_document

    doc = parse_model_document(
        {
            "version": "1.0",
            "name": "fo_lag",
            "inputs": ["u"],
            "measurements": [{"tag": "Y_OUT", "expr": "y"}],
            "params": {"tau": 1.0},
            "initial": {"y": 0.0},
            "ops": [
                {
                    "id": "plant",
                    "type": "custom_ode",
                    "params": {"derivatives": {"y": "(u - y) / tau"}},
                }
            ],
        }
    )
    model = document_to_model(doc)
    model.set_input("u", 1.0)
    _step(model, 0.1, 50)
    assert model.state["y"] == pytest.approx(1.0, abs=0.05)
    assert model.outputs()["Y_OUT"] == pytest.approx(model.state["y"])


def test_example_single_tank_orifice_measurements() -> None:
    """Catalog tank + orifice; FT measurement uses closed-form k*sqrt(h)."""
    from dynamics.compile import document_to_model, parse_model_document

    doc = parse_model_document(
        {
            "version": "1.0",
            "name": "tank_orifice",
            "inputs": ["qin"],
            "measurements": [
                {"tag": "LT", "expr": "h"},
                {"tag": "FT", "expr": "k * sqrt(h)"},
            ],
            "params": {"k": 2.0},
            "initial": {"h": 0.25},
            "ops": [
                {
                    "id": "drain",
                    "type": "orifice",
                    "params": {"k": "k"},
                    "bind": {"h": "h", "q": "q"},
                },
                {
                    "id": "tank",
                    "type": "tank",
                    "params": {"area": 0.05},
                    "bind": {"h": "h", "q_in": "qin", "q_out": "q"},
                },
            ],
        }
    )
    model = document_to_model(doc)
    model.set_input("qin", 0.0)
    outs0 = model.outputs()
    assert outs0["LT"] == pytest.approx(0.25)
    assert outs0["FT"] == pytest.approx(2.0 * math.sqrt(0.25))
    _step(model, 0.1, 20)
    assert model.state["h"] < 0.25
    assert model.outputs()["FT"] == pytest.approx(2.0 * math.sqrt(model.state["h"]), rel=1e-6)


def test_example_heated_tank_non_identity_measurement() -> None:
    """Two custom states; TT = T + bias (measurement ≠ state)."""
    from dynamics.compile import document_to_model, parse_model_document

    doc = parse_model_document(
        {
            "version": "1.0",
            "name": "heated_tank",
            "inputs": ["q_heat"],
            "measurements": [
                {"tag": "LT", "expr": "h"},
                {"tag": "TT", "expr": "T + bias"},
            ],
            "params": {"bias": 2.0, "UA": 0.1, "T_amb": 20.0, "cp": 1.0},
            "initial": {"h": 1.0, "T": 25.0},
            "ops": [
                {
                    "id": "thermal",
                    "type": "custom_ode",
                    "params": {
                        "derivatives": {
                            "h": "0",
                            "T": "(q_heat - UA * (T - T_amb)) / cp",
                        }
                    },
                }
            ],
        }
    )
    model = document_to_model(doc)
    model.set_input("q_heat", 0.0)
    assert model.outputs()["TT"] == pytest.approx(27.0)
    assert model.outputs()["LT"] == pytest.approx(1.0)
    # Cool toward ambient.
    _step(model, 0.1, 100)
    assert model.state["T"] < 25.0
    assert model.outputs()["TT"] == pytest.approx(model.state["T"] + 2.0)


def test_example_mass_spring_damper() -> None:
    from dynamics.compile import document_to_model, parse_model_document

    doc = parse_model_document(
        {
            "version": "1.0",
            "name": "msd",
            "inputs": ["f"],
            "measurements": [
                {"tag": "POS", "expr": "x"},
                {"tag": "VEL", "expr": "v"},
            ],
            "params": {"m": 1.0, "k": 4.0, "c": 0.5},
            "initial": {"x": 1.0, "v": 0.0},
            "ops": [
                {
                    "id": "mech",
                    "type": "custom_ode",
                    "params": {
                        "derivatives": {
                            "x": "v",
                            "v": "(f - k * x - c * v) / m",
                        }
                    },
                }
            ],
        }
    )
    model = document_to_model(doc)
    model.set_input("f", 0.0)
    _step(model, 0.01, 200)
    # Underdamped decay from x=1 — energy leaves the spring.
    assert abs(model.state["x"]) < 1.0
    assert model.outputs()["POS"] == model.state["x"]
    assert model.outputs()["VEL"] == model.state["v"]


def test_example_rc_filter_with_algebraic() -> None:
    from dynamics.compile import document_to_model, parse_model_document

    doc = parse_model_document(
        {
            "version": "1.0",
            "name": "rc",
            "inputs": ["u"],
            "measurements": [
                {"tag": "V_OUT", "expr": "v_c"},
                {"tag": "I_OUT", "expr": "i"},
            ],
            "params": {"R": 1.0, "C": 1.0},
            "initial": {"v_c": 0.0},
            "ops": [
                {
                    "id": "rc",
                    "type": "custom_ode",
                    "params": {
                        "derivatives": {"v_c": "(u - v_c) / (R * C)"},
                        "algebraic": {"i": "(u - v_c) / R"},
                    },
                }
            ],
        }
    )
    model = document_to_model(doc)
    model.set_input("u", 1.0)
    # Algebraic i is not in state; measurement uses state+params+inputs only.
    # So I_OUT uses closed form (u - v_c)/R via measurement expr — use that:
    doc2 = parse_model_document(
        {
            "version": "1.0",
            "name": "rc2",
            "inputs": ["u"],
            "measurements": [
                {"tag": "V_OUT", "expr": "v_c"},
                {"tag": "I_OUT", "expr": "(u - v_c) / R"},
            ],
            "params": {"R": 1.0, "C": 1.0},
            "initial": {"v_c": 0.0},
            "ops": [
                {
                    "id": "rc",
                    "type": "custom_ode",
                    "params": {
                        "derivatives": {"v_c": "(u - v_c) / (R * C)"},
                        "algebraic": {"i": "(u - v_c) / R"},
                    },
                }
            ],
        }
    )
    model = document_to_model(doc2)
    model.set_input("u", 1.0)
    assert model.outputs()["I_OUT"] == pytest.approx(1.0)
    _step(model, 0.1, 50)
    assert model.state["v_c"] == pytest.approx(1.0, abs=0.05)
    assert model.outputs()["I_OUT"] == pytest.approx(
        (1.0 - model.state["v_c"]) / 1.0, abs=1e-6
    )


def test_legacy_outputs_synthesize_measurements() -> None:
    from dynamics.compile import document_to_model, parse_model_document

    doc = parse_model_document(
        {
            "version": "1.0",
            "name": "legacy",
            "inputs": ["u"],
            "outputs": {"Y": "y"},
            "params": {"tau": 0.2},
            "initial": {"y": 0.0},
            "ops": [
                {
                    "id": "lag",
                    "type": "lag",
                    "params": {"tau": "tau"},
                    "bind": {"u": "u", "y": "y"},
                }
            ],
        }
    )
    assert doc.measurements[0].tag == "Y"
    assert doc.measurements[0].expr == "y"
    model = document_to_model(doc)
    model.set_input("u", 10.0)
    _step(model, 0.1, 30)
    assert model.outputs()["Y"] == pytest.approx(model.state["y"])


def test_predefined_lag_equations_match_runtime() -> None:
    from dynamics.compile import document_to_model, parse_model_document
    from dynamics.equations import describe_op_equations

    forms = describe_op_equations(
        "lag", {"u": "cmd", "y": "speed"}, {"tau": 0.2}
    )
    assert forms[0].left == "d(speed)/dt"
    assert "cmd" in forms[0].right

    doc = parse_model_document(
        {
            "version": "1.0",
            "name": "lag_only",
            "inputs": ["cmd"],
            "measurements": [{"tag": "SC", "expr": "speed"}],
            "params": {},
            "initial": {"speed": 0.0},
            "ops": [
                {
                    "id": "fb",
                    "type": "lag",
                    "params": {"tau": 0.2},
                    "bind": {"u": "cmd", "y": "speed"},
                }
            ],
        }
    )
    model = document_to_model(doc)
    model.set_input("cmd", 50.0)
    _step(model, 0.1, 40)
    assert model.state["speed"] == pytest.approx(50.0, abs=0.5)


def test_editor_shows_state_and_measurement_rows() -> None:
    html = (CC / "www" / "dynamics_editor.html").read_text(encoding="utf-8")
    assert "State equations" in html
    assert "Measurement equations" in html
    assert "d(state)/dt" in html
    assert "btn-add-state" in html
    assert "btn-add-meas" in html
    assert "equation_templates" in (CC / "dynamics" / "store.py").read_text(encoding="utf-8")
    assert (CC / "dynamics" / "equations.py").is_file()
