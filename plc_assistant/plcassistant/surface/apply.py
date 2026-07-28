"""Apply policy for block programs (SWD-117).

``ProgramLoader`` holds the active Program and BlockRuntime.  Two apply modes
are supported:

restart_apply (default)
    Swap the program **and** clear all runtime state (integrals, flags, cached
    outputs).  Always safe.  Equivalent to a process restart: the new program
    starts from a clean slate on the next tick.

hot_apply (superuser only)
    Swap the program without clearing runtime state.  Useful during
    development to apply incremental changes without losing controller
    wind-up.  Requires *superuser* authorisation (see below).

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
from typing import TYPE_CHECKING, Callable

from plcassistant.surface.model import Program, TemplateLibrary
from plcassistant.surface.runtime import BlockRuntime
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
        """Remove user templates from the library that are absent from *new_program*."""
        new_ids = set(new_program.user_templates.keys())
        to_remove = [
            (tmpl.library, tmpl.template_id)
            for tmpl in self._library.all_templates()
            if not tmpl.is_builtin and tmpl.template_id not in new_ids
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


__all__ = [
    "ProgramLoader",
]
