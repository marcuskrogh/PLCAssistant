"""Stdlib http.server-based App for the operator dashboard + block editor.

Endpoints
---------
GET  /                      Operator dashboard + program editor (HTML/JS)
GET  /api/program           Main scheduled program as JSON dict (canvas)
PUT  /api/program           Replace Main program; body = JSON dict
GET  /api/project           Soft-PLC project tree (Tasks + Programs)
PUT  /api/project           Replace project tree; structure → restart apply
GET  /api/library           All templates (builtin + user) as JSON list
POST /api/library/user      Create/update a user template; body = template JSON
DELETE /api/library/user/<tid>  Delete a user template
POST /api/place             Place a block; body = {template_id, library, instance_id, x?, y?}
POST /api/reset_instance    Reset instance params to library defaults; body = {instance_id}
POST /api/apply             Apply program; body = {mode: "restart"|"hot"}
                            (hot requires PLCASSISTANT_SUPERUSER_HOT_APPLY=1;
                             client "superuser" field is ignored)
GET  /api/runtime           Live Soft-PLC status + tag snapshot
POST /api/cmd               Operator command; body = {name: "start"|"stop"|"reset"}

The server holds an in-memory project and a ProjectLoader.  No file persistence
by default; callers may pass an initial project or legacy program dict.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from plcassistant.app._canvas import get_canvas_html
from plcassistant.app.operator_runtime import OperatorRuntime
from plcassistant.io.mqtt_topics import DEFAULT_INSTANCE_ID
from plcassistant.surface.apply import ProjectLoader
from plcassistant.surface.builtin import register_builtins, wedge_softplc_project
from plcassistant.surface.model import Program, SoftPlcProject, Task, TemplateLibrary
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
        if loaded is not None:
            try:
                self.loader.load(project_from_dict(loaded))
            except (ValueError, KeyError, TypeError):
                self.loader.load(project_from_dict(default_project))
        else:
            self.loader.load(project_from_dict(default_project))
        self._ensure_program_logs()
        if "tank" in self.program_logs and not self.program_logs["tank"]:
            self.append_log("tank", "info", "Program Tank loaded")

    def _sync_scan_period_to_runtime(self) -> None:
        """Propagate project ``scan_period_s`` into the live MQTT scan loop."""
        proj = self.loader.project
        if proj is None:
            return
        loop = self.operator._scan_loop()
        if loop is not None and hasattr(loop, "set_scan_period_s"):
            loop.set_scan_period_s(proj.scan_period_s)

    @property
    def instance_id(self) -> str:
        return self.operator.instance_id

    @instance_id.setter
    def instance_id(self, value: str) -> None:
        self.operator.instance_id = str(value) if value else DEFAULT_INSTANCE_ID

    def attach_runtime(self, lifecycle: Any) -> None:
        """Attach MQTT scan lifecycle so the UI can read tags and issue cmds."""
        self.operator.attach(lifecycle)
        loop = self.operator._scan_loop()
        if loop is not None:
            self._sync_scan_period_to_runtime()
        elif hasattr(lifecycle, "set_on_attach"):
            lifecycle.set_on_attach(lambda _loop: self._sync_scan_period_to_runtime())

    def runtime_snapshot(self) -> dict[str, Any]:
        """JSON-serialisable Soft-PLC status for the operator dashboard."""
        return self.operator.snapshot()

    def issue_cmd(self, name: str) -> dict[str, Any]:
        """Start / stop / reset via scan loop (enqueued), or defer while offline."""
        return self.operator.issue_cmd(name)

    @property
    def project_dict(self) -> dict[str, Any]:
        proj = self.loader.project
        if proj is None:
            return project_to_dict(project_from_dict(wedge_softplc_project()))
        return project_to_dict(proj)

    @property
    def program_dict(self) -> dict[str, Any]:
        return self.program_dict_for(None)

    def main_program_id(self) -> str:
        proj = self.loader.project
        if proj is None:
            return "main"
        return self.loader._main_program_id(proj)

    def program_for_id(self, program_id: str | None) -> Program | None:
        proj = self.loader.project
        if proj is None:
            return None
        pid = program_id or self.main_program_id()
        if pid not in proj.programs:
            raise KeyError(f"Program {pid!r} not found")
        return proj.programs[pid]

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
        """Replace the selected program in the active project."""
        pid = program_id or self.main_program_id()
        self.loader.replace_program(pid, new_prog, restart=True)

    def _ensure_program_logs(self) -> None:
        proj = self.loader.project
        if proj is None:
            return
        for pid in proj.programs:
            self.program_logs.setdefault(pid, [])
        for pid in list(self.program_logs):
            if pid not in proj.programs:
                self.program_logs.pop(pid, None)

    def append_log(self, program_id: str, level: str, message: str) -> None:
        self.program_logs.setdefault(program_id, []).append(
            {"ts": _now_ts(), "level": level, "message": message}
        )

    def program_logs_for(self, program_id: str) -> list[dict[str, str]]:
        self._ensure_program_logs()
        if self.loader.project is None or program_id not in self.loader.project.programs:
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
        proj = self.loader.project
        if proj is None or program_id not in proj.programs:
            raise KeyError(f"Program {program_id!r} not found")
        prog = proj.programs[program_id]
        logs = self.program_logs.get(program_id, [])
        task_id = self._task_id_for_program(proj, program_id)
        return {
            "id": program_id,
            "name": prog.name or program_id,
            "description": prog.description,
            "status": program_run_status(proj, program_id, self._softplc_running()),
            "health": health_from_log(logs),
            "task_id": task_id,
        }

    def program_cards(self) -> list[dict[str, Any]]:
        self._ensure_program_logs()
        proj = self.loader.project
        if proj is None:
            return []
        return [self.program_card(pid) for pid in proj.programs]

    def create_program(self, name: str, description: str = "") -> dict[str, Any]:
        clean_name = str(name).strip()
        if not clean_name:
            raise ValueError("name required")
        proj = self.loader.project or project_from_dict(wedge_softplc_project())
        base = _slugify_program_id(clean_name)
        pid = base
        suffix = 2
        while pid in proj.programs:
            pid = f"{base}-{suffix}"
            suffix += 1
        programs = dict(proj.programs)
        programs[pid] = Program(name=clean_name, description=str(description or ""))
        new_project = SoftPlcProject(
            programs=programs,
            tasks=list(proj.tasks),
            scan_period_s=proj.scan_period_s,
            version=proj.version,
        )
        self.loader.restart_apply(new_project)
        self._ensure_program_logs()
        self.append_log(pid, "info", f"Program {clean_name} created")
        self.persist_program()
        return self.program_card(pid)

    def update_program_meta(self, program_id: str, name: str, description: str = "") -> dict[str, Any]:
        prog = self.program_for_id(program_id)
        if prog is None:
            raise KeyError(f"Program {program_id!r} not found")
        prog.name = str(name).strip()
        prog.description = str(description or "")
        self.persist_program()
        self.append_log(program_id, "info", "Program settings saved")
        return self.program_card(program_id)

    def delete_program(self, program_id: str) -> dict[str, Any]:
        proj = self.loader.project
        if proj is None or program_id not in proj.programs:
            raise KeyError(f"Program {program_id!r} not found")
        programs = dict(proj.programs)
        programs.pop(program_id)
        tasks = [
            Task(task.task_id, task.priority, [pid for pid in task.programs if pid != program_id])
            for task in proj.tasks
        ]
        new_project = SoftPlcProject(
            programs=programs,
            tasks=tasks,
            scan_period_s=proj.scan_period_s,
            version=proj.version,
        )
        self.loader.restart_apply(new_project)
        self.program_logs.pop(program_id, None)
        self._ensure_program_logs()
        self.persist_program()
        return {"deleted": program_id}

    def persist_program(self) -> None:
        """Write project-of-record to ``program_path`` when configured."""
        if not self.program_path:
            return
        parent = os.path.dirname(self.program_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp_path = f"{self.program_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(self.project_dict, fh, indent=2)
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
            return [] if not suffix else suffix.split("/")

        def do_GET(self) -> None:
            path = urlparse(self.path).path.rstrip("/") or "/"
            try:
                if path == "/":
                    self._send_html(get_canvas_html())
                elif path == "/api/program":
                    self._send_json(state.program_dict_for(self._program_id_from()))
                elif path == "/api/programs":
                    self._send_json(state.program_cards())
                elif (parts := self._program_path_parts()) and len(parts) == 1:
                    self._send_json(state.program_dict_for(parts[0]))
                elif (parts := self._program_path_parts()) and len(parts) == 2 and parts[1] == "log":
                    self._send_json(state.program_logs_for(parts[0]))
                elif path == "/api/project":
                    self._send_json(state.project_dict)
                elif path == "/api/library":
                    templates = state.library.all_templates()
                    self._send_json(
                        [
                            {
                                "template_id": t.template_id,
                                "library": t.library,
                                "description": t.description,
                                "pins": [
                                    {
                                        "name": p.name,
                                        "direction": p.direction.value,
                                        "data_type": p.data_type,
                                        **(
                                            {"default": p.default}
                                            if p.default is not None
                                            else {}
                                        ),
                                    }
                                    for p in t.pins
                                ],
                                "params": t.params,
                                "body": t.body,
                                "is_builtin": t.is_builtin,
                            }
                            for t in templates
                        ]
                    )
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
                    pid = self._program_id_from(data)
                    state._set_program(pid, new_prog)
                    state.persist_program()
                    self._send_json(state.program_dict_for(pid))
                elif (parts := self._program_path_parts()) and len(parts) == 1:
                    data = self._read_json()
                    new_prog = program_from_dict(data)
                    state._set_program(parts[0], new_prog)
                    state.persist_program()
                    self._send_json(state.program_dict_for(parts[0]))
                elif (parts := self._program_path_parts()) and len(parts) == 2 and parts[1] == "meta":
                    data = self._read_json()
                    self._send_json(
                        state.update_program_meta(
                            parts[0],
                            str(data.get("name", "")),
                            str(data.get("description", "")),
                        )
                    )
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
                    state.persist_program()
                    state._sync_scan_period_to_runtime()
                    self._send_json(state.project_dict)
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
                    state.persist_program()
                    self._send_json({"deleted": tid})
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
                elif path == "/api/library/user":
                    self._handle_post_user_template()
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
            tmpl = state.library.get(tlib, tid)
            if tmpl is None:
                prog = state.program_for_id(pid)
                tmpl = (prog.user_templates or {}).get(tid) if prog else None
            if tmpl is None:
                self._send_error_json(f"Template {tlib!r}/{tid!r} not found", 404)
                return
            prog = state.program_for_id(pid)
            if prog is None:
                self._send_error_json("No program loaded", 400)
                return
            inst = place_block(tmpl, iid, x=x, y=y)
            prog.instances[iid] = inst
            if iid not in prog.execution_order:
                prog.execution_order.append(iid)
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
            tmpl = state.library.get(inst.library, inst.template_id)
            if tmpl is None:
                tmpl = (prog.user_templates or {}).get(inst.template_id)
            if tmpl is None:
                self._send_error_json(
                    f"Template {inst.library!r}/{inst.template_id!r} not found", 404
                )
                return
            prog.instances[iid] = reset_instance(inst, tmpl)
            state.persist_program()
            self._send_json(program_to_dict(prog))

        def _handle_post_apply(self) -> None:
            data = self._read_json()
            pid = self._program_id_from(data) or state.main_program_id()
            mode = str(data.get("mode", "restart")).lower()
            proj = state.loader.project
            if proj is None:
                self._send_error_json("No project loaded", 400)
                return
            if mode == "restart":
                state.loader.restart_apply(proj)
                state.persist_program()
                state.append_log(pid, "info", "Applied with restart")
                self._send_json({"applied": "restart"})
            elif mode == "hot":
                state.loader.hot_apply(proj, superuser=state.superuser_hot_apply)
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
