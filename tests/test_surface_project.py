"""Unit tests for Soft-PLC project organization (SWD-182)."""

from __future__ import annotations

import copy

import pytest

from plcassistant.surface.apply import ProjectLoader
from plcassistant.surface.builtin import register_builtins, wedge_cascade_program, wedge_softplc_project
from plcassistant.surface.model import MAIN_TASK_ID, Program, SoftPlcProject, Task, TemplateLibrary
from plcassistant.surface.runtime import BlockRuntime, DictContext
from plcassistant.surface.schema import (
    classify_project_apply,
    is_legacy_program_dict,
    main_program,
    migrate_legacy_program_dict,
    program_from_dict,
    project_from_dict,
    project_to_dict,
    scheduled_programs,
    validate_project,
)


def _make_loader() -> tuple[ProjectLoader, BlockRuntime]:
    lib = TemplateLibrary()
    rt = BlockRuntime(lib)
    register_builtins(lib, rt)
    return ProjectLoader(lib, rt), rt


def test_is_legacy_program_dict():
    flat = wedge_cascade_program()
    assert is_legacy_program_dict(flat) is True
    project = wedge_softplc_project()
    assert is_legacy_program_dict(project) is False


def test_migrate_legacy_wraps_main_task():
    flat = wedge_cascade_program()
    wrapped = migrate_legacy_program_dict(flat)
    proj = project_from_dict(wrapped)
    assert proj.version == "2.0"
    assert "main" in proj.programs
    assert len(proj.tasks) == 1
    assert proj.tasks[0].task_id == MAIN_TASK_ID
    assert proj.tasks[0].programs == ["main"]


def test_project_from_dict_auto_migrates_legacy():
    flat = wedge_cascade_program()
    proj = project_from_dict(flat)
    assert main_program(proj) is not None
    assert "level_pi" in main_program(proj).instances  # type: ignore[union-attr]


def test_validate_rejects_program_on_two_tasks():
    prog = program_from_dict(wedge_cascade_program())
    project = SoftPlcProject(
        programs={"tank": prog},
        tasks=[
            Task("t1", 1, ["tank"]),
            Task("t2", 2, ["tank"]),
        ],
    )
    with pytest.raises(ValueError, match="scheduled on tasks"):
        validate_project(project)


def test_validate_rejects_unknown_program_reference():
    project = SoftPlcProject(
        programs={},
        tasks=[Task("main", 1, ["missing"])],
    )
    with pytest.raises(ValueError, match="unknown program"):
        validate_project(project)


def test_scheduled_programs_priority_order():
    p1 = program_from_dict({"version": "1.0", "instances": {}, "wires": [], "execution_order": []})
    p2 = program_from_dict({"version": "1.0", "instances": {}, "wires": [], "execution_order": []})
    project = SoftPlcProject(
        programs={"low": p1, "high": p2},
        tasks=[
            Task("slow", 10, ["low"]),
            Task("fast", 1, ["high"]),
        ],
    )
    order = [pid for _t, pid, _p in scheduled_programs(project)]
    assert order == ["high", "low"]


def test_unscheduled_program_not_in_schedule():
    prog = program_from_dict(wedge_cascade_program())
    orphan = program_from_dict({"version": "1.0", "instances": {}, "wires": [], "execution_order": []})
    project = SoftPlcProject(
        programs={"tank": prog, "orphan": orphan},
        tasks=[Task("main", 1, ["tank"])],
    )
    scheduled_ids = {pid for _t, pid, _p in scheduled_programs(project)}
    assert scheduled_ids == {"tank"}
    assert "orphan" not in scheduled_ids


def test_classify_hot_for_param_change_only():
    base = project_from_dict(wedge_softplc_project())
    tweaked = copy.deepcopy(project_to_dict(base))
    tweaked["programs"]["tank"]["instances"]["level_pi"]["params"]["kp"] = 41.0
    new_proj = project_from_dict(tweaked)
    assert classify_project_apply(base, new_proj) == "hot"


def test_classify_restart_for_task_structure_change():
    base = project_from_dict(wedge_softplc_project())
    extra = copy.deepcopy(project_to_dict(base))
    extra["tasks"].append({"id": "aux", "priority": 5, "programs": []})
    new_proj = project_from_dict(extra)
    assert classify_project_apply(base, new_proj) == "restart"


def test_classify_restart_for_program_membership_change():
    base = project_from_dict(wedge_softplc_project())
    moved = copy.deepcopy(project_to_dict(base))
    moved["tasks"][0]["programs"] = []
    new_proj = project_from_dict(moved)
    assert classify_project_apply(base, new_proj) == "restart"


def test_project_loader_tick_runs_scheduled(monkeypatch):
    loader, rt = _make_loader()
    proj = project_from_dict(wedge_softplc_project())
    loader.load(proj)
    ctx = DictContext()
    ctx["level_pi.pv"] = 0.15
    ctx["level_pi.sp"] = 0.20
    ctx["level_pi.running"] = True
    ctx["flow_pi.pv"] = 0.0
    ctx["flow_pi.running"] = True
    loader.tick(ctx, 0.1)
    assert ctx.get("level_pi.cv") is not None


def test_hot_apply_rejects_structure_change(monkeypatch):
    monkeypatch.delenv("PLCASSISTANT_SUPERUSER_HOT_APPLY", raising=False)
    loader, _rt = _make_loader()
    base = project_from_dict(wedge_softplc_project())
    loader.load(base)
    extra = copy.deepcopy(project_to_dict(base))
    extra["tasks"].append({"id": "aux", "priority": 2, "programs": []})
    with pytest.raises(ValueError, match="structure changed"):
        loader.hot_apply(project_from_dict(extra), superuser=True)


def test_project_round_trip():
    raw = wedge_softplc_project()
    proj = project_from_dict(raw)
    again = project_from_dict(project_to_dict(proj))
    assert project_to_dict(again) == project_to_dict(proj)
