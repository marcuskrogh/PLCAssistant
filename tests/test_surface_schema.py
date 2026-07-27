"""Tests for block model + YAML schema (SWD-119).

Covers:
- copy-on-place independence (instance vs template, instance vs instance)
- reset_instance semantics
- program_to_dict / program_from_dict round-trip
- execution_order: explicit, default insertion order, validation errors
- validate_program: unknown instances, duplicate order, conflicting wires
- validation errors for missing required fields
- TemplateLibrary seam: register, get, all_templates
- user_template round-trip; built-in templates not stored in program dict
- injectable design: no hard-wired I/O, no HA imports
"""

from __future__ import annotations

import copy

import pytest

from plcassistant.surface import (
    BlockInstance,
    BlockTemplate,
    PinDirection,
    PinSpec,
    Program,
    TemplateLibrary,
    Wire,
    place_block,
    program_from_dict,
    program_to_dict,
    reset_instance,
    validate_program,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _pid_template(
    template_id: str = "pid",
    library: str = "user",
    *,
    is_builtin: bool = False,
) -> BlockTemplate:
    return BlockTemplate(
        template_id=template_id,
        library=library,
        description="PID controller",
        pins=[
            PinSpec("pv", PinDirection.IN, "float", 0.0),
            PinSpec("sp", PinDirection.IN, "float", 0.0),
            PinSpec("cv", PinDirection.OUT, "float"),
        ],
        params={"kp": 1.0, "ki": 0.0, "kd": 0.0},
        body="cv = kp * (sp - pv)",
        is_builtin=is_builtin,
    )


def _sensor_template(library: str = "builtin") -> BlockTemplate:
    return BlockTemplate(
        template_id="level_sensor",
        library=library,
        description="Level sensor block",
        pins=[PinSpec("level_out", PinDirection.OUT, "float")],
        params={},
        is_builtin=(library == "builtin"),
    )


def _minimal_program_dict() -> dict:
    return {
        "version": "1.0",
        "instances": {
            "inst_a": {"template_id": "pid", "library": "user", "params": {}},
        },
        "wires": [],
        "execution_order": ["inst_a"],
    }


# ---------------------------------------------------------------------------
# place_block: copy-on-place independence
# ---------------------------------------------------------------------------


def test_place_block_params_independent_of_template():
    """Mutating placed instance params must not affect the template."""
    tmpl = _pid_template()
    inst = place_block(tmpl, "i1")
    inst.params["kp"] = 99.0
    assert tmpl.params["kp"] == 1.0, "template params must not be modified"


def test_place_block_two_instances_independent():
    """Two placed copies are independent of each other."""
    tmpl = _pid_template()
    inst_a = place_block(tmpl, "i1")
    inst_b = place_block(tmpl, "i2")
    inst_a.params["kp"] = 42.0
    assert inst_b.params["kp"] == 1.0
    assert tmpl.params["kp"] == 1.0


def test_place_block_override_params():
    """Caller-supplied params are merged on top of template defaults."""
    tmpl = _pid_template()
    inst = place_block(tmpl, "i1", params={"kp": 5.0})
    assert inst.params["kp"] == 5.0
    assert inst.params["ki"] == 0.0  # template default preserved
    assert tmpl.params["kp"] == 1.0  # template unchanged


def test_place_block_override_params_deep_copy():
    """Caller-supplied mutable param values are deep-copied."""
    tmpl = BlockTemplate(
        template_id="block_with_list",
        library="user",
        params={"tags": ["a", "b"]},
    )
    caller_params: dict = {"tags": ["x"]}
    inst = place_block(tmpl, "i1", params=caller_params)
    caller_params["tags"].append("y")  # mutate caller's dict
    assert inst.params["tags"] == ["x"]  # instance unaffected


def test_place_block_sets_instance_id_and_identity():
    tmpl = _pid_template()
    inst = place_block(tmpl, "my_inst", x=10.0, y=20.0)
    assert inst.instance_id == "my_inst"
    assert inst.template_id == tmpl.template_id
    assert inst.library == tmpl.library
    assert inst.x == 10.0
    assert inst.y == 20.0


# ---------------------------------------------------------------------------
# reset_instance
# ---------------------------------------------------------------------------


def test_reset_instance_restores_template_defaults():
    tmpl = _pid_template()
    inst = place_block(tmpl, "i1", params={"kp": 9.9, "ki": 3.3})
    reset = reset_instance(inst, tmpl)
    assert reset.params["kp"] == 1.0
    assert reset.params["ki"] == 0.0
    assert reset.params["kd"] == 0.0


def test_reset_instance_preserves_position_and_id():
    tmpl = _pid_template()
    inst = place_block(tmpl, "i1", x=50.0, y=75.0, params={"kp": 9.9})
    reset = reset_instance(inst, tmpl)
    assert reset.instance_id == "i1"
    assert reset.x == 50.0
    assert reset.y == 75.0


def test_reset_instance_result_independent_of_template():
    """Mutating reset result must not affect the template."""
    tmpl = _pid_template()
    inst = place_block(tmpl, "i1", params={"kp": 9.9})
    reset = reset_instance(inst, tmpl)
    reset.params["kp"] = 0.0
    assert tmpl.params["kp"] == 1.0


def test_reset_instance_wrong_template_raises():
    tmpl_a = _pid_template(template_id="pid_a")
    tmpl_b = _pid_template(template_id="pid_b")
    inst = place_block(tmpl_a, "i1")
    with pytest.raises(ValueError, match="template mismatch"):
        reset_instance(inst, tmpl_b)


def test_reset_instance_wrong_library_raises():
    tmpl_user = _pid_template(library="user")
    tmpl_builtin = _pid_template(library="builtin")
    inst = place_block(tmpl_user, "i1")
    with pytest.raises(ValueError, match="template mismatch"):
        reset_instance(inst, tmpl_builtin)


# ---------------------------------------------------------------------------
# program_to_dict / program_from_dict round-trip
# ---------------------------------------------------------------------------


def _make_small_program() -> Program:
    tmpl = _pid_template()
    sensor = _sensor_template()
    inst_s = place_block(sensor, "inst_sensor")
    inst_p = place_block(tmpl, "inst_pid", params={"kp": 2.5}, x=100.0, y=200.0)
    return Program(
        instances={"inst_sensor": inst_s, "inst_pid": inst_p},
        wires=[
            Wire(
                src_instance="inst_sensor",
                src_pin="level_out",
                dst_instance="inst_pid",
                dst_pin="pv",
            )
        ],
        execution_order=["inst_sensor", "inst_pid"],
        user_templates={"pid": tmpl},
        version="1.0",
    )


def test_round_trip_dict_identity():
    """program_from_dict(program_to_dict(p)) reproduces the same logical program."""
    prog = _make_small_program()
    d = program_to_dict(prog)
    reloaded = program_from_dict(d)

    assert set(reloaded.instances.keys()) == set(prog.instances.keys())
    assert reloaded.execution_order == prog.execution_order
    assert len(reloaded.wires) == len(prog.wires)
    w = reloaded.wires[0]
    assert w.src_instance == "inst_sensor"
    assert w.src_pin == "level_out"
    assert w.dst_instance == "inst_pid"
    assert w.dst_pin == "pv"
    assert reloaded.instances["inst_pid"].params["kp"] == pytest.approx(2.5)
    assert reloaded.instances["inst_pid"].x == pytest.approx(100.0)
    assert reloaded.instances["inst_pid"].y == pytest.approx(200.0)
    assert reloaded.version == "1.0"


def test_round_trip_does_not_share_mutable_state():
    """Mutating reloaded instance params must not affect the original program dict."""
    prog = _make_small_program()
    d = program_to_dict(prog)
    reloaded = program_from_dict(d)
    reloaded.instances["inst_pid"].params["kp"] = 0.0
    # Re-serialise original dict — kp should still be 2.5
    assert d["instances"]["inst_pid"]["params"]["kp"] == pytest.approx(2.5)


def test_round_trip_empty_program():
    prog = Program()
    d = program_to_dict(prog)
    reloaded = program_from_dict(d)
    assert reloaded.instances == {}
    assert reloaded.wires == []
    assert reloaded.execution_order == []


# ---------------------------------------------------------------------------
# execution_order handling
# ---------------------------------------------------------------------------


def test_execution_order_defaults_to_insertion_order():
    """Absent execution_order in dict defaults to instance insertion order."""
    d = {
        "version": "1.0",
        "instances": {
            "b": {"template_id": "t", "library": "builtin", "params": {}},
            "a": {"template_id": "t", "library": "builtin", "params": {}},
        },
        "wires": [],
    }
    prog = program_from_dict(d)
    assert prog.execution_order == ["b", "a"]


def test_execution_order_explicit_subset_is_valid():
    """execution_order may reference a subset of instances (no error)."""
    d = {
        "version": "1.0",
        "instances": {
            "inst_a": {"template_id": "t", "library": "builtin", "params": {}},
            "inst_b": {"template_id": "t", "library": "builtin", "params": {}},
        },
        "wires": [],
        "execution_order": ["inst_a"],
    }
    prog = program_from_dict(d)
    assert prog.execution_order == ["inst_a"]


def test_execution_order_unknown_instance_raises():
    d = _minimal_program_dict()
    d["execution_order"] = ["inst_a", "inst_UNKNOWN"]
    with pytest.raises(ValueError, match="unknown instance"):
        program_from_dict(d)


def test_execution_order_duplicate_raises():
    d = _minimal_program_dict()
    d["execution_order"] = ["inst_a", "inst_a"]
    with pytest.raises(ValueError, match="duplicate instance"):
        program_from_dict(d)


def test_execution_order_preserved_in_round_trip():
    prog = _make_small_program()
    reloaded = program_from_dict(program_to_dict(prog))
    assert reloaded.execution_order == ["inst_sensor", "inst_pid"]


# ---------------------------------------------------------------------------
# validate_program: wires
# ---------------------------------------------------------------------------


def test_validate_wire_unknown_src_raises():
    d = _minimal_program_dict()
    d["wires"] = [
        {
            "src_instance": "GHOST",
            "src_pin": "out",
            "dst_instance": "inst_a",
            "dst_pin": "in",
        }
    ]
    with pytest.raises(ValueError, match="src_instance"):
        program_from_dict(d)


def test_validate_wire_unknown_dst_raises():
    d = _minimal_program_dict()
    d["wires"] = [
        {
            "src_instance": "inst_a",
            "src_pin": "out",
            "dst_instance": "GHOST",
            "dst_pin": "in",
        }
    ]
    with pytest.raises(ValueError, match="dst_instance"):
        program_from_dict(d)


def test_validate_duplicate_dst_pin_raises():
    """Two wires to the same (dst_instance, dst_pin) are forbidden."""
    d = {
        "version": "1.0",
        "instances": {
            "src1": {"template_id": "t", "library": "builtin", "params": {}},
            "src2": {"template_id": "t", "library": "builtin", "params": {}},
            "dst": {"template_id": "t", "library": "builtin", "params": {}},
        },
        "wires": [
            {"src_instance": "src1", "src_pin": "out", "dst_instance": "dst", "dst_pin": "in"},
            {"src_instance": "src2", "src_pin": "out", "dst_instance": "dst", "dst_pin": "in"},
        ],
        "execution_order": ["src1", "src2", "dst"],
    }
    with pytest.raises(ValueError, match="multiple wires drive pin"):
        program_from_dict(d)


def test_fanout_from_same_source_is_valid():
    """Multiple wires from one source to different destinations are allowed."""
    d = {
        "version": "1.0",
        "instances": {
            "src": {"template_id": "t", "library": "builtin", "params": {}},
            "dst1": {"template_id": "t", "library": "builtin", "params": {}},
            "dst2": {"template_id": "t", "library": "builtin", "params": {}},
        },
        "wires": [
            {"src_instance": "src", "src_pin": "out", "dst_instance": "dst1", "dst_pin": "in"},
            {"src_instance": "src", "src_pin": "out", "dst_instance": "dst2", "dst_pin": "in"},
        ],
        "execution_order": ["src", "dst1", "dst2"],
    }
    prog = program_from_dict(d)
    assert len(prog.wires) == 2


# ---------------------------------------------------------------------------
# Validation errors: missing required fields
# ---------------------------------------------------------------------------


def test_instance_missing_template_id_raises():
    d = _minimal_program_dict()
    d["instances"]["inst_a"] = {"library": "user", "params": {}}
    with pytest.raises(ValueError, match="missing required key 'template_id'"):
        program_from_dict(d)


def test_instance_missing_library_raises():
    d = _minimal_program_dict()
    d["instances"]["inst_a"] = {"template_id": "pid", "params": {}}
    with pytest.raises(ValueError, match="missing required key 'library'"):
        program_from_dict(d)


def test_wire_missing_key_raises():
    d = _minimal_program_dict()
    d["wires"] = [{"src_instance": "inst_a", "src_pin": "out", "dst_instance": "inst_a"}]
    with pytest.raises(ValueError, match="missing required key 'dst_pin'"):
        program_from_dict(d)


def test_pin_missing_name_raises():
    d = {
        "version": "1.0",
        "user_templates": {
            "t": {
                "library": "user",
                "pins": [{"direction": "IN"}],
                "params": {},
            }
        },
        "instances": {},
        "wires": [],
        "execution_order": [],
    }
    with pytest.raises(ValueError, match="missing required key 'name'"):
        program_from_dict(d)


def test_pin_invalid_direction_raises():
    d = {
        "version": "1.0",
        "user_templates": {
            "t": {
                "library": "user",
                "pins": [{"name": "p", "direction": "SIDEWAYS"}],
                "params": {},
            }
        },
        "instances": {},
        "wires": [],
        "execution_order": [],
    }
    with pytest.raises(ValueError, match="invalid direction"):
        program_from_dict(d)


def test_program_data_not_mapping_raises():
    with pytest.raises(ValueError, match="must be a mapping"):
        program_from_dict("not a dict")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# user_templates round-trip and built-in not stored
# ---------------------------------------------------------------------------


def test_user_template_round_trips_pins_and_params():
    tmpl = _pid_template()
    prog = Program(user_templates={"pid": tmpl})
    d = program_to_dict(prog)
    assert "user_templates" in d
    reloaded = program_from_dict(d)
    rt = reloaded.user_templates["pid"]
    assert rt.template_id == "pid"
    assert rt.library == "user"
    assert rt.params["kp"] == pytest.approx(1.0)
    assert len(rt.pins) == 3
    assert rt.pins[0].name == "pv"
    assert rt.pins[0].direction == PinDirection.IN


def test_builtin_template_not_stored_in_program_dict():
    """Built-in templates are referenced by id only; program_to_dict must not embed them."""
    tmpl = _sensor_template(library="builtin")
    assert tmpl.is_builtin is True
    inst = place_block(tmpl, "inst_s")
    prog = Program(
        instances={"inst_s": inst},
        execution_order=["inst_s"],
    )
    d = program_to_dict(prog)
    assert "user_templates" not in d or not d.get("user_templates")
    # Instance still references the template by id
    assert d["instances"]["inst_s"]["template_id"] == "level_sensor"
    assert d["instances"]["inst_s"]["library"] == "builtin"


# ---------------------------------------------------------------------------
# TemplateLibrary seam
# ---------------------------------------------------------------------------


def test_template_library_register_and_get():
    lib = TemplateLibrary()
    tmpl = _pid_template(library="builtin", is_builtin=True)
    lib.register(tmpl)
    found = lib.get("builtin", "pid")
    assert found is tmpl


def test_template_library_get_missing_returns_none():
    lib = TemplateLibrary()
    assert lib.get("builtin", "nonexistent") is None


def test_template_library_all_templates():
    lib = TemplateLibrary()
    t1 = _pid_template(template_id="pid", library="builtin")
    t2 = _sensor_template(library="builtin")
    lib.register(t1)
    lib.register(t2)
    all_t = lib.all_templates()
    assert len(all_t) == 2
    assert t1 in all_t
    assert t2 in all_t


def test_template_library_register_overwrite():
    lib = TemplateLibrary()
    t_v1 = _pid_template()
    t_v2 = _pid_template()
    t_v2.params["kp"] = 99.0
    lib.register(t_v1)
    lib.register(t_v2)
    assert len(lib) == 1
    assert lib.get("user", "pid") is t_v2


def test_template_library_contains_operator():
    lib = TemplateLibrary()
    lib.register(_pid_template())
    assert ("user", "pid") in lib
    assert ("user", "missing") not in lib


def test_template_library_injectable_no_global_state():
    """Two independent TemplateLibrary instances share no state."""
    lib_a = TemplateLibrary()
    lib_b = TemplateLibrary()
    lib_a.register(_pid_template())
    assert lib_b.get("user", "pid") is None
    assert len(lib_a) == 1
    assert len(lib_b) == 0


# ---------------------------------------------------------------------------
# validate_program: direct API
# ---------------------------------------------------------------------------


def test_validate_program_clean_passes():
    prog = _make_small_program()
    validate_program(prog)  # must not raise


def test_validate_program_instance_key_mismatch_raises():
    inst = BlockInstance(
        instance_id="wrong_id",
        template_id="pid",
        library="user",
    )
    prog = Program(
        instances={"correct_key": inst},
        execution_order=[],
    )
    with pytest.raises(ValueError, match="does not match instance_id"):
        validate_program(prog)


def test_validate_program_empty_template_id_raises():
    inst = BlockInstance(instance_id="i1", template_id="", library="user")
    prog = Program(instances={"i1": inst}, execution_order=[])
    with pytest.raises(ValueError, match="empty template_id"):
        validate_program(prog)


def test_validate_program_empty_library_raises():
    inst = BlockInstance(instance_id="i1", template_id="pid", library="")
    prog = Program(instances={"i1": inst}, execution_order=[])
    with pytest.raises(ValueError, match="empty library"):
        validate_program(prog)


# ---------------------------------------------------------------------------
# canvas position round-trip
# ---------------------------------------------------------------------------


def test_canvas_position_omitted_when_zero():
    """x=0, y=0 positions are not included in the serialised dict."""
    tmpl = _pid_template()
    inst = place_block(tmpl, "i1")
    prog = Program(instances={"i1": inst}, execution_order=["i1"])
    d = program_to_dict(prog)
    assert "x" not in d["instances"]["i1"]
    assert "y" not in d["instances"]["i1"]


def test_canvas_position_serialised_when_nonzero():
    tmpl = _pid_template()
    inst = place_block(tmpl, "i1", x=42.0, y=7.5)
    prog = Program(instances={"i1": inst}, execution_order=["i1"])
    d = program_to_dict(prog)
    assert d["instances"]["i1"]["x"] == pytest.approx(42.0)
    assert d["instances"]["i1"]["y"] == pytest.approx(7.5)


# ---------------------------------------------------------------------------
# No HA / no external imports (smoke)
# ---------------------------------------------------------------------------


def test_no_ha_imports():
    """Surface package must not import Home Assistant modules."""
    import plcassistant.surface as surface_pkg

    src_modules = [
        surface_pkg.__name__,
        "plcassistant.surface.model",
        "plcassistant.surface.schema",
    ]
    import sys

    for mod_name in src_modules:
        mod = sys.modules.get(mod_name)
        if mod is None:
            continue
        for attr in dir(mod):
            assert "homeassistant" not in attr.lower(), (
                f"{mod_name} references homeassistant symbol: {attr}"
            )
