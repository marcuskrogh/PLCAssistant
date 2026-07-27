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
``hot_apply`` is gated on either:

* Passing ``superuser=True`` explicitly (e.g. from a trusted App setting), or
* The environment variable ``PLCASSISTANT_SUPERUSER_HOT_APPLY=1`` being set.

If neither condition is met ``hot_apply`` raises ``PermissionError``.

No Home Assistant dependency; no hard-wired I/O.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

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

        # In App settings: enable_hot_apply = True
        loader.hot_apply(new_program, superuser=True)
        # or set PLCASSISTANT_SUPERUSER_HOT_APPLY=1 in the environment
    """

    def __init__(self, library: TemplateLibrary, runtime: BlockRuntime) -> None:
        self._library = library
        self._runtime = runtime
        self._program: Program | None = None

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
    # Public API
    # ------------------------------------------------------------------

    def load(self, program: Program) -> None:
        """Load *program* as the active program.

        Clears all runtime state (restart semantics).  Equivalent to
        ``restart_apply``.  User templates from *program* are registered into
        the ``TemplateLibrary`` so the runtime can resolve them.
        """
        register_user_templates(self._library, program)
        self._runtime.reset_state()
        self._program = program

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

        Authorisation
        ~~~~~~~~~~~~~
        Requires *one* of:

        * ``superuser=True`` (caller asserts authority — e.g. trusted App
          setting ``enable_hot_apply``), **or**
        * ``PLCASSISTANT_SUPERUSER_HOT_APPLY=1`` set in the environment.

        Raises ``PermissionError`` when neither condition holds.

        .. warning::
            Hot-apply is intended for development only.  State from the
            previous program may be inconsistent with the new program's
            topology (e.g. a removed instance retains stale state entries).
            Call ``runtime.reset_state()`` manually afterwards if needed.
        """
        if not self._is_superuser(superuser=superuser):
            raise PermissionError(
                "hot_apply requires superuser authorisation: pass superuser=True "
                f"or set {_ENV_HOT_APPLY}=1"
            )
        register_user_templates(self._library, program)
        self._program = program

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_superuser(*, superuser: bool) -> bool:
        """Return True when either the caller flag or the env var grants authority."""
        if superuser:
            return True
        return os.environ.get(_ENV_HOT_APPLY, "") == "1"


__all__ = [
    "ProgramLoader",
]
