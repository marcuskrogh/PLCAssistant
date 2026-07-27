"""Tests for block runtime (SWD-116).

Covers:
- execution_order is respected (blocks run in declared order)
- wire resolution: output of block A feeds input of block B
- tag I/O: unwired IN pins read from context; OUT pins written to context
- pin default fallback when context has no value for an unwired pin
- per-instance state persists across ticks
- fan-out: one source pin wired to multiple destinations
- user-body blocks (exec'd Python string)
- errors: dt < 0, unknown instance, template not found, unconnected no-default
- DictContext convenience wrapper
- safety constraint: runtime has no safety awareness
- no HA imports
"""

from __future__ import annotations

from typing import Any

import pytest

from plcassistant.surface.model import (
    BlockInstance,
    BlockTemplate,
    PinDirection,
    PinSpec,
    Program,
    TemplateLibrary,
    Wire,
)
from plcassistant.surface.runtime import (
    BlockRuntime,
    DictContext,
    make_runtime,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_library(*templates: BlockTemplate) -> TemplateLibrary:
    lib = TemplateLibrary()
    for t in templates:
        lib.register(t)
    return lib


def _make_passthrough_template(
    template_id: str = "passthrough",
    library: str = "builtin",
) -> BlockTemplate:
    """Template with one IN and one OUT pin; callable copies in→out."""
    return BlockTemplate(
        template_id=template_id,
        library=library,
        description="Copy in_val to out_val",
        pins=[
            PinSpec("in_val", PinDirection.IN, "float", 0.0),
            PinSpec("out_val", PinDirection.OUT, "float"),
        ],
        params={},
        is_builtin=True,
    )


def _register_passthrough(runtime: BlockRuntime, template: BlockTemplate) -> None:
    runtime.register_callable(
        template.library,
        template.template_id,
        lambda pins, _params, _state, _dt: {"out_val": pins["in_val"]},
    )


def _make_adder_template(library: str = "builtin") -> BlockTemplate:
    """Template: out = a + b."""
    return BlockTemplate(
        template_id="adder",
        library=library,
        description="out = a + b",
        pins=[
            PinSpec("a", PinDirection.IN, "float", 0.0),
            PinSpec("b", PinDirection.IN, "float", 0.0),
            PinSpec("out", PinDirection.OUT, "float"),
        ],
        params={},
        is_builtin=True,
    )


def _register_adder(runtime: BlockRuntime) -> None:
    runtime.register_callable(
        "builtin",
        "adder",
        lambda pins, _params, _state, _dt: {"out": pins["a"] + pins["b"]},
    )


def _make_counter_template(library: str = "builtin") -> BlockTemplate:
    """Template with persistent state: count increments each tick."""
    return BlockTemplate(
        template_id="counter",
        library=library,
        description="Increment counter each tick",
        pins=[
            PinSpec("count", PinDirection.OUT, "float"),
        ],
        params={},
        is_builtin=True,
    )


def _register_counter(runtime: BlockRuntime) -> None:
    def _fn(
        _pins: dict[str, Any],
        _params: dict[str, Any],
        state: dict,
        _dt: float,
    ) -> dict[str, Any]:
        state["n"] = state.get("n", 0) + 1
        return {"count": state["n"]}

    runtime.register_callable("builtin", "counter", _fn)


def _simple_program(
    instances: dict[str, BlockInstance],
    wires: list[Wire] | None = None,
    execution_order: list[str] | None = None,
) -> Program:
    return Program(
        instances=instances,
        wires=wires or [],
        execution_order=execution_order or list(instances.keys()),
    )


def _inst(instance_id: str, template_id: str, library: str = "builtin") -> BlockInstance:
    return BlockInstance(
        instance_id=instance_id,
        template_id=template_id,
        library=library,
        params={},
    )


# ---------------------------------------------------------------------------
# DictContext
# ---------------------------------------------------------------------------


def test_dict_context_get_missing_returns_none():
    ctx = DictContext()
    assert ctx.get("x") is None


def test_dict_context_set_and_get():
    ctx = DictContext({"a": 1.0})
    ctx.set("b", 2.0)
    assert ctx.get("a") == 1.0
    assert ctx.get("b") == 2.0


def test_dict_context_as_dict():
    ctx = DictContext({"x": 10})
    ctx.set("y", 20)
    d = ctx.as_dict()
    assert d == {"x": 10, "y": 20}


def test_dict_context_contains():
    ctx = DictContext({"a": 1})
    assert "a" in ctx
    assert "z" not in ctx


# ---------------------------------------------------------------------------
# Tag I/O: unwired IN reads from context; OUT written to context
# ---------------------------------------------------------------------------


def test_unwired_in_pin_reads_from_context():
    tmpl = _make_passthrough_template()
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    _register_passthrough(runtime, tmpl)

    ctx = DictContext({"inst1.in_val": 42.0})
    prog = _simple_program({"inst1": _inst("inst1", "passthrough")})
    runtime.tick(prog, ctx, 0.1)

    assert ctx.get("inst1.out_val") == pytest.approx(42.0)


def test_out_pin_written_to_context_with_convention():
    """OUT pins are always written as '{instance_id}.{pin_name}'."""
    tmpl = _make_passthrough_template()
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    _register_passthrough(runtime, tmpl)

    ctx = DictContext({"inst1.in_val": 7.5})
    prog = _simple_program({"inst1": _inst("inst1", "passthrough")})
    runtime.tick(prog, ctx, 0.1)

    assert "inst1.out_val" in ctx
    assert ctx["inst1.out_val"] == pytest.approx(7.5)


def test_pin_default_used_when_context_absent():
    """Unwired IN pin with default=1.0 uses default when context returns None."""
    tmpl = BlockTemplate(
        template_id="with_default",
        library="builtin",
        pins=[
            PinSpec("x", PinDirection.IN, "float", 99.0),
            PinSpec("y", PinDirection.OUT, "float"),
        ],
        params={},
        is_builtin=True,
    )
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    runtime.register_callable(
        "builtin", "with_default",
        lambda pins, _p, _s, _dt: {"y": pins["x"]},
    )
    ctx = DictContext()
    prog = _simple_program({"i1": _inst("i1", "with_default")})
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("i1.y") == pytest.approx(99.0)


# ---------------------------------------------------------------------------
# Wire resolution
# ---------------------------------------------------------------------------


def test_wire_routes_output_to_input():
    """Output of A feeds input of B via wire."""
    tmpl = _make_passthrough_template()
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    _register_passthrough(runtime, tmpl)

    ctx = DictContext({"A.in_val": 3.14})
    prog = Program(
        instances={
            "A": _inst("A", "passthrough"),
            "B": _inst("B", "passthrough"),
        },
        wires=[
            Wire(
                src_instance="A", src_pin="out_val",
                dst_instance="B", dst_pin="in_val",
            )
        ],
        execution_order=["A", "B"],
    )
    runtime.tick(prog, ctx, 0.1)

    assert ctx.get("B.out_val") == pytest.approx(3.14)
    assert ctx.get("A.out_val") == pytest.approx(3.14)


def test_wire_value_overrides_context_for_dst_pin():
    """Wired input ignores context tag for that pin."""
    tmpl = _make_passthrough_template()
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    _register_passthrough(runtime, tmpl)

    # Context has a value for B.in_val, but it should be overridden by the wire
    ctx = DictContext({"A.in_val": 5.0, "B.in_val": 999.0})
    prog = Program(
        instances={
            "A": _inst("A", "passthrough"),
            "B": _inst("B", "passthrough"),
        },
        wires=[
            Wire(
                src_instance="A", src_pin="out_val",
                dst_instance="B", dst_pin="in_val",
            )
        ],
        execution_order=["A", "B"],
    )
    runtime.tick(prog, ctx, 0.1)

    assert ctx.get("B.out_val") == pytest.approx(5.0)  # from wire, not 999


def test_fan_out_one_source_to_two_destinations():
    """Multiple wires from the same source pin reach both destinations."""
    tmpl = _make_passthrough_template()
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    _register_passthrough(runtime, tmpl)

    ctx = DictContext({"src.in_val": 7.0})
    prog = Program(
        instances={
            "src": _inst("src", "passthrough"),
            "dst1": _inst("dst1", "passthrough"),
            "dst2": _inst("dst2", "passthrough"),
        },
        wires=[
            Wire(src_instance="src", src_pin="out_val",
                 dst_instance="dst1", dst_pin="in_val"),
            Wire(src_instance="src", src_pin="out_val",
                 dst_instance="dst2", dst_pin="in_val"),
        ],
        execution_order=["src", "dst1", "dst2"],
    )
    runtime.tick(prog, ctx, 0.1)

    assert ctx.get("dst1.out_val") == pytest.approx(7.0)
    assert ctx.get("dst2.out_val") == pytest.approx(7.0)


# ---------------------------------------------------------------------------
# Execution order
# ---------------------------------------------------------------------------


def test_execution_order_determines_block_sequence():
    """Blocks execute strictly in execution_order; result depends on order."""
    adder_tmpl = _make_adder_template()
    lib = _make_library(adder_tmpl)
    runtime = make_runtime(lib)
    _register_adder(runtime)

    # Two adder instances sharing no wires; just verify order via side effects
    execution_sequence: list[str] = []

    def _adder_fn(pins, _params, _state, _dt):
        execution_sequence.append(_state.get("__id", "?"))
        return {"out": pins["a"] + pins["b"]}

    runtime.register_callable("builtin", "adder", _adder_fn)

    ctx = DictContext({"first.a": 1.0, "first.b": 2.0, "second.a": 3.0, "second.b": 4.0})

    inst_first = BlockInstance(
        instance_id="first", template_id="adder", library="builtin", params={}
    )
    inst_second = BlockInstance(
        instance_id="second", template_id="adder", library="builtin", params={}
    )

    # Patch state to carry id for tracking
    prog = Program(
        instances={"first": inst_first, "second": inst_second},
        wires=[],
        execution_order=["first", "second"],
    )
    runtime._state["first"] = {"__id": "first"}
    runtime._state["second"] = {"__id": "second"}

    runtime.tick(prog, ctx, 0.1)
    assert execution_sequence == ["first", "second"]


def test_execution_order_only_executes_listed_instances():
    """Instances not in execution_order are not executed."""
    tmpl = _make_passthrough_template()
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    called_ids: list[str] = []

    def _fn(pins, _p, state, _dt):
        called_ids.append(state.get("__id", "?"))
        return {"out_val": pins["in_val"]}

    runtime.register_callable("builtin", "passthrough", _fn)

    ctx = DictContext({"included.in_val": 1.0, "excluded.in_val": 2.0})
    prog = Program(
        instances={
            "included": _inst("included", "passthrough"),
            "excluded": _inst("excluded", "passthrough"),
        },
        wires=[],
        execution_order=["included"],  # excluded is not listed
    )
    runtime._state["included"] = {"__id": "included"}
    runtime._state["excluded"] = {"__id": "excluded"}

    runtime.tick(prog, ctx, 0.1)
    assert called_ids == ["included"]


# ---------------------------------------------------------------------------
# Per-instance state persistence
# ---------------------------------------------------------------------------


def test_state_persists_across_ticks():
    """Per-instance state dict is preserved between tick calls."""
    tmpl = _make_counter_template()
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    _register_counter(runtime)

    ctx = DictContext()
    prog = _simple_program({"c1": _inst("c1", "counter")})

    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("c1.count") == pytest.approx(1.0)

    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("c1.count") == pytest.approx(2.0)

    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("c1.count") == pytest.approx(3.0)


def test_reset_state_clears_single_instance():
    tmpl = _make_counter_template()
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    _register_counter(runtime)

    ctx = DictContext()
    prog = _simple_program({"c1": _inst("c1", "counter")})

    runtime.tick(prog, ctx, 0.1)
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("c1.count") == pytest.approx(2.0)

    runtime.reset_state("c1")
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("c1.count") == pytest.approx(1.0)


def test_reset_state_clears_all():
    tmpl = _make_counter_template()
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    _register_counter(runtime)

    ctx = DictContext()
    prog = _simple_program({"c1": _inst("c1", "counter"), "c2": _inst("c2", "counter")})

    runtime.tick(prog, ctx, 0.1)
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("c1.count") == pytest.approx(2.0)
    assert ctx.get("c2.count") == pytest.approx(2.0)

    runtime.reset_state()
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("c1.count") == pytest.approx(1.0)
    assert ctx.get("c2.count") == pytest.approx(1.0)


def test_two_instances_have_independent_state():
    """Same template; two instances maintain independent state dicts."""
    tmpl = _make_counter_template()
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    _register_counter(runtime)

    ctx = DictContext()
    prog = _simple_program({"c1": _inst("c1", "counter"), "c2": _inst("c2", "counter")})

    runtime.tick(prog, ctx, 0.1)
    runtime.reset_state("c2")  # only reset c2
    runtime.tick(prog, ctx, 0.1)

    # c1 has run 2 ticks, c2 only 1 after reset
    assert ctx.get("c1.count") == pytest.approx(2.0)
    assert ctx.get("c2.count") == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# User-body execution
# ---------------------------------------------------------------------------


def test_user_body_executes_and_writes_output():
    body = "result = x * 2"
    tmpl = BlockTemplate(
        template_id="doubler",
        library="user",
        description="double x",
        pins=[
            PinSpec("x", PinDirection.IN, "float", 0.0),
            PinSpec("result", PinDirection.OUT, "float"),
        ],
        params={},
        body=body,
    )
    lib = TemplateLibrary()
    runtime = BlockRuntime(lib)
    # user templates go in program.user_templates (not library)
    prog = Program(
        instances={"d": BlockInstance(
            instance_id="d", template_id="doubler", library="user", params={}
        )},
        wires=[],
        execution_order=["d"],
        user_templates={"doubler": tmpl},
    )
    ctx = DictContext({"d.x": 5.0})
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("d.result") == pytest.approx(10.0)


def test_user_body_can_use_params():
    body = "out = x * scale"
    tmpl = BlockTemplate(
        template_id="scaler",
        library="user",
        pins=[
            PinSpec("x", PinDirection.IN, "float", 0.0),
            PinSpec("out", PinDirection.OUT, "float"),
        ],
        params={"scale": 3.0},
        body=body,
    )
    lib = TemplateLibrary()
    runtime = BlockRuntime(lib)
    inst = BlockInstance(
        instance_id="s1", template_id="scaler", library="user",
        params={"scale": 5.0},  # override
    )
    prog = Program(
        instances={"s1": inst},
        wires=[],
        execution_order=["s1"],
        user_templates={"scaler": tmpl},
    )
    ctx = DictContext({"s1.x": 4.0})
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("s1.out") == pytest.approx(20.0)  # 4 * 5


def test_user_body_can_accumulate_state():
    body = "state['n'] = state.get('n', 0) + 1\nout = state['n']"
    tmpl = BlockTemplate(
        template_id="stateful",
        library="user",
        pins=[PinSpec("out", PinDirection.OUT, "float")],
        params={},
        body=body,
    )
    lib = TemplateLibrary()
    runtime = BlockRuntime(lib)
    prog = Program(
        instances={"s": BlockInstance(
            instance_id="s", template_id="stateful", library="user", params={}
        )},
        wires=[],
        execution_order=["s"],
        user_templates={"stateful": tmpl},
    )
    ctx = DictContext()
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("s.out") == pytest.approx(1.0)
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("s.out") == pytest.approx(2.0)


def test_user_body_out_pin_defaults_when_not_set():
    """If body doesn't set an OUT pin, the pin's default is used."""
    tmpl = BlockTemplate(
        template_id="noop",
        library="user",
        pins=[PinSpec("out", PinDirection.OUT, "float", default=99.0)],
        params={},
        body="pass",  # does not set 'out'
    )
    lib = TemplateLibrary()
    runtime = BlockRuntime(lib)
    prog = Program(
        instances={"n": BlockInstance(
            instance_id="n", template_id="noop", library="user", params={}
        )},
        wires=[],
        execution_order=["n"],
        user_templates={"noop": tmpl},
    )
    ctx = DictContext()
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("n.out") == pytest.approx(99.0)


# ---------------------------------------------------------------------------
# Params: instance params passed to callable
# ---------------------------------------------------------------------------


def test_instance_params_passed_to_callable():
    tmpl = BlockTemplate(
        template_id="gain_block",
        library="builtin",
        pins=[
            PinSpec("x", PinDirection.IN, "float", 0.0),
            PinSpec("y", PinDirection.OUT, "float"),
        ],
        params={"gain": 1.0},
        is_builtin=True,
    )
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    runtime.register_callable(
        "builtin", "gain_block",
        lambda pins, params, _s, _dt: {"y": pins["x"] * params["gain"]},
    )
    inst = BlockInstance(
        instance_id="g1", template_id="gain_block", library="builtin",
        params={"gain": 3.0},
    )
    prog = _simple_program({"g1": inst})
    ctx = DictContext({"g1.x": 4.0})
    runtime.tick(prog, ctx, 0.1)
    assert ctx.get("g1.y") == pytest.approx(12.0)  # 4 * 3


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_tick_negative_dt_raises():
    runtime = BlockRuntime(TemplateLibrary())
    prog = Program()
    ctx = DictContext()
    with pytest.raises(ValueError, match="dt must be non-negative"):
        runtime.tick(prog, ctx, -0.1)


def test_tick_unknown_instance_in_execution_order_raises():
    tmpl = _make_passthrough_template()
    runtime = BlockRuntime(_make_library(tmpl))
    _register_passthrough(runtime, tmpl)

    prog = Program(
        instances={"real_inst": _inst("real_inst", "passthrough")},
        wires=[],
        execution_order=["real_inst", "ghost_inst"],
    )
    ctx = DictContext()
    with pytest.raises(ValueError, match="unknown instance"):
        runtime.tick(prog, ctx, 0.1)


def test_tick_template_not_in_library_raises():
    runtime = BlockRuntime(TemplateLibrary())
    prog = Program(
        instances={"i": _inst("i", "missing_template")},
        wires=[],
        execution_order=["i"],
    )
    ctx = DictContext()
    with pytest.raises(ValueError, match="not found in library"):
        runtime.tick(prog, ctx, 0.1)


def test_tick_unconnected_pin_no_default_raises():
    tmpl = BlockTemplate(
        template_id="strict",
        library="builtin",
        pins=[
            PinSpec("required_in", PinDirection.IN, "float", None),  # no default
            PinSpec("out", PinDirection.OUT, "float"),
        ],
        params={},
        is_builtin=True,
    )
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    runtime.register_callable(
        "builtin", "strict",
        lambda pins, _p, _s, _dt: {"out": pins["required_in"]},
    )
    prog = _simple_program({"i": _inst("i", "strict")})
    ctx = DictContext()  # no value for i.required_in
    with pytest.raises(ValueError, match="unconnected and has no default"):
        runtime.tick(prog, ctx, 0.1)


def test_tick_no_callable_no_body_raises():
    tmpl = BlockTemplate(
        template_id="empty",
        library="builtin",
        pins=[PinSpec("x", PinDirection.OUT, "float")],
        params={},
        body="",  # no body
        is_builtin=True,
    )
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    # No callable registered for this template
    prog = _simple_program({"i": _inst("i", "empty")})
    ctx = DictContext()
    with pytest.raises(ValueError, match="no callable registered"):
        runtime.tick(prog, ctx, 0.1)


# ---------------------------------------------------------------------------
# make_runtime convenience factory
# ---------------------------------------------------------------------------


def test_make_runtime_returns_block_runtime():
    lib = TemplateLibrary()
    runtime = make_runtime(lib)
    assert isinstance(runtime, BlockRuntime)


# ---------------------------------------------------------------------------
# dt=0 is valid (holds state)
# ---------------------------------------------------------------------------


def test_dt_zero_is_valid():
    tmpl = _make_passthrough_template()
    lib = _make_library(tmpl)
    runtime = make_runtime(lib)
    _register_passthrough(runtime, tmpl)
    ctx = DictContext({"i.in_val": 1.0})
    prog = _simple_program({"i": _inst("i", "passthrough")})
    runtime.tick(prog, ctx, 0.0)  # must not raise
    assert ctx.get("i.out_val") == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Safety awareness: runtime has no safety-specific logic
# ---------------------------------------------------------------------------


def test_runtime_has_no_safety_awareness():
    """Verify BlockRuntime has no safety-related attributes or methods."""
    runtime = BlockRuntime(TemplateLibrary())
    safety_attrs = [a for a in dir(runtime) if "safe" in a.lower() or "trip" in a.lower()]
    assert safety_attrs == [], (
        f"BlockRuntime must not have safety attributes: {safety_attrs}"
    )


# ---------------------------------------------------------------------------
# No HA imports
# ---------------------------------------------------------------------------


def test_no_ha_imports_in_runtime():
    import sys

    mod = sys.modules.get("plcassistant.surface.runtime")
    if mod is not None:
        for attr in dir(mod):
            assert "homeassistant" not in attr.lower(), (
                f"runtime module references homeassistant symbol: {attr}"
            )


# ---------------------------------------------------------------------------
# Review findings — Finding 2: sandboxed user-body exec
# ---------------------------------------------------------------------------


def _make_body_template(body: str, tid: str = "t") -> BlockTemplate:
    return BlockTemplate(
        template_id=tid,
        library="user",
        pins=[PinSpec("out", PinDirection.OUT, "float", default=0.0)],
        params={},
        body=body,
    )


def _run_body(body: str) -> DictContext:
    """Execute *body* via the runtime and return the context."""
    tmpl = _make_body_template(body)
    lib = TemplateLibrary()
    rt = BlockRuntime(lib)
    prog = Program(
        instances={"t": BlockInstance(instance_id="t", template_id="t", library="user", params={})},
        wires=[],
        execution_order=["t"],
        user_templates={"t": tmpl},
    )
    ctx = DictContext()
    rt.tick(prog, ctx, 0.1)
    return ctx


def test_sandbox_import_denied():
    """__import__ must not be available inside user block bodies."""
    with pytest.raises((NameError, ImportError)):
        _run_body("__import__('os')")


def test_sandbox_open_denied():
    """open() must not be available inside user block bodies."""
    with pytest.raises(NameError):
        _run_body("open('/etc/passwd')")


def test_sandbox_eval_denied():
    """eval() must not be available inside user block bodies."""
    with pytest.raises(NameError):
        _run_body("eval('1+1')")


def test_sandbox_exec_denied():
    """exec() must not be available inside user block bodies."""
    with pytest.raises(NameError):
        _run_body("exec('pass')")


def test_sandbox_safe_math_abs():
    """abs() is allowed in user bodies."""
    ctx = _run_body("out = abs(-7.0)")
    assert ctx.get("t.out") == pytest.approx(7.0)


def test_sandbox_safe_math_module():
    """math module is available in user bodies (math.sqrt etc.)."""
    ctx = _run_body("out = math.sqrt(9.0)")
    assert ctx.get("t.out") == pytest.approx(3.0)


def test_sandbox_safe_min_max():
    """min/max are allowed in user bodies."""
    ctx = _run_body("out = max(1.0, min(5.0, 3.0))")
    assert ctx.get("t.out") == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Review findings — Finding 4: reverse-wire-order raises
# ---------------------------------------------------------------------------


def test_wire_reverse_order_raises():
    """Source must run before destination; wrong execution_order raises ValueError."""
    tmpl = _make_passthrough_template()
    lib = _make_library(tmpl)
    rt = make_runtime(lib)
    _register_passthrough(rt, tmpl)

    # Wire B.out_val → A.in_val, but execution_order puts A before B.
    # When A runs it tries to read B.out_val which hasn't been computed yet.
    prog = Program(
        instances={
            "A": _inst("A", "passthrough"),
            "B": _inst("B", "passthrough"),
        },
        wires=[
            Wire(src_instance="B", src_pin="out_val",
                 dst_instance="A", dst_pin="in_val"),
        ],
        execution_order=["A", "B"],  # A before B — wrong order
    )
    ctx = DictContext({"B.in_val": 1.0})
    with pytest.raises(ValueError, match="not been computed yet"):
        rt.tick(prog, ctx, 0.1)
