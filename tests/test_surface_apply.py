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
