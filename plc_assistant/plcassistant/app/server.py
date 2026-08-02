"""Stdlib http.server-based App for the operator dashboard + block editor.

Endpoints
---------
GET  /                      Operator dashboard + program editor (HTML/JS)
GET  /api/program           Main scheduled program as JSON dict (canvas)
PUT  /api/program           Replace Main program; body = JSON dict
GET  /api/project           Soft-PLC project tree (Tasks + Programs)
PUT  /api/project           Replace project tree; structure → restart apply
GET  /api/tasks             Saved schedule Tasks (draft project)
POST /api/tasks             Create Task in saved schedule draft
PUT  /api/tasks/<id>        Update Task metadata in saved schedule draft
DELETE /api/tasks/<id>      Delete Task; its Programs become unscheduled in draft
PUT  /api/tasks/<id>/programs  Replace ordered Program call list in draft
GET  /api/programs/unscheduled  Programs not assigned in saved schedule draft
POST /api/schedule/save     Persist saved project without touching live Soft-PLC
POST /api/schedule/apply    Restart-apply saved project into live Soft-PLC
GET  /api/schedule/status   Saved/applied signature comparison
GET  /api/library           All templates (shipped + custom + legacy user) as JSON list
PUT  /api/library/shipped/<tid>  Persist shipped template override
POST /api/library/shipped/<tid>/reset  Reset shipped template to factory
POST /api/library/custom    Create/update a global custom template
DELETE /api/library/custom/<tid>  Delete a global custom template
POST /api/library/user      Create/update a user template; body = template JSON
DELETE /api/library/user/<tid>  Delete a user template
POST /api/place             Place a block; body = {template_id, library, instance_id, x?, y?}
POST /api/reset_instance    Reset instance params to library defaults; body = {instance_id}
POST /api/apply             Apply program; body = {mode: "restart"|"hot"}
                            (hot requires PLCASSISTANT_SUPERUSER_HOT_APPLY=1;
                             client "superuser" field is ignored)
GET  /api/runtime           Live Soft-PLC status + tag snapshot
POST /api/cmd               Operator command; body = {name: "start"|"stop"|"reset"}

The server holds a saved project draft plus a live ProjectLoader project.  Schedule
edits update the saved draft; Save persists it; Apply restart-loads it into live.
No file persistence by default; callers may pass an initial project or legacy
program dict.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
from collections.abc import Mapping

from plcassistant.app._canvas import get_canvas_html
from plcassistant.app.operator_runtime import OperatorRuntime
from plcassistant.io.mqtt_topics import DEFAULT_INSTANCE_ID
from plcassistant.surface.apply import ProjectLoader
from plcassistant.surface.builtin import (
    PID_TEMPLATE_ID,
    pid_template,
    register_builtins,
    wedge_softplc_project,
)
from plcassistant.surface.model import (
    BlockTemplate,
    PinDirection,
    PinSpec,
    Program,
    SoftPlcProject,
    Task,
    TemplateLibrary,
)
from plcassistant.surface.program_status import health_from_log, program_run_status
from plcassistant.surface.runtime import BlockRuntime
from plcassistant.surface.schema import (
    classify_project_apply,
    place_block,
    program_from_dict,
    program_to_dict,
    project_from_dict,
    project_to_dict,
    reset_instance,
)
from plcassistant.surface.user_library import (
    add_user_template,
    make_user_template,
    remove_user_template,
)


def _make_loader() -> tuple[ProjectLoader, TemplateLibrary, BlockRuntime]:
    library = TemplateLibrary()
    runtime = BlockRuntime(library)
    register_builtins(library, runtime)
    loader = ProjectLoader(library, runtime)
    return loader, library, runtime


_ENV_HOT_APPLY = "PLCASSISTANT_SUPERUSER_HOT_APPLY"


def _now_ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slugify_program_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "program"


def _clone_project(project: SoftPlcProject) -> SoftPlcProject:
    return project_from_dict(project_to_dict(project))


def _load_project_pair(data: Mapping[str, Any]) -> tuple[SoftPlcProject, SoftPlcProject]:
    if isinstance(data.get("project"), Mapping):
        saved_raw = data["project"]
        applied_raw = data.get("applied_project") or saved_raw
    else:
        saved_raw = data
        applied_raw = data
    saved = project_from_dict(saved_raw)
    applied = project_from_dict(applied_raw)
    return saved, applied


def _pin_payload(pin: PinSpec) -> dict[str, Any]:
    return {
        "name": pin.name,
        "direction": pin.direction.value,
        "data_type": pin.data_type,
        **({"default": pin.default} if pin.default is not None else {}),
    }


def _template_payload(template: BlockTemplate, *, kind: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "template_id": template.template_id,
        "library": template.library,
        "description": template.description,
        "pins": [_pin_payload(pin) for pin in template.pins],
        "params": template.params,
        "body": template.body,
        "is_builtin": template.is_builtin,
    }
    if kind is not None:
        payload["kind"] = kind
    return payload


def _template_from_payload(
    data: Mapping[str, Any],
    *,
    template_id: str | None = None,
    library: str,
    is_builtin: bool,
) -> BlockTemplate:
    tid = str(template_id or data.get("template_id", "")).strip()
    if not tid:
        raise ValueError("template_id required")
    raw_pins = data.get("pins") or []
    if not isinstance(raw_pins, list):
        raise ValueError("pins must be a list")
    pins: list[PinSpec] = []
    for raw in raw_pins:
        if not isinstance(raw, Mapping):
            raise ValueError("pin must be a mapping")
        raw_dir = str(raw.get("direction", "IN")).upper()
        try:
            direction = PinDirection(raw_dir)
        except ValueError as exc:
            raise ValueError(f"invalid pin direction {raw.get('direction')!r}") from exc
        name = str(raw.get("name", "")).strip()
        if not name:
            raise ValueError("pin name required")
        pins.append(
            PinSpec(
                name=name,
                direction=direction,
                data_type=str(raw.get("data_type", "float")),
                default=raw.get("default"),
            )
        )
    raw_params = data.get("params") or {}
    if not isinstance(raw_params, Mapping):
        raise ValueError("params must be a mapping")
    return BlockTemplate(
        template_id=tid,
        library=library,
        description=str(data.get("description", "")),
        pins=pins,
        params=dict(raw_params),
        body=str(data.get("body", "")),
        is_builtin=is_builtin,
    )


class AppState:
    """Mutable shared state for one App server instance."""

    def __init__(
        self,
        initial_program: dict[str, Any] | None = None,
        *,
        initial_project: dict[str, Any] | None = None,
        program_path: str | None = None,
    ) -> None:
        self.loader, self.library, self.runtime = _make_loader()
        self.superuser_hot_apply: bool = os.environ.get(_ENV_HOT_APPLY, "") == "1"
        self.program_path = program_path
        self.operator = OperatorRuntime()
        self.program_logs: dict[str, list[dict[str, str]]] = {}
        self.library_state: dict[str, dict[str, dict[str, Any]]] = {
            "shipped_overrides": {},
            "custom": {},
        }
        loaded: dict[str, Any] | None = initial_project or initial_program
        if loaded is None and program_path and os.path.isfile(program_path):
            try:
                with open(program_path, encoding="utf-8") as fh:
                    loaded = json.load(fh)
                if not isinstance(loaded, dict):
                    loaded = None
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                loaded = None
        default_project = wedge_softplc_project()
        if loaded is None:
            loaded = default_project
        if isinstance(loaded.get("library"), Mapping):
            try:
                self._load_library_state(loaded["library"])
            except (ValueError, KeyError, TypeError):
                self.library_state = {"shipped_overrides": {}, "custom": {}}
        try:
            saved_project, applied_project = _load_project_pair(loaded)
        except (ValueError, KeyError, TypeError):
            saved_project = project_from_dict(default_project)
            applied_project = _clone_project(saved_project)
        self.saved_project = _clone_project(saved_project)
        self.loader.load(_clone_project(applied_project))
        self._reapply_library_state()
        self._ensure_program_logs()
        if "tank" in self.program_logs and not self.program_logs["tank"]:
            self.append_log("tank", "info", "Program Tank loaded")

    def _load_library_state(self, raw: Mapping[str, Any]) -> None:
        shipped = raw.get("shipped_overrides") or {}
        custom = raw.get("custom") or {}
        if not isinstance(shipped, Mapping) or not isinstance(custom, Mapping):
            return
        for tid, payload in shipped.items():
            if not isinstance(payload, Mapping):
                continue
            try:
                tmpl = _template_from_payload(
                    payload,
                    template_id=str(tid),
                    library="builtin",
                    is_builtin=True,
                )
            except (ValueError, KeyError, TypeError):
                continue
            self.library_state["shipped_overrides"][tmpl.template_id] = _template_payload(tmpl)
            self.library.register(tmpl)
        for tid, payload in custom.items():
            if not isinstance(payload, Mapping):
                continue
            try:
                tmpl = _template_from_payload(
                    payload,
                    template_id=str(tid),
                    library="custom",
                    is_builtin=False,
                )
            except (ValueError, KeyError, TypeError):
                continue
            self.library_state["custom"][tmpl.template_id] = _template_payload(tmpl)
            self.library.register(tmpl)

    def _reapply_library_state(self) -> None:
        """Re-register App-owned library entries after Soft-PLC load/apply prune."""
        self._register_library_into(self.library)
        live = self._live_skid_loader()
        if live is not None:
            self._register_library_into(live._library)

    def _register_library_into(self, library: Any) -> None:
        for payload in self.library_state["shipped_overrides"].values():
            tmpl = _template_from_payload(
                payload,
                template_id=str(payload.get("template_id", "")),
                library="builtin",
                is_builtin=True,
            )
            library.register(tmpl)
        for payload in self.library_state["custom"].values():
            tmpl = _template_from_payload(
                payload,
                template_id=str(payload.get("template_id", "")),
                library="custom",
                is_builtin=False,
            )
            library.register(tmpl)

    def _dry_run_equation(
        self,
        equation: str,
        template: Any,
        params: Mapping[str, Any],
    ) -> None:
        """Validate math equation with defaults; raise ValueError on failure."""
        from plcassistant.surface.equations import EquationError, evaluate_equation
        from plcassistant.surface.model import PinDirection

        text = str(equation or "").strip()
        if not text:
            return
        pins = {
            pin.name: (pin.default if pin.default is not None else 0.0)
            for pin in template.pins
            if pin.direction is PinDirection.IN
        }
        try:
            evaluate_equation(text, template, pins, dict(params), {}, 0.1)
        except EquationError as exc:
            raise ValueError(f"invalid equation: {exc}") from exc

    def _validate_program_equations(self, program: Program) -> None:
        for inst in program.instances.values():
            tmpl = self.library.get(inst.library, inst.template_id)
            if tmpl is None:
                tmpl = (program.user_templates or {}).get(inst.template_id)
            if tmpl is None or not inst.equation:
                continue
            self._dry_run_equation(inst.equation, tmpl, inst.params)

    def _sync_scan_period_to_runtime(self) -> None:
        """Propagate project ``scan_period_s`` into the live MQTT scan loop."""
        proj = self.loader.project
        if proj is None:
            return
        loop = self.operator._scan_loop()
        if loop is not None and hasattr(loop, "set_scan_period_s"):
            loop.set_scan_period_s(proj.scan_period_s)

    def _live_skid_loader(self) -> Any | None:
        """ProjectLoader owned by the attached MQTT scan loop Skid, if any."""
        loop = self.operator._scan_loop()
        if loop is None:
            return None
        logic = getattr(loop, "logic", None)
        skid = getattr(logic, "skid", None)
        return getattr(skid, "program_loader", None) if skid is not None else None

    def _sync_applied_project_to_runtime(self, *, mode: str = "restart") -> None:
        """Push the live applied project into the scan-loop Skid loader.

        ``mode`` must match the App loader apply (``hot`` vs ``restart``) so a
        hot Apply does not ``restart_apply`` the MQTT Skid and re-bumpless
        CVs to 0 while MODE stays RUNNING (SWD-225 review-fix).
        """
        live = self._live_skid_loader()
        applied = self.loader.project
        if live is None or applied is None:
            return
        clone = _clone_project(applied)
        if mode == "hot":
            try:
                live.hot_apply(clone, superuser=True)
            except (PermissionError, ValueError):
                live.restart_apply(clone)
        else:
            live.restart_apply(clone)
        self._register_library_into(live._library)

    @property
    def instance_id(self) -> str:
        return self.operator.instance_id

    @instance_id.setter
    def instance_id(self, value: str) -> None:
        self.operator.instance_id = str(value) if value else DEFAULT_INSTANCE_ID

    def attach_runtime(self, lifecycle: Any) -> None:
        """Attach MQTT scan lifecycle so the UI can read tags and issue cmds."""
        self.operator.attach(lifecycle)

        def _on_attach(_loop: Any) -> None:
            self._sync_applied_project_to_runtime()
            self._sync_scan_period_to_runtime()

        loop = self.operator._scan_loop()
        if loop is not None:
            _on_attach(loop)
        elif hasattr(lifecycle, "set_on_attach"):
            lifecycle.set_on_attach(_on_attach)

    def runtime_snapshot(self) -> dict[str, Any]:
        """JSON-serialisable Soft-PLC status for the operator dashboard."""
        return self.operator.snapshot()

    def issue_cmd(self, name: str) -> dict[str, Any]:
        """Start / stop / reset via scan loop (enqueued), or defer while offline."""
        return self.operator.issue_cmd(name)

    @property
    def project_dict(self) -> dict[str, Any]:
        return project_to_dict(self.saved_project)

    @property
    def applied_project_dict(self) -> dict[str, Any]:
        proj = self.loader.project
        if proj is None:
            return project_to_dict(self.saved_project)
        return project_to_dict(proj)

    @property
    def persistence_dict(self) -> dict[str, Any]:
        return {
            "version": "2.0",
            "project": self.project_dict,
            "applied_project": self.applied_project_dict,
            "library": self.library_persistence_dict(),
        }

    @property
    def program_dict(self) -> dict[str, Any]:
        return self.program_dict_for(None)

    def main_program_id(self) -> str:
        return self.loader._main_program_id(self.saved_project)

    def program_for_id(self, program_id: str | None) -> Program | None:
        pid = program_id or self.main_program_id()
        if pid not in self.saved_project.programs:
            raise KeyError(f"Program {pid!r} not found")
        return self.saved_project.programs[pid]

    def program_dict_for(self, program_id: str | None) -> dict[str, Any]:
        prog = self.program_for_id(program_id)
        if prog is None:
            return {
                "version": "1.0",
                "instances": {},
                "wires": [],
                "execution_order": [],
            }
        return program_to_dict(prog)

    def _set_program(self, program_id: str | None, new_prog: Program) -> None:
        """Replace the selected program in saved and live projects."""
        pid = program_id or self.main_program_id()
        if pid not in self.saved_project.programs:
            raise KeyError(f"Program {pid!r} not found")
        saved_programs = dict(self.saved_project.programs)
        saved_programs[pid] = new_prog
        self.saved_project = SoftPlcProject(
            programs=saved_programs,
            tasks=list(self.saved_project.tasks),
            scan_period_s=self.saved_project.scan_period_s,
            version=self.saved_project.version,
        )
        self._sync_program_to_live(pid)

    def _sync_program_to_live(self, program_id: str) -> None:
        """Apply one saved Program body without changing the live Task schedule."""
        if self.loader.project is None or program_id not in self.loader.project.programs:
            return
        live_program = _clone_project(self.saved_project).programs[program_id]
        self.loader.replace_program(program_id, live_program, restart=True)
        self._reapply_library_state()
        # Keep scan-loop Skid aligned with App applied Programs (SWD-225).
        self._sync_applied_project_to_runtime()

    def _ensure_program_logs(self) -> None:
        for pid in self.saved_project.programs:
            self.program_logs.setdefault(pid, [])
        for pid in list(self.program_logs):
            if pid not in self.saved_project.programs:
                self.program_logs.pop(pid, None)

    def append_log(self, program_id: str, level: str, message: str) -> None:
        self.program_logs.setdefault(program_id, []).append(
            {"ts": _now_ts(), "level": level, "message": message}
        )

    def program_logs_for(self, program_id: str) -> list[dict[str, str]]:
        self._ensure_program_logs()
        if program_id not in self.saved_project.programs:
            raise KeyError(f"Program {program_id!r} not found")
        return list(self.program_logs.get(program_id, []))

    def _softplc_running(self) -> bool:
        snap = self.runtime_snapshot()
        mode = snap.get("mode")
        if mode is None and isinstance(snap.get("tags"), dict):
            mode_tag = snap["tags"].get("MODE")
            if isinstance(mode_tag, dict):
                mode = mode_tag.get("value")
        return str(mode or "").upper() == "RUNNING"

    def _task_id_for_program(self, project: SoftPlcProject, program_id: str) -> str | None:
        for task in project.tasks:
            if program_id in task.programs:
                return task.task_id
        return None

    def program_card(self, program_id: str) -> dict[str, Any]:
        saved = self.saved_project
        applied = self.loader.project
        if program_id not in saved.programs:
            raise KeyError(f"Program {program_id!r} not found")
        prog = saved.programs[program_id]
        logs = self.program_logs.get(program_id, [])
        task_id = self._task_id_for_program(applied, program_id) if applied else None
        saved_task_id = self._task_id_for_program(saved, program_id)
        if applied is not None and program_id in applied.programs:
            status = program_run_status(applied, program_id, self._softplc_running())
        else:
            status = "unscheduled"
        return {
            "id": program_id,
            "name": prog.name or program_id,
            "description": prog.description,
            "status": status,
            "health": health_from_log(logs),
            "task_id": task_id,
            "saved_task_id": saved_task_id,
            "pending_schedule": saved_task_id != task_id,
        }

    def program_cards(self) -> list[dict[str, Any]]:
        self._ensure_program_logs()
        return [self.program_card(pid) for pid in self.saved_project.programs]

    def create_program(self, name: str, description: str = "") -> dict[str, Any]:
        clean_name = str(name).strip()
        if not clean_name:
            raise ValueError("name required")
        base = _slugify_program_id(clean_name)
        pid = base
        suffix = 2
        while pid in self.saved_project.programs:
            pid = f"{base}-{suffix}"
            suffix += 1
        programs = dict(self.saved_project.programs)
        programs[pid] = Program(name=clean_name, description=str(description or ""))
        new_project = SoftPlcProject(
            programs=programs,
            tasks=list(self.saved_project.tasks),
            scan_period_s=self.saved_project.scan_period_s,
            version=self.saved_project.version,
        )
        self.saved_project = new_project
        self.loader.restart_apply(_clone_project(new_project))
        self._reapply_library_state()
        self._ensure_program_logs()
        self.append_log(pid, "info", f"Program {clean_name} created")
        self.persist_program()
        return self.program_card(pid)

    def update_program_meta(self, program_id: str, name: str, description: str = "") -> dict[str, Any]:
        prog = self.program_for_id(program_id)
        if prog is None:
            raise KeyError(f"Program {program_id!r} not found")
        clean_name = str(name).strip()
        if not clean_name:
            raise ValueError("name required")
        prog.name = clean_name
        prog.description = str(description or "")
        self._sync_program_to_live(program_id)
        self.persist_program()
        self.append_log(program_id, "info", "Program settings saved")
        return self.program_card(program_id)

    def resolve_template(self, program_id: str | None, library: str, template_id: str):
        """Resolve a template for *program_id*.

        User templates are Program-scoped — never fall back to another Program's
        globally registered user template.
        """
        prog = self.program_for_id(program_id)
        if library == "user":
            if prog is None:
                return None
            return (prog.user_templates or {}).get(template_id)
        tmpl = self.library.get(library, template_id)
        if tmpl is not None:
            return tmpl
        if prog is not None:
            return (prog.user_templates or {}).get(template_id)
        return None

    def library_persistence_dict(self) -> dict[str, Any]:
        """JSON payload for shipped overrides and global custom templates."""
        return {
            "shipped_overrides": self.library_state["shipped_overrides"],
            "custom": self.library_state["custom"],
        }

    def library_payload(self, program_id: str | None = None) -> list[dict[str, Any]]:
        """Shipped templates, global custom, and selected Program user templates."""
        self._reapply_library_state()
        builtins = [t for t in self.library.all_templates() if t.is_builtin]
        custom = [
            _template_from_payload(
                payload,
                template_id=str(payload.get("template_id", "")),
                library="custom",
                is_builtin=False,
            )
            for payload in self.library_state["custom"].values()
        ]
        prog = self.program_for_id(program_id)
        user = list((prog.user_templates or {}).values()) if prog is not None else []
        return (
            [_template_payload(t, kind="shipped") for t in builtins]
            + [_template_payload(t, kind="custom") for t in custom]
            + [_template_payload(t, kind="user") for t in user]
        )

    def library_template(self, library: str, template_id: str) -> dict[str, Any]:
        tmpl = self.library.get(library, template_id)
        if tmpl is None:
            raise KeyError(f"Template {library!r}/{template_id!r} not found")
        kind = "shipped" if tmpl.is_builtin else tmpl.library
        return _template_payload(tmpl, kind=kind)

    def save_shipped_template(self, template_id: str, data: Mapping[str, Any]) -> dict[str, Any]:
        if template_id != PID_TEMPLATE_ID:
            raise KeyError(f"Shipped template {template_id!r} not found")
        tmpl = _template_from_payload(
            data,
            template_id=template_id,
            library="builtin",
            is_builtin=True,
        )
        self._dry_run_equation(tmpl.body, tmpl, tmpl.params)
        self.library.register(tmpl)
        self.library_state["shipped_overrides"][template_id] = _template_payload(tmpl)
        self.persist_program()
        return _template_payload(tmpl, kind="shipped")

    def reset_shipped_template(self, template_id: str) -> dict[str, Any]:
        if template_id != PID_TEMPLATE_ID:
            raise KeyError(f"Shipped template {template_id!r} not found")
        tmpl = pid_template()
        self.library.register(tmpl)
        self.library_state["shipped_overrides"].pop(template_id, None)
        self.persist_program()
        return _template_payload(tmpl, kind="shipped")

    def save_custom_template(self, data: Mapping[str, Any]) -> dict[str, Any]:
        tmpl = _template_from_payload(data, library="custom", is_builtin=False)
        self._dry_run_equation(tmpl.body, tmpl, tmpl.params)
        self.library.register(tmpl)
        self.library_state["custom"][tmpl.template_id] = _template_payload(tmpl)
        self.persist_program()
        return _template_payload(tmpl, kind="custom")

    def delete_custom_template(self, template_id: str) -> dict[str, Any]:
        if template_id not in self.library_state["custom"]:
            raise KeyError(f"Custom template {template_id!r} not found")
        self.library.unregister("custom", template_id)
        self.library_state["custom"].pop(template_id, None)
        self.persist_program()
        return {"deleted": template_id}

    def delete_program(self, program_id: str) -> dict[str, Any]:
        if program_id not in self.saved_project.programs:
            raise KeyError(f"Program {program_id!r} not found")
        programs = dict(self.saved_project.programs)
        programs.pop(program_id)
        tasks = [
            Task(
                task.task_id,
                task.priority,
                [pid for pid in task.programs if pid != program_id],
                task.description,
            )
            for task in self.saved_project.tasks
        ]
        new_project = SoftPlcProject(
            programs=programs,
            tasks=tasks,
            scan_period_s=self.saved_project.scan_period_s,
            version=self.saved_project.version,
        )
        self.saved_project = new_project
        self.loader.restart_apply(_clone_project(new_project))
        self._reapply_library_state()
        self.program_logs.pop(program_id, None)
        self._ensure_program_logs()
        self.persist_program()
        return {"deleted": program_id}

    def tasks_payload(self) -> list[dict[str, Any]]:
        return [
            {
                "id": task.task_id,
                "priority": task.priority,
                "description": task.description,
                "programs": list(task.programs),
            }
            for task in sorted(self.saved_project.tasks, key=lambda t: (t.priority, t.task_id))
        ]

    def _find_task(self, task_id: str) -> Task:
        for task in self.saved_project.tasks:
            if task.task_id == task_id:
                return task
        raise KeyError(f"Task {task_id!r} not found")

    def _replace_saved_tasks(self, tasks: list[Task]) -> None:
        new_project = SoftPlcProject(
            programs=dict(self.saved_project.programs),
            tasks=tasks,
            scan_period_s=self.saved_project.scan_period_s,
            version=self.saved_project.version,
        )
        self.saved_project = project_from_dict(project_to_dict(new_project))

    def _task_payload(self, task: Task) -> dict[str, Any]:
        return {
            "id": task.task_id,
            "priority": task.priority,
            "description": task.description,
            "programs": list(task.programs),
        }

    def create_task(
        self, task_id: str, priority: int, description: str = ""
    ) -> dict[str, Any]:
        clean_id = str(task_id).strip()
        if not clean_id:
            raise ValueError("task id required")
        if any(task.task_id == clean_id for task in self.saved_project.tasks):
            raise ValueError(f"Task {clean_id!r} already exists")
        task = Task(clean_id, int(priority), [], str(description or ""))
        self._replace_saved_tasks(list(self.saved_project.tasks) + [task])
        return self._task_payload(task)

    def update_task_meta(
        self,
        task_id: str,
        *,
        new_id: str | None = None,
        priority: int | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        task = self._find_task(task_id)
        clean_id = str(new_id if new_id is not None else task.task_id).strip()
        if not clean_id:
            raise ValueError("task id required")
        if clean_id != task.task_id and any(
            other.task_id == clean_id for other in self.saved_project.tasks
        ):
            raise ValueError(f"Task {clean_id!r} already exists")
        updated = Task(
            clean_id,
            int(priority if priority is not None else task.priority),
            list(task.programs),
            str(description if description is not None else task.description),
        )
        tasks = [
            updated if existing.task_id == task_id else existing
            for existing in self.saved_project.tasks
        ]
        self._replace_saved_tasks(tasks)
        return self._task_payload(updated)

    def delete_task(self, task_id: str) -> dict[str, Any]:
        self._find_task(task_id)
        tasks = [task for task in self.saved_project.tasks if task.task_id != task_id]
        self._replace_saved_tasks(tasks)
        return {"deleted": task_id}

    def unscheduled_programs(self) -> list[dict[str, Any]]:
        assigned = {pid for task in self.saved_project.tasks for pid in task.programs}
        result: list[dict[str, Any]] = []
        for pid, prog in self.saved_project.programs.items():
            if pid in assigned:
                continue
            result.append(
                {
                    "id": pid,
                    "name": prog.name or pid,
                    "description": prog.description,
                }
            )
        return result

    def set_task_programs(self, task_id: str, program_ids: list[str]) -> dict[str, Any]:
        task = self._find_task(task_id)
        ordered = [str(pid) for pid in program_ids]
        if len(set(ordered)) != len(ordered):
            raise ValueError("program list contains duplicates")
        for pid in ordered:
            if pid not in self.saved_project.programs:
                raise ValueError(f"Program {pid!r} not found")
            owner = self._task_id_for_program(self.saved_project, pid)
            if owner is not None and owner != task_id:
                raise ValueError(f"Program {pid!r} is already scheduled on Task {owner!r}")
        updated = Task(task.task_id, task.priority, ordered, task.description)
        tasks = [
            updated if existing.task_id == task_id else existing
            for existing in self.saved_project.tasks
        ]
        self._replace_saved_tasks(tasks)
        return self._task_payload(updated)

    def schedule_status(self) -> dict[str, Any]:
        saved = self.project_dict
        applied = self.applied_project_dict
        return {
            "saved_applied": saved == applied,
            "saved_signature": saved.get("tasks", []),
            "applied_signature": applied.get("tasks", []),
        }

    def save_schedule(self) -> dict[str, Any]:
        self.persist_program()
        return {"saved": True, **self.schedule_status()}

    def apply_saved_schedule(self) -> dict[str, Any]:
        self.loader.restart_apply(_clone_project(self.saved_project))
        self._reapply_library_state()
        self._sync_applied_project_to_runtime(mode="restart")
        self._sync_scan_period_to_runtime()
        self._ensure_program_logs()
        self.persist_program()
        return {"applied": "restart", **self.schedule_status()}

    def persist_program(self) -> None:
        """Write project-of-record to ``program_path`` when configured."""
        if not self.program_path:
            return
        parent = os.path.dirname(self.program_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp_path = f"{self.program_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(self.persistence_dict, fh, indent=2)
            fh.write("\n")
        os.replace(tmp_path, self.program_path)


def make_handler(state: AppState) -> type[BaseHTTPRequestHandler]:
    """Return a handler class closed over *state*."""

    class Handler(BaseHTTPRequestHandler):
        log_message = lambda self, fmt, *args: None  # noqa: E731

        def _read_json(self) -> Any:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            return json.loads(body.decode())

        def _send_json(self, data: Any, status: int = 200) -> None:
            body = json.dumps(data, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_error_json(self, message: str, status: int = 400) -> None:
            self._send_json({"error": message}, status)

        def _send_html(self, html: str, status: int = 200) -> None:
            body = html.encode()
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _query(self) -> dict[str, list[str]]:
            return parse_qs(urlparse(self.path).query)

        def _program_id_from(self, data: Any | None = None) -> str | None:
            query = self._query()
            if query.get("id"):
                return query["id"][0]
            if isinstance(data, dict) and data.get("program_id"):
                return str(data["program_id"])
            return None

        def _program_path_parts(self) -> list[str] | None:
            path = urlparse(self.path).path.rstrip("/") or "/"
            if not path.startswith("/api/programs"):
                return None
            suffix = path[len("/api/programs") :].strip("/")
            if not suffix:
                return []
            return [unquote(part) for part in suffix.split("/")]

        def _task_path_parts(self) -> list[str] | None:
            path = urlparse(self.path).path.rstrip("/") or "/"
            if not path.startswith("/api/tasks"):
                return None
            suffix = path[len("/api/tasks") :].strip("/")
            if not suffix:
                return []
            return [unquote(part) for part in suffix.split("/")]

        def _library_path_parts(self) -> list[str] | None:
            path = urlparse(self.path).path.rstrip("/") or "/"
            if not path.startswith("/api/library"):
                return None
            suffix = path[len("/api/library") :].strip("/")
            if not suffix:
                return []
            return [unquote(part) for part in suffix.split("/")]

        def do_GET(self) -> None:
            path = urlparse(self.path).path.rstrip("/") or "/"
            try:
                if path == "/":
                    self._send_html(get_canvas_html())
                elif path == "/api/program":
                    self._send_json(state.program_dict_for(self._program_id_from()))
                elif path == "/api/programs":
                    self._send_json(state.program_cards())
                elif path == "/api/programs/unscheduled":
                    self._send_json(state.unscheduled_programs())
                elif path == "/api/tasks":
                    self._send_json(state.tasks_payload())
                elif path == "/api/schedule/status":
                    self._send_json(state.schedule_status())
                elif (parts := self._program_path_parts()) and len(parts) == 1:
                    self._send_json(state.program_dict_for(parts[0]))
                elif (parts := self._program_path_parts()) and len(parts) == 2 and parts[1] == "log":
                    self._send_json(state.program_logs_for(parts[0]))
                elif path == "/api/project":
                    self._send_json(state.project_dict)
                elif path == "/api/library":
                    self._send_json(state.library_payload(self._program_id_from()))
                elif (parts := self._library_path_parts()) and len(parts) == 2 and parts[0] in ("shipped", "custom"):
                    lib = "builtin" if parts[0] == "shipped" else "custom"
                    self._send_json(state.library_template(lib, parts[1]))
                elif path == "/api/runtime":
                    self._send_json(state.runtime_snapshot())
                else:
                    self._send_error_json("Not found", 404)
            except KeyError as exc:
                self._send_error_json(str(exc), 404)
            except Exception as exc:
                self._send_error_json(str(exc), 500)

        def do_PUT(self) -> None:
            path = urlparse(self.path).path.rstrip("/")
            try:
                if path == "/api/program":
                    data = self._read_json()
                    new_prog = program_from_dict(data)
                    try:
                        state._validate_program_equations(new_prog)
                    except ValueError as exc:
                        self._send_error_json(str(exc), 400)
                        return
                    pid = self._program_id_from(data)
                    state._set_program(pid, new_prog)
                    state.persist_program()
                    self._send_json(state.program_dict_for(pid))
                elif (parts := self._program_path_parts()) and len(parts) == 1:
                    data = self._read_json()
                    new_prog = program_from_dict(data)
                    try:
                        state._validate_program_equations(new_prog)
                    except ValueError as exc:
                        self._send_error_json(str(exc), 400)
                        return
                    state._set_program(parts[0], new_prog)
                    state.persist_program()
                    self._send_json(state.program_dict_for(parts[0]))
                elif (parts := self._program_path_parts()) and len(parts) == 2 and parts[1] == "meta":
                    data = self._read_json()
                    try:
                        self._send_json(
                            state.update_program_meta(
                                parts[0],
                                str(data.get("name", "")),
                                str(data.get("description", "")),
                            )
                        )
                    except ValueError as exc:
                        self._send_error_json(str(exc))
                        return
                elif path == "/api/project":
                    data = self._read_json()
                    new_project = project_from_dict(data)
                    mode = classify_project_apply(state.loader.project, new_project)
                    if mode == "hot":
                        state.loader.hot_apply(
                            new_project, superuser=state.superuser_hot_apply
                        )
                    else:
                        state.loader.restart_apply(new_project)
                    state._reapply_library_state()
                    state.saved_project = _clone_project(new_project)
                    state.persist_program()
                    # Same dual-loader sync as /api/apply (SWD-225).
                    state._sync_applied_project_to_runtime(mode=mode)
                    state._sync_scan_period_to_runtime()
                    self._send_json(state.project_dict)
                elif (parts := self._task_path_parts()) and len(parts) == 1:
                    data = self._read_json()
                    self._send_json(
                        state.update_task_meta(
                            parts[0],
                            new_id=data.get("id"),
                            priority=(
                                int(data["priority"]) if "priority" in data else None
                            ),
                            description=(
                                str(data["description"])
                                if "description" in data
                                else None
                            ),
                        )
                    )
                elif (parts := self._task_path_parts()) and len(parts) == 2 and parts[1] == "programs":
                    data = self._read_json()
                    raw_programs = data.get("programs", data)
                    if not isinstance(raw_programs, list):
                        raise ValueError("programs must be a list")
                    self._send_json(state.set_task_programs(parts[0], raw_programs))
                elif (parts := self._library_path_parts()) and len(parts) == 2 and parts[0] == "shipped":
                    data = self._read_json()
                    self._send_json(state.save_shipped_template(parts[1], data))
                elif (parts := self._library_path_parts()) and len(parts) == 2 and parts[0] == "custom":
                    data = self._read_json()
                    data["template_id"] = parts[1]
                    self._send_json(state.save_custom_template(data))
                else:
                    self._send_error_json("Not found", 404)
            except PermissionError as exc:
                pid = self._program_id_from() or state.main_program_id()
                if state.loader.project is not None and pid in state.loader.project.programs:
                    state.append_log(pid, "warning", str(exc))
                self._send_error_json(str(exc), 403)
            except (ValueError, KeyError) as exc:
                pid = self._program_id_from() or state.main_program_id()
                if state.loader.project is not None and pid in state.loader.project.programs:
                    state.append_log(pid, "error", str(exc))
                status = 404 if isinstance(exc, KeyError) else 400
                self._send_error_json(str(exc), status)
            except Exception as exc:
                self._send_error_json(str(exc), 500)

        def do_DELETE(self) -> None:
            path = urlparse(self.path).path
            try:
                prefix = "/api/library/user/"
                if path.startswith(prefix):
                    tid = path[len(prefix) :]
                    pid = self._program_id_from()
                    prog = state.program_for_id(pid)
                    if prog is None:
                        self._send_error_json("No program loaded", 400)
                        return
                    remove_user_template(prog, tid)
                    state.library.unregister("user", tid)
                    if pid is None:
                        pid = state.main_program_id()
                    state._sync_program_to_live(pid)
                    state.persist_program()
                    self._send_json({"deleted": tid})
                elif (parts := self._library_path_parts()) and len(parts) == 2 and parts[0] == "custom":
                    self._send_json(state.delete_custom_template(parts[1]))
                elif (parts := self._task_path_parts()) and len(parts) == 1:
                    self._send_json(state.delete_task(parts[0]))
                elif (parts := self._program_path_parts()) and len(parts) == 1:
                    self._send_json(state.delete_program(parts[0]))
                else:
                    self._send_error_json("Not found", 404)
            except KeyError as exc:
                self._send_error_json(str(exc), 404)
            except Exception as exc:
                self._send_error_json(str(exc), 500)

        def do_POST(self) -> None:
            path = urlparse(self.path).path.rstrip("/")
            try:
                if path == "/api/programs":
                    data = self._read_json()
                    self._send_json(
                        state.create_program(
                            str(data.get("name", "")),
                            str(data.get("description", "")),
                        ),
                        status=201,
                    )
                elif path == "/api/tasks":
                    data = self._read_json()
                    self._send_json(
                        state.create_task(
                            str(data.get("id", "")),
                            int(data.get("priority", 1)),
                            str(data.get("description", "")),
                        ),
                        status=201,
                    )
                elif path == "/api/schedule/save":
                    self._send_json(state.save_schedule())
                elif path == "/api/schedule/apply":
                    self._send_json(state.apply_saved_schedule())
                elif path == "/api/library/user":
                    self._handle_post_user_template()
                elif path == "/api/library/custom":
                    data = self._read_json()
                    if not isinstance(data, Mapping):
                        raise ValueError("template payload must be a mapping")
                    self._send_json(state.save_custom_template(data))
                elif (parts := self._library_path_parts()) and len(parts) == 3 and parts[0] == "shipped" and parts[2] == "reset":
                    self._send_json(state.reset_shipped_template(parts[1]))
                elif path == "/api/place":
                    self._handle_post_place()
                elif path == "/api/reset_instance":
                    self._handle_post_reset_instance()
                elif path == "/api/apply":
                    self._handle_post_apply()
                elif path == "/api/cmd":
                    self._handle_post_cmd()
                else:
                    self._send_error_json("Not found", 404)
            except PermissionError as exc:
                pid = self._program_id_from() or state.main_program_id()
                if state.loader.project is not None and pid in state.loader.project.programs:
                    state.append_log(pid, "warning", str(exc))
                self._send_error_json(str(exc), 403)
            except (ValueError, KeyError) as exc:
                pid = self._program_id_from() or state.main_program_id()
                if state.loader.project is not None and pid in state.loader.project.programs:
                    state.append_log(pid, "error", str(exc))
                status = 404 if isinstance(exc, KeyError) else 400
                self._send_error_json(str(exc), status)
            except Exception as exc:
                self._send_error_json(str(exc), 500)

        def _handle_post_cmd(self) -> None:
            data = self._read_json()
            name = str(data.get("name", ""))
            self._send_json(state.issue_cmd(name))

        def _handle_post_user_template(self) -> None:
            data = self._read_json()
            tid = str(data.get("template_id", ""))
            if not tid:
                self._send_error_json("template_id required")
                return
            tmpl = make_user_template(
                template_id=tid,
                body=str(data.get("body", "")),
                library=str(data.get("library", "user")),
                description=str(data.get("description", "")),
                pins=data.get("pins"),
                params=data.get("params"),
            )
            pid = self._program_id_from(data)
            prog = state.program_for_id(pid)
            if prog is None:
                self._send_error_json("No program loaded", 400)
                return
            add_user_template(prog, tmpl)
            state.library.register(tmpl)
            if pid is None:
                pid = state.main_program_id()
            state._sync_program_to_live(pid)
            state.persist_program()
            self._send_json(
                {"template_id": tmpl.template_id, "library": tmpl.library}
            )

        def _handle_post_place(self) -> None:
            data = self._read_json()
            pid = self._program_id_from(data)
            tid = str(data.get("template_id", ""))
            tlib = str(data.get("library", "builtin"))
            iid = str(
                data.get("instance_id")
                or f"{tid}_{len(state.program_dict_for(pid).get('instances', {}))}"
            )
            x = float(data.get("x", 0.0))
            y = float(data.get("y", 0.0))
            prog = state.program_for_id(pid)
            if prog is None:
                self._send_error_json("No program loaded", 400)
                return
            tmpl = state.resolve_template(pid, tlib, tid)
            if tmpl is None:
                self._send_error_json(f"Template {tlib!r}/{tid!r} not found", 404)
                return
            if iid in prog.instances:
                self._send_error_json(f"Instance {iid!r} already exists", 409)
                return
            inst = place_block(tmpl, iid, x=x, y=y)
            prog.instances[iid] = inst
            if iid not in prog.execution_order:
                prog.execution_order.append(iid)
            if pid is None:
                pid = state.main_program_id()
            state._sync_program_to_live(pid)
            state.persist_program()
            self._send_json(program_to_dict(prog))

        def _handle_post_reset_instance(self) -> None:
            data = self._read_json()
            pid = self._program_id_from(data)
            iid = str(data.get("instance_id", ""))
            prog = state.program_for_id(pid)
            if prog is None:
                self._send_error_json("No program loaded", 400)
                return
            inst = prog.instances.get(iid)
            if inst is None:
                self._send_error_json(f"Instance {iid!r} not found", 404)
                return
            tmpl = state.resolve_template(pid, inst.library, inst.template_id)
            if tmpl is None:
                self._send_error_json(
                    f"Template {inst.library!r}/{inst.template_id!r} not found", 404
                )
                return
            prog.instances[iid] = reset_instance(inst, tmpl)
            if pid is None:
                pid = state.main_program_id()
            state._sync_program_to_live(pid)
            state.persist_program()
            self._send_json(program_to_dict(prog))

        def _handle_post_apply(self) -> None:
            data = self._read_json()
            pid = self._program_id_from(data) or state.main_program_id()
            mode = str(data.get("mode", "restart")).lower()
            proj = _clone_project(state.saved_project)
            if mode == "restart":
                state.loader.restart_apply(proj)
                state._reapply_library_state()
                # Live MQTT Skid must run the same applied project (SWD-225).
                state._sync_applied_project_to_runtime(mode="restart")
                state._sync_scan_period_to_runtime()
                state.persist_program()
                state.append_log(pid, "info", "Applied with restart")
                self._send_json({"applied": "restart"})
            elif mode == "hot":
                state.loader.hot_apply(proj, superuser=state.superuser_hot_apply)
                state._reapply_library_state()
                state._sync_applied_project_to_runtime(mode="hot")
                state._sync_scan_period_to_runtime()
                state.persist_program()
                state.append_log(pid, "info", "Hot apply succeeded")
                self._send_json({"applied": "hot"})
            else:
                self._send_error_json(f"Unknown mode {mode!r}")

    return Handler


def run_app(
    host: str = "127.0.0.1",
    port: int = 8099,
    initial_program: dict[str, Any] | None = None,
    *,
    state: AppState | None = None,
    program_path: str | None = None,
) -> HTTPServer:
    """Create the App HTTP server (caller runs ``serve_forever``)."""
    if state is None:
        state = AppState(initial_program, program_path=program_path)
    handler = make_handler(state)
    return HTTPServer((host, port), handler)


__all__ = [
    "AppState",
    "make_handler",
    "run_app",
]
