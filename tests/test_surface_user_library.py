"""Tests for user block library CRUD API (SWD-114).

Covers:
- add_user_template: stores a deep copy; rejects builtins
- remove_user_template: removes by template_id; raises KeyError when absent
- get_user_template: returns entry or None
- list_user_templates: returns all user templates
- make_user_template: constructs BlockTemplate from primitives
- register_user_templates: wires user templates into TemplateLibrary
- reset_instance works with user templates (round-trip)
- runtime exec's user body correctly after registration
"""

from __future__ import annotations

import pytest

from plcassistant.surface.model import (
    BlockInstance,
    BlockTemplate,
    PinDirection,
    PinSpec,
    Program,
    TemplateLibrary,
)
from plcassistant.surface.runtime import BlockRuntime, DictContext
from plcassistant.surface.schema import place_block, reset_instance
from plcassistant.surface.user_library import (
    add_user_template,
    get_user_template,
    list_user_templates,
    make_user_template,
    register_user_templates,
    remove_user_template,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _user_tmpl(template_id: str = "my_block", body: str = "out = x * 2") -> BlockTemplate:
    return BlockTemplate(
        template_id=template_id,
        library="user",
        description="Test user block",
        pins=[
            PinSpec("x", PinDirection.IN, "float", 0.0),
            PinSpec("out", PinDirection.OUT, "float"),
        ],
        params={"gain": 1.0},
        body=body,
        is_builtin=False,
    )


def _builtin_tmpl() -> BlockTemplate:
    return BlockTemplate(
        template_id="stock",
        library="builtin",
        description="Stock block",
        pins=[],
        params={},
        body="",
        is_builtin=True,
    )


# ---------------------------------------------------------------------------
# add_user_template
# ---------------------------------------------------------------------------


def test_add_user_template_stores_template():
    prog = Program()
    tmpl = _user_tmpl()
    add_user_template(prog, tmpl)
    assert "my_block" in prog.user_templates


def test_add_user_template_stores_deep_copy():
    prog = Program()
    tmpl = _user_tmpl()
    add_user_template(prog, tmpl)
    # Mutating original must not affect stored copy
    tmpl.params["gain"] = 999.0
    assert prog.user_templates["my_block"].params.get("gain") == 1.0


def test_add_user_template_overwrites_existing():
    prog = Program()
    t1 = _user_tmpl(body="out = x")
    t2 = _user_tmpl(body="out = x * 3")
    add_user_template(prog, t1)
    add_user_template(prog, t2)
    assert prog.user_templates["my_block"].body == "out = x * 3"


def test_add_builtin_template_raises():
    prog = Program()
    tmpl = _builtin_tmpl()
    with pytest.raises(ValueError, match="is_builtin=True"):
        add_user_template(prog, tmpl)


# ---------------------------------------------------------------------------
# remove_user_template
# ---------------------------------------------------------------------------


def test_remove_user_template_removes_entry():
    prog = Program()
    add_user_template(prog, _user_tmpl())
    remove_user_template(prog, "my_block")
    assert "my_block" not in prog.user_templates


def test_remove_user_template_missing_raises_key_error():
    prog = Program()
    with pytest.raises(KeyError, match="my_block"):
        remove_user_template(prog, "my_block")


# ---------------------------------------------------------------------------
# get_user_template
# ---------------------------------------------------------------------------


def test_get_user_template_returns_entry():
    prog = Program()
    tmpl = _user_tmpl()
    add_user_template(prog, tmpl)
    found = get_user_template(prog, "my_block")
    assert found is not None
    assert found.template_id == "my_block"


def test_get_user_template_missing_returns_none():
    prog = Program()
    assert get_user_template(prog, "ghost") is None


# ---------------------------------------------------------------------------
# list_user_templates
# ---------------------------------------------------------------------------


def test_list_user_templates_returns_all():
    prog = Program()
    add_user_template(prog, _user_tmpl("a"))
    add_user_template(prog, _user_tmpl("b"))
    tids = [t.template_id for t in list_user_templates(prog)]
    assert set(tids) == {"a", "b"}


def test_list_user_templates_empty():
    prog = Program()
    assert list_user_templates(prog) == []


# ---------------------------------------------------------------------------
# make_user_template
# ---------------------------------------------------------------------------


def test_make_user_template_basic():
    tmpl = make_user_template(
        "gain_block",
        body="out = x * gain",
        pins=[
            {"name": "x", "direction": "IN", "data_type": "float", "default": 0.0},
            {"name": "out", "direction": "OUT", "data_type": "float"},
        ],
        params={"gain": 1.0},
    )
    assert tmpl.template_id == "gain_block"
    assert tmpl.library == "user"
    assert tmpl.is_builtin is False
    assert len(tmpl.pins) == 2
    assert tmpl.pins[0].name == "x"
    assert tmpl.pins[0].direction == PinDirection.IN
    assert tmpl.pins[1].direction == PinDirection.OUT
    assert tmpl.params["gain"] == 1.0


def test_make_user_template_invalid_direction_raises():
    with pytest.raises(ValueError, match="invalid direction"):
        make_user_template(
            "bad",
            body="pass",
            pins=[{"name": "p", "direction": "SIDEWAYS"}],
        )


def test_make_user_template_no_pins():
    tmpl = make_user_template("empty_block", body="pass")
    assert tmpl.pins == []
    assert tmpl.params == {}


def test_make_user_template_params_deep_copied():
    params = {"gain": 1.0, "offset": [0.0]}
    tmpl = make_user_template("t", body="pass", params=params)
    params["gain"] = 99.0
    params["offset"].append(1.0)
    assert tmpl.params["gain"] == 1.0
    assert tmpl.params["offset"] == [0.0]


# ---------------------------------------------------------------------------
# register_user_templates
# ---------------------------------------------------------------------------


def test_register_user_templates_wires_into_library():
    prog = Program()
    tmpl = _user_tmpl()
    add_user_template(prog, tmpl)
    lib = TemplateLibrary()
    register_user_templates(lib, prog)
    found = lib.get("user", "my_block")
    assert found is not None
    assert found.template_id == "my_block"


def test_register_user_templates_empty_program():
    prog = Program()
    lib = TemplateLibrary()
    register_user_templates(lib, prog)
    assert len(lib) == 0


def test_register_user_templates_does_not_clobber_builtins():
    builtin_tmpl = BlockTemplate(
        template_id="level_pi", library="builtin", is_builtin=True,
        description="builtin", pins=[], params={}, body="",
    )
    lib = TemplateLibrary()
    lib.register(builtin_tmpl)
    # User templates keyed on ("user", ...) should not affect ("builtin", ...)
    prog = Program()
    tmpl = _user_tmpl("level_pi")  # same template_id but library="user"
    add_user_template(prog, tmpl)
    register_user_templates(lib, prog)
    assert lib.get("builtin", "level_pi") is builtin_tmpl
    assert lib.get("user", "level_pi") is not None


# ---------------------------------------------------------------------------
# reset_instance works with user templates
# ---------------------------------------------------------------------------


def test_reset_instance_user_template():
    tmpl = _user_tmpl()
    inst = place_block(tmpl, "i1", params={"gain": 9.9})
    reset = reset_instance(inst, tmpl)
    assert reset.params["gain"] == pytest.approx(1.0)
    assert reset.instance_id == "i1"


def test_reset_instance_wrong_user_template_raises():
    t_a = _user_tmpl("block_a")
    t_b = _user_tmpl("block_b")
    inst = place_block(t_a, "i1")
    with pytest.raises(ValueError, match="template mismatch"):
        reset_instance(inst, t_b)


# ---------------------------------------------------------------------------
# Runtime executes user body (with user templates in program)
# ---------------------------------------------------------------------------


def test_runtime_executes_user_body_from_program_user_templates():
    prog = Program()
    tmpl = make_user_template(
        "doubler",
        body="out = x * 2",
        pins=[
            {"name": "x", "direction": "IN", "data_type": "float", "default": 0.0},
            {"name": "out", "direction": "OUT", "data_type": "float"},
        ],
    )
    add_user_template(prog, tmpl)
    inst = place_block(prog.user_templates["doubler"], "d1")
    prog.instances["d1"] = inst
    prog.execution_order = ["d1"]

    lib = TemplateLibrary()
    register_user_templates(lib, prog)
    runtime = BlockRuntime(lib)
    ctx = DictContext({"d1.x": 5.0})
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("d1.out") == pytest.approx(10.0)


def test_runtime_uses_instance_params_in_user_body():
    prog = Program()
    tmpl = make_user_template(
        "scaler",
        body="out = x * scale",
        pins=[
            {"name": "x", "direction": "IN", "data_type": "float", "default": 0.0},
            {"name": "out", "direction": "OUT", "data_type": "float"},
        ],
        params={"scale": 1.0},
    )
    add_user_template(prog, tmpl)
    inst = place_block(prog.user_templates["scaler"], "s1", params={"scale": 3.0})
    prog.instances["s1"] = inst
    prog.execution_order = ["s1"]

    lib = TemplateLibrary()
    register_user_templates(lib, prog)
    runtime = BlockRuntime(lib)
    ctx = DictContext({"s1.x": 4.0})
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("s1.out") == pytest.approx(12.0)  # 4 * 3


def test_runtime_user_body_state_persists():
    prog = Program()
    tmpl = make_user_template(
        "counter",
        body="state['n'] = state.get('n', 0) + 1\nout = state['n']",
        pins=[{"name": "out", "direction": "OUT", "data_type": "float"}],
    )
    add_user_template(prog, tmpl)
    inst = place_block(prog.user_templates["counter"], "c1")
    prog.instances["c1"] = inst
    prog.execution_order = ["c1"]

    lib = TemplateLibrary()
    runtime = BlockRuntime(lib)
    ctx = DictContext()
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("c1.out") == pytest.approx(1.0)
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("c1.out") == pytest.approx(2.0)
