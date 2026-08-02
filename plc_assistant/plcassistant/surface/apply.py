"""Apply policy for block programs (SWD-117) and Soft-PLC projects (SWD-182).

``ProgramLoader`` holds the active Program and BlockRuntime.  ``ProjectLoader``
extends that model to a Soft-PLC project (Tasks → Programs) with priority-ordered
scan passes and structure vs logic apply classification.

restart_apply (default)
    Swap the program **and** clear all runtime state (integrals, flags, cached
    outputs).  Always safe.  Equivalent to a process restart: the new program
    starts from a clean slate on the next tick.

hot_apply (superuser only)
    Swap the program without clearing runtime state.  Useful during
    development to apply incremental changes without losing controller
    wind-up.  Requires *superuser* authorisation (see below).

Project structure (Tasks, program membership) always requires ``restart_apply``.
Program logic/params within unchanged structure may use ``hot_apply``.

Superuser authorisation
-----------------------
``hot_apply`` is gated on the environment variable
``PLCASSISTANT_SUPERUSER_HOT_APPLY=1`` (read at runtime) **or** a server-side
flag set at ``AppState`` construction time.  The client-supplied ``superuser``
body field is **ignored** by the HTTP server — only server-side config grants
authority.

If neither condition is met ``hot_apply`` raises ``PermissionError``.

On-apply hooks
--------------
Callers can register callbacks via ``add_on_apply_hook`` to be notified
whenever the active program changes.  The scan context (e.g. ``DictContext``)
should be cleared on every apply to avoid stale pin values from a previous
program run.

No Home Assistant dependency; no hard-wired I/O.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Callable

from plcassistant.surface.model import Program, SoftPlcProject, TemplateLibrary
from plcassistant.surface.runtime import BlockRuntime
from plcassistant.surface.schema import (
    classify_project_apply,
    main_program,
    migrate_legacy_program_dict,
    migrate_program_to_pid,
    program_to_dict,
    project_from_dict,
    scheduled_programs,
)
from plcassistant.surface.user_library import register_user_templates

if TYPE_CHECKING:
    pass


_ENV_HOT_APPLY = "PLCASSISTANT_SUPERUSER_HOT_APPLY"


class ProgramLoader:
    """Hold and manage the active Program + BlockRuntime.

    Typical usage::

        library = TemplateLibrary()
        runtime = BlockRuntime(library)
        register_builtins(library, runtime)

        loader = ProgramLoader(library, runtime)
        loader.load(program_from_dict(yaml_dict))

        # inside on_control:
        runtime.tick(loader.program, context, dt)

    Hot-apply (development only)::

        # Set PLCASSISTANT_SUPERUSER_HOT_APPLY=1 in the environment
        loader.hot_apply(new_program)
        # or pass superuser=True for trusted server-side callers
        loader.hot_apply(new_program, superuser=True)
    """

    def __init__(self, library: TemplateLibrary, runtime: BlockRuntime) -> None:
        self._library = library
        self._runtime = runtime
        self._program: Program | None = None
        # Callbacks: fn(is_restart: bool) invoked on every apply.
        self._on_apply_hooks: list[Callable[[bool], None]] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def program(self) -> Program | None:
        """Currently active ``Program``, or ``None`` before first load."""
        return self._program

    @property
    def runtime(self) -> BlockRuntime:
        """The ``BlockRuntime`` managed by this loader."""
        return self._runtime

    # ------------------------------------------------------------------
    # Hook registration
    # ------------------------------------------------------------------

    def add_on_apply_hook(self, fn: Callable[[bool], None]) -> None:
        """Register *fn* to be called after each apply.

        ``fn(is_restart)`` is invoked with ``is_restart=True`` for
        ``load``/``restart_apply`` and ``False`` for ``hot_apply``.  Callers
        use this to clear scan context and reset transient flags.
        """
        self._on_apply_hooks.append(fn)

    def _fire_hooks(self, is_restart: bool) -> None:
        for fn in self._on_apply_hooks:
            fn(is_restart)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, program: Program) -> None:
        """Load *program* as the active program.

        Clears all runtime state (restart semantics).  Equivalent to
        ``restart_apply``.  User templates from *program* are registered into
        the ``TemplateLibrary`` so the runtime can resolve them.  Stale user
        templates no longer in *program* are pruned from the library.
        """
        self._prune_user_templates(program)
        register_user_templates(self._library, program)
        self._runtime.reset_state()
        self._program = program
        self._fire_hooks(is_restart=True)

    def restart_apply(self, program: Program) -> None:
        """Apply *program* via restart semantics (default apply path).

        Clears all runtime state before activating the new program.  The next
        ``runtime.tick()`` starts with a clean state (integrals reset,
        bumpless flags cleared).
        """
        self.load(program)

    def hot_apply(self, program: Program, *, superuser: bool = False) -> None:
        """Apply *program* without clearing runtime state.

        Preserves per-instance state (integrals, flags, cached outputs) so
        that the controller continues bumplessly after the program is swapped.
        State entries for instances that no longer exist in *program* are
        pruned; state for instances whose ``template_id`` changed is reset.

        Authorisation
        ~~~~~~~~~~~~~
        Requires *one* of:

        * ``superuser=True`` (server-side assertion of authority), **or**
        * ``PLCASSISTANT_SUPERUSER_HOT_APPLY=1`` set in the environment.

        The HTTP server **ignores** any ``superuser`` field in the request
        body — only server-side config grants authority.

        Raises ``PermissionError`` when neither condition holds.
        """
        if not self._is_superuser(superuser=superuser):
            raise PermissionError(
                "hot_apply requires superuser authorisation: pass superuser=True "
                f"or set {_ENV_HOT_APPLY}=1"
            )
        old_program = self._program
        self._prune_user_templates(program)
        register_user_templates(self._library, program)
        # Prune/reset runtime state for topology changes.
        self._prune_runtime_state(old_program, program)
        self._program = program
        self._fire_hooks(is_restart=False)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_superuser(*, superuser: bool) -> bool:
        """Return True when either the caller flag or the env var grants authority."""
        if superuser:
            return True
        return os.environ.get(_ENV_HOT_APPLY, "") == "1"

    def _prune_user_templates(self, new_program: Program) -> None:
        """Remove program-scoped user templates absent from *new_program*.

        App-global ``library=="custom"`` templates are owned by the App layer
        and must not be pruned here (SWD-180).
        """
        new_ids = set(new_program.user_templates.keys())
        to_remove = [
            (tmpl.library, tmpl.template_id)
            for tmpl in self._library.all_templates()
            if (
                not tmpl.is_builtin
                and tmpl.library != "custom"
                and tmpl.template_id not in new_ids
            )
        ]
        for lib, tid in to_remove:
            self._library.unregister(lib, tid)

    def _prune_runtime_state(
        self,
        old_program: Program | None,
        new_program: Program,
    ) -> None:
        """Drop stale state on hot-apply topology changes.

        * Instances removed from the program → state entry dropped.
        * Same instance_id but different template_id → state entry reset
          (the new template has a different state schema).
        """
        for inst_id in list(self._runtime.state.keys()):
            if inst_id not in new_program.instances:
                self._runtime.reset_state(inst_id)
            elif old_program is not None and inst_id in old_program.instances:
                old_inst = old_program.instances[inst_id]
                new_inst = new_program.instances[inst_id]
                if (old_inst.library, old_inst.template_id) != (
                    new_inst.library,
                    new_inst.template_id,
                ):
                    self._runtime.reset_state(inst_id)


class ProjectLoader:
    """Hold and manage an active SoftPlcProject + BlockRuntime (SWD-182).

  Typical usage::

        library = TemplateLibrary()
        runtime = BlockRuntime(library)
        register_builtins(library, runtime)

        loader = ProjectLoader(library, runtime)
        loader.load(project_from_dict(yaml_dict))

        # inside on_control:
        loader.tick(context, dt)
    """

    def __init__(self, library: TemplateLibrary, runtime: BlockRuntime) -> None:
        self._library = library
        self._runtime = runtime
        self._project: SoftPlcProject | None = None
        self._on_apply_hooks: list[Callable[[bool], None]] = []

    @property
    def project(self) -> SoftPlcProject | None:
        """Currently active project, or ``None`` before first load."""
        return self._project

    @property
    def program(self) -> Program | None:
        """Main / canvas program (first program on ``MAIN_TASK_ID``)."""
        if self._project is None:
            return None
        return main_program(self._project)

    @property
    def runtime(self) -> BlockRuntime:
        return self._runtime

    def add_on_apply_hook(self, fn: Callable[[bool], None]) -> None:
        self._on_apply_hooks.append(fn)

    def _fire_hooks(self, is_restart: bool) -> None:
        for fn in self._on_apply_hooks:
            fn(is_restart)

    def load(self, project: SoftPlcProject | Program) -> None:
        """Load *project* with restart semantics."""
        project = self._coerce_project(project)
        self._register_all_user_templates(project)
        self._runtime.reset_state()
        self._project = project
        self._fire_hooks(is_restart=True)

    def restart_apply(self, project: SoftPlcProject | Program) -> None:
        if isinstance(project, Program):
            self.replace_main_program(project, restart=True)
            return
        self.load(project)

    def hot_apply(
        self, project: SoftPlcProject | Program, *, superuser: bool = False
    ) -> None:
        if isinstance(project, Program):
            self.replace_main_program(project, restart=False, superuser=superuser)
            return
        if not ProgramLoader._is_superuser(superuser=superuser):
            raise PermissionError(
                "hot_apply requires superuser authorisation: pass superuser=True "
                f"or set {_ENV_HOT_APPLY}=1"
            )
        if classify_project_apply(self._project, project) != "hot":
            raise ValueError(
                "hot_apply rejected: project structure changed; use restart_apply"
            )
        old_project = self._project
        self._register_all_user_templates(project)
        self._prune_runtime_state(old_project, project)
        self._project = project
        self._fire_hooks(is_restart=False)

    def replace_main_program(
        self,
        program: Program,
        *,
        restart: bool = True,
        superuser: bool = False,
    ) -> None:
        """Swap the Main-task program (canvas / legacy Program apply path)."""
        program = migrate_program_to_pid(program)
        proj = self._project
        if proj is None:
            self.load(
                project_from_dict(
                    migrate_legacy_program_dict(program_to_dict(program))
                )
            )
            return
        main_id = self._main_program_id(proj)
        new_programs = dict(proj.programs)
        new_programs[main_id] = program
        new_project = SoftPlcProject(
            programs=new_programs,
            tasks=list(proj.tasks),
            scan_period_s=proj.scan_period_s,
            version=proj.version,
        )
        if restart:
            self.restart_apply(new_project)
        else:
            self.hot_apply(new_project, superuser=superuser)

    def replace_program(
        self,
        program_id: str,
        program: Program,
        *,
        restart: bool = True,
        superuser: bool = False,
    ) -> None:
        """Swap a selected Program in the active project."""
        program = migrate_program_to_pid(program)
        proj = self._project
        if proj is None:
            if program_id in ("", self._main_program_id(SoftPlcProject())):
                self.load(
                    project_from_dict(
                        migrate_legacy_program_dict(program_to_dict(program))
                    )
                )
                return
            raise KeyError(f"Program {program_id!r} not found")
        if program_id not in proj.programs:
            raise KeyError(f"Program {program_id!r} not found")
        new_programs = dict(proj.programs)
        new_programs[program_id] = program
        new_project = SoftPlcProject(
            programs=new_programs,
            tasks=list(proj.tasks),
            scan_period_s=proj.scan_period_s,
            version=proj.version,
        )
        if restart:
            self.restart_apply(new_project)
        else:
            self.hot_apply(new_project, superuser=superuser)

    @staticmethod
    def _main_program_id(project: SoftPlcProject) -> str:
        from plcassistant.surface.model import MAIN_TASK_ID

        for task in project.tasks:
            if task.task_id == MAIN_TASK_ID and task.programs:
                return task.programs[0]
        for task in sorted(project.tasks, key=lambda t: t.priority):
            if task.programs:
                return task.programs[0]
        return "main"

    @staticmethod
    def _coerce_project(project: SoftPlcProject | Program) -> SoftPlcProject:
        if isinstance(project, Program):
            return project_from_dict(
                migrate_legacy_program_dict(program_to_dict(project))
            )
        migrated_programs = {
            pid: migrate_program_to_pid(prog)
            for pid, prog in project.programs.items()
        }
        if any(migrated_programs[pid] is not project.programs[pid] for pid in project.programs):
            return SoftPlcProject(
                programs=migrated_programs,
                tasks=list(project.tasks),
                scan_period_s=project.scan_period_s,
                version=project.version,
            )
        return project

    def apply(
        self,
        project: SoftPlcProject,
        *,
        mode: str = "auto",
        superuser: bool = False,
    ) -> str:
        """Apply *project* using ``mode`` of ``auto``, ``restart``, or ``hot``.

        Returns the mode actually used (``restart`` or ``hot``).
        """
        if mode == "auto":
            mode = classify_project_apply(self._project, project)
        if mode == "hot":
            self.hot_apply(project, superuser=superuser)
        else:
            self.restart_apply(project)
        return mode

    def tick(
        self,
        context: Any,
        dt: float,
        *,
        prefer_context: frozenset[tuple[str, str]] | set[tuple[str, str]] | None = None,
    ) -> None:
        """Run all scheduled Programs: Tasks by priority, programs in call order."""
        if self._project is None:
            return
        for _task, _prog_id, prog in scheduled_programs(self._project):
            self._runtime.tick(
                prog, context, dt, prefer_context=prefer_context
            )

    def _register_all_user_templates(self, project: SoftPlcProject) -> None:
        """Prune stale program user templates; keep App-global custom templates."""
        all_ids: set[str] = set()
        for prog in project.programs.values():
            all_ids.update(prog.user_templates.keys())
        to_remove = [
            (tmpl.library, tmpl.template_id)
            for tmpl in self._library.all_templates()
            if (
                not tmpl.is_builtin
                and tmpl.library != "custom"
                and tmpl.template_id not in all_ids
            )
        ]
        for lib, tid in to_remove:
            self._library.unregister(lib, tid)
        for prog in project.programs.values():
            register_user_templates(self._library, prog)

    def _prune_runtime_state(
        self,
        old_project: SoftPlcProject | None,
        new_project: SoftPlcProject,
    ) -> None:
        """Drop or reset runtime state when program topology changes on hot apply."""
        if old_project is None:
            return
        new_instance_ids: set[str] = set()
        old_by_inst: dict[str, tuple[str, str]] = {}
        for _t, _pid, prog in scheduled_programs(old_project):
            for iid, inst in prog.instances.items():
                old_by_inst[iid] = (inst.library, inst.template_id)
        for _t, _pid, prog in scheduled_programs(new_project):
            new_instance_ids.update(prog.instances.keys())
            for iid, inst in prog.instances.items():
                if iid not in old_by_inst:
                    continue
                if old_by_inst[iid] != (inst.library, inst.template_id):
                    self._runtime.reset_state(iid)
        for inst_id in list(self._runtime.state.keys()):
            if inst_id not in new_instance_ids:
                self._runtime.reset_state(inst_id)


__all__ = [
    "ProgramLoader",
    "ProjectLoader",
]
