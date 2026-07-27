"""Tests for apply policy (SWD-117).

Covers:
- ProgramLoader.load / restart_apply: loads program, clears runtime state
- ProgramLoader.hot_apply: swaps program without clearing state when authorised
- hot_apply PermissionError when neither superuser=True nor env var set
- hot_apply allowed via PLCASSISTANT_SUPERUSER_HOT_APPLY=1 env var
- loader.program property before and after load
- user templates registered into library on load
"""

from __future__ import annotations

import os

import pytest

from plcassistant.surface.apply import ProgramLoader
from plcassistant.surface.builtin import register_builtins
from plcassistant.surface.model import (
    BlockInstance,
    BlockTemplate,
    PinDirection,
    PinSpec,
    Program,
    TemplateLibrary,
)
from plcassistant.surface.runtime import BlockRuntime, DictContext
from plcassistant.surface.schema import program_from_dict
from plcassistant.surface.user_library import add_user_template, make_user_template


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_loader() -> tuple[ProgramLoader, TemplateLibrary, BlockRuntime]:
    lib = TemplateLibrary()
    rt = BlockRuntime(lib)
    register_builtins(lib, rt)
    loader = ProgramLoader(lib, rt)
    return loader, lib, rt


def _empty_prog() -> Program:
    return program_from_dict({"version": "1.0", "instances": {}, "wires": [], "execution_order": []})


def _counter_program() -> tuple[Program, BlockTemplate]:
    """Program with one user counter block; returns (program, template)."""
    tmpl = make_user_template(
        "counter",
        body="state['n'] = state.get('n', 0) + 1\nout = state['n']",
        pins=[{"name": "out", "direction": "OUT", "data_type": "float"}],
    )
    prog = Program(
        instances={"c1": BlockInstance(
            instance_id="c1", template_id="counter", library="user", params={}
        )},
        wires=[],
        execution_order=["c1"],
    )
    add_user_template(prog, tmpl)
    return prog, tmpl


# ---------------------------------------------------------------------------
# program property before load
# ---------------------------------------------------------------------------


def test_loader_program_none_before_load():
    loader, _, _ = _make_loader()
    assert loader.program is None


# ---------------------------------------------------------------------------
# load / restart_apply
# ---------------------------------------------------------------------------


def test_load_sets_program():
    loader, _, _ = _make_loader()
    prog = _empty_prog()
    loader.load(prog)
    assert loader.program is prog


def test_restart_apply_sets_program():
    loader, _, _ = _make_loader()
    prog = _empty_prog()
    loader.restart_apply(prog)
    assert loader.program is prog


def test_load_clears_runtime_state():
    loader, lib, rt = _make_loader()
    # Manually inject state
    rt._state["c1"] = {"n": 5}
    loader.load(_empty_prog())
    assert rt._state == {}


def test_restart_apply_clears_runtime_state():
    loader, lib, rt = _make_loader()
    rt._state["c1"] = {"n": 3}
    loader.restart_apply(_empty_prog())
    assert rt._state == {}


def test_load_registers_user_templates_into_library():
    loader, lib, rt = _make_loader()
    prog, tmpl = _counter_program()
    loader.load(prog)
    assert lib.get("user", "counter") is not None


def test_load_runs_user_body_after_registration():
    loader, lib, rt = _make_loader()
    prog, _ = _counter_program()
    loader.load(prog)
    ctx = DictContext()
    rt.tick(loader.program, ctx, 0.1)
    assert ctx.get("c1.out") == pytest.approx(1.0)
    rt.tick(loader.program, ctx, 0.1)
    assert ctx.get("c1.out") == pytest.approx(2.0)


def test_restart_apply_resets_state_between_programs():
    """After restart_apply the counter resets because state is cleared."""
    loader, lib, rt = _make_loader()
    prog, _ = _counter_program()
    loader.load(prog)
    ctx = DictContext()
    rt.tick(loader.program, ctx, 0.1)
    rt.tick(loader.program, ctx, 0.1)
    assert ctx.get("c1.out") == pytest.approx(2.0)

    # restart_apply with the same program — state must reset
    prog2, _ = _counter_program()
    loader.restart_apply(prog2)
    ctx2 = DictContext()
    rt.tick(loader.program, ctx2, 0.1)
    assert ctx2.get("c1.out") == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# hot_apply: permission checks
# ---------------------------------------------------------------------------


def test_hot_apply_denied_without_superuser(monkeypatch):
    """hot_apply raises PermissionError when superuser=False and env var not set."""
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    loader, _, _ = _make_loader()
    loader.load(_empty_prog())
    with pytest.raises(PermissionError, match="superuser authorisation"):
        loader.hot_apply(_empty_prog(), superuser=False)


def test_hot_apply_allowed_with_superuser_flag(monkeypatch):
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    loader, _, _ = _make_loader()
    loader.load(_empty_prog())
    prog2 = _empty_prog()
    loader.hot_apply(prog2, superuser=True)  # must not raise
    assert loader.program is prog2


def test_hot_apply_allowed_via_env_var(monkeypatch):
    monkeypatch.setenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", "1")
    loader, _, _ = _make_loader()
    loader.load(_empty_prog())
    prog2 = _empty_prog()
    loader.hot_apply(prog2, superuser=False)  # env var grants authority
    assert loader.program is prog2


def test_hot_apply_env_var_value_must_be_one(monkeypatch):
    """Only the value '1' grants authority; other values are rejected."""
    for val in ("0", "true", "yes", "on", " 1 "):
        monkeypatch.setenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", val)
        loader, _, _ = _make_loader()
        loader.load(_empty_prog())
        with pytest.raises(PermissionError):
            loader.hot_apply(_empty_prog(), superuser=False)


# ---------------------------------------------------------------------------
# hot_apply: state preservation
# ---------------------------------------------------------------------------


def test_hot_apply_preserves_runtime_state(monkeypatch):
    """hot_apply does NOT clear runtime state."""
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    loader, lib, rt = _make_loader()
    prog, _ = _counter_program()
    loader.load(prog)
    ctx = DictContext()
    rt.tick(loader.program, ctx, 0.1)
    rt.tick(loader.program, ctx, 0.1)
    assert ctx.get("c1.out") == pytest.approx(2.0)

    # hot_apply with same program structure — state must be preserved
    prog2, _ = _counter_program()
    loader.hot_apply(prog2, superuser=True)
    rt.tick(loader.program, ctx, 0.1)
    # Counter continues from 3, not restarted
    assert ctx.get("c1.out") == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# runtime property
# ---------------------------------------------------------------------------


def test_loader_runtime_property():
    loader, lib, rt = _make_loader()
    assert loader.runtime is rt


# ---------------------------------------------------------------------------
# Review findings — Finding 5: prune stale user templates on load/hot_apply
# ---------------------------------------------------------------------------


def _template_prog(tid: str) -> tuple[Program, BlockTemplate]:
    """Return a program containing one user template with *tid*."""
    tmpl = make_user_template(
        tid,
        body="out = 0.0",
        pins=[{"name": "out", "direction": "OUT", "data_type": "float"}],
    )
    prog = Program(
        instances={},
        wires=[],
        execution_order=[],
    )
    add_user_template(prog, tmpl)
    return prog, tmpl


def test_prune_removes_stale_user_template_on_load():
    """load() removes library entries for templates absent from the new program."""
    loader, lib, rt = _make_loader()
    prog1, _ = _template_prog("old_t")
    loader.load(prog1)
    assert lib.get("user", "old_t") is not None

    # Load a new program that does NOT include "old_t".
    prog2 = _empty_prog()
    loader.load(prog2)
    assert lib.get("user", "old_t") is None, (
        "load() must prune stale user templates from the library"
    )


def test_prune_removes_stale_user_template_on_hot_apply(monkeypatch):
    """hot_apply() removes library entries for templates absent from the new program."""
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    loader, lib, rt = _make_loader()
    prog1, _ = _template_prog("old_t")
    loader.load(prog1)
    assert lib.get("user", "old_t") is not None

    prog2 = _empty_prog()
    loader.hot_apply(prog2, superuser=True)
    assert lib.get("user", "old_t") is None, (
        "hot_apply() must prune stale user templates from the library"
    )


def test_prune_keeps_templates_in_new_program():
    """Templates present in the new program are not pruned."""
    loader, lib, rt = _make_loader()
    prog1, _ = _template_prog("keep_me")
    loader.load(prog1)

    prog2, _ = _template_prog("keep_me")
    loader.load(prog2)
    assert lib.get("user", "keep_me") is not None, (
        "Templates still in the new program must remain registered"
    )


def test_template_library_unregister():
    """TemplateLibrary.unregister() removes a template; no-op if absent."""
    from plcassistant.surface.model import TemplateLibrary, BlockTemplate

    lib = TemplateLibrary()
    tmpl = BlockTemplate(template_id="t", library="user")
    lib.register(tmpl)
    assert lib.get("user", "t") is not None

    lib.unregister("user", "t")
    assert lib.get("user", "t") is None

    # Second call must be a no-op.
    lib.unregister("user", "t")  # must not raise


# ---------------------------------------------------------------------------
# Review findings — Finding 7: hot-apply state pruning
# ---------------------------------------------------------------------------


def test_hot_apply_drops_state_for_removed_instance(monkeypatch):
    """hot_apply() drops runtime state for instances not in the new program."""
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    loader, lib, rt = _make_loader()
    prog, _ = _counter_program()
    loader.load(prog)
    ctx = DictContext()
    rt.tick(loader.program, ctx, 0.1)
    rt.tick(loader.program, ctx, 0.1)
    assert "c1" in rt.state

    # New program has no "c1" instance.
    prog2 = _empty_prog()
    loader.hot_apply(prog2, superuser=True)
    assert "c1" not in rt.state, (
        "hot_apply must drop state for instances removed from the new program"
    )


def test_hot_apply_resets_state_on_template_id_change(monkeypatch):
    """hot_apply() resets state when an instance switches template_id."""
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    loader, lib, rt = _make_loader()
    prog, _ = _counter_program()
    loader.load(prog)
    ctx = DictContext()
    rt.tick(loader.program, ctx, 0.1)
    rt.tick(loader.program, ctx, 0.1)
    assert rt.state.get("c1", {}).get("n", 0) == 2

    # New program keeps "c1" but with a different template_id.
    new_tmpl = make_user_template(
        "counter_v2",
        body="state['n'] = state.get('n', 0) + 10\nout = state['n']",
        pins=[{"name": "out", "direction": "OUT", "data_type": "float"}],
    )
    from plcassistant.surface.model import BlockInstance, Program
    prog2 = Program(
        instances={"c1": BlockInstance(
            instance_id="c1", template_id="counter_v2", library="user", params={}
        )},
        wires=[],
        execution_order=["c1"],
    )
    add_user_template(prog2, new_tmpl)
    loader.hot_apply(prog2, superuser=True)
    # State for c1 must have been reset (template changed).
    assert rt.state.get("c1", {}).get("n", 0) == 0, (
        "hot_apply must reset state when template_id changes for same instance_id"
    )


def test_hot_apply_resets_state_on_library_change(monkeypatch):
    """hot_apply() resets state when an instance switches library (same template_id)."""
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    loader, lib, rt = _make_loader()
    prog, _ = _counter_program()
    loader.load(prog)
    ctx = DictContext()
    rt.tick(loader.program, ctx, 0.1)
    rt.tick(loader.program, ctx, 0.1)
    assert rt.state.get("c1", {}).get("n", 0) == 2

    # Same template_id string, different library namespace.
    other = make_user_template(
        "counter",
        body="state['n'] = state.get('n', 0) + 1\nout = state['n']",
        library="user_alt",
        pins=[{"name": "out", "direction": "OUT", "data_type": "float"}],
    )
    from plcassistant.surface.model import BlockInstance, Program
    prog2 = Program(
        instances={"c1": BlockInstance(
            instance_id="c1", template_id="counter", library="user_alt", params={}
        )},
        wires=[],
        execution_order=["c1"],
    )
    add_user_template(prog2, other)
    loader.hot_apply(prog2, superuser=True)
    assert rt.state.get("c1", {}).get("n", 0) == 0, (
        "hot_apply must reset state when library changes for same instance_id"
    )


def test_on_apply_hook_fires_on_load():
    """add_on_apply_hook callback is invoked with is_restart=True on load."""
    loader, lib, rt = _make_loader()
    calls: list[bool] = []
    loader.add_on_apply_hook(lambda is_restart: calls.append(is_restart))
    loader.load(_empty_prog())
    assert calls == [True]


def test_on_apply_hook_fires_on_hot_apply(monkeypatch):
    """add_on_apply_hook callback is invoked with is_restart=False on hot_apply."""
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    loader, lib, rt = _make_loader()
    loader.load(_empty_prog())
    calls: list[bool] = []
    loader.add_on_apply_hook(lambda is_restart: calls.append(is_restart))
    loader.hot_apply(_empty_prog(), superuser=True)
    assert calls == [False]
