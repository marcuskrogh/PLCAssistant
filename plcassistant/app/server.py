"""Stdlib http.server-based App for the block program editor (SWD-120).

Endpoints
---------
GET  /                      Visual canvas (HTML/JS)
GET  /api/program           Current program as JSON dict
PUT  /api/program           Replace program; body = JSON dict; returns new program dict
GET  /api/library           All templates (builtin + user) as JSON list
POST /api/library/user      Create/update a user template; body = template JSON
DELETE /api/library/user/<tid>  Delete a user template
POST /api/place             Place a block; body = {template_id, library, instance_id, x?, y?}
POST /api/reset_instance    Reset instance params to library defaults; body = {instance_id}
POST /api/apply             Apply program; body = {mode: "restart"|"hot"}
                            (hot requires PLCASSISTANT_SUPERUSER_HOT_APPLY=1;
                             client "superuser" field is ignored)

The server holds an in-memory program and a ProgramLoader.  No file persistence
by default; callers may pass an initial program dict.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse

from plcassistant.app._canvas import get_canvas_html
from plcassistant.surface.apply import ProgramLoader
from plcassistant.surface.builtin import register_builtins
from plcassistant.surface.model import TemplateLibrary
from plcassistant.surface.runtime import BlockRuntime
from plcassistant.surface.schema import (
    place_block,
    program_from_dict,
    program_to_dict,
    reset_instance,
)
from plcassistant.surface.user_library import (
    add_user_template,
    list_user_templates,
    make_user_template,
    remove_user_template,
)


def _make_loader() -> tuple[ProgramLoader, TemplateLibrary, BlockRuntime]:
    library = TemplateLibrary()
    runtime = BlockRuntime(library)
    register_builtins(library, runtime)
    loader = ProgramLoader(library, runtime)
    return loader, library, runtime


_ENV_HOT_APPLY = "PLCASSISTANT_SUPERUSER_HOT_APPLY"


class AppState:
    """Mutable shared state for one App server instance."""

    def __init__(
        self,
        initial_program: dict[str, Any] | None = None,
        *,
        program_path: str | None = None,
    ) -> None:
        self.loader, self.library, self.runtime = _make_loader()
        # Server-side hot-apply authority: read env var once at startup.
        self.superuser_hot_apply: bool = (
            os.environ.get(_ENV_HOT_APPLY, "") == "1"
        )
        self.program_path = program_path
        loaded: dict[str, Any] | None = initial_program
        if loaded is None and program_path and os.path.isfile(program_path):
            with open(program_path, encoding="utf-8") as fh:
                loaded = json.load(fh)
        if loaded is not None:
            self.loader.load(program_from_dict(loaded))
        else:
            self.loader.load(
                program_from_dict(
                    {
                        "version": "1.0",
                        "instances": {},
                        "wires": [],
                        "execution_order": [],
                    }
                )
            )

    @property
    def program_dict(self) -> dict[str, Any]:
        prog = self.loader.program
        if prog is None:
            return {"version": "1.0", "instances": {}, "wires": [], "execution_order": []}
        return program_to_dict(prog)

    def persist_program(self) -> None:
        """Write program-of-record to ``program_path`` when configured (App /data)."""
        if not self.program_path:
            return
        parent = os.path.dirname(self.program_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self.program_path, "w", encoding="utf-8") as fh:
            json.dump(self.program_dict, fh, indent=2)
            fh.write("\n")


def make_handler(state: AppState) -> type[BaseHTTPRequestHandler]:
    """Return a handler class closed over *state*."""

    class Handler(BaseHTTPRequestHandler):
        log_message = lambda self, fmt, *args: None  # silence access logs

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

        # ── GET routing ──────────────────────────────────────────────────

        def do_GET(self) -> None:
            path = urlparse(self.path).path.rstrip("/") or "/"
            try:
                if path == "/":
                    self._send_html(get_canvas_html())
                elif path == "/api/program":
                    self._send_json(state.program_dict)
                elif path == "/api/library":
                    templates = state.library.all_templates()
                    self._send_json([
                        {
                            "template_id": t.template_id,
                            "library": t.library,
                            "description": t.description,
                            "pins": [
                                {
                                    "name": p.name,
                                    "direction": p.direction.value,
                                    "data_type": p.data_type,
                                    **({"default": p.default} if p.default is not None else {}),
                                }
                                for p in t.pins
                            ],
                            "params": t.params,
                            "body": t.body,
                            "is_builtin": t.is_builtin,
                        }
                        for t in templates
                    ])
                else:
                    self._send_error_json("Not found", 404)
            except Exception as exc:
                self._send_error_json(str(exc), 500)

        # ── PUT routing ──────────────────────────────────────────────────

        def do_PUT(self) -> None:
            path = urlparse(self.path).path.rstrip("/")
            try:
                if path == "/api/program":
                    data = self._read_json()
                    new_prog = program_from_dict(data)
                    state.loader.restart_apply(new_prog)
                    state.persist_program()
                    self._send_json(state.program_dict)
                else:
                    self._send_error_json("Not found", 404)
            except (ValueError, KeyError) as exc:
                self._send_error_json(str(exc))
            except Exception as exc:
                self._send_error_json(str(exc), 500)

        # ── DELETE routing ───────────────────────────────────────────────

        def do_DELETE(self) -> None:
            path = urlparse(self.path).path
            try:
                prefix = "/api/library/user/"
                if path.startswith(prefix):
                    tid = path[len(prefix):]
                    prog = state.loader.program
                    if prog is None:
                        self._send_error_json("No program loaded", 400)
                        return
                    remove_user_template(prog, tid)
                    state.library.unregister("user", tid)
                    self._send_json({"deleted": tid})
                else:
                    self._send_error_json("Not found", 404)
            except KeyError as exc:
                self._send_error_json(str(exc), 404)
            except Exception as exc:
                self._send_error_json(str(exc), 500)

        # ── POST routing ─────────────────────────────────────────────────

        def do_POST(self) -> None:
            path = urlparse(self.path).path.rstrip("/")
            try:
                if path == "/api/library/user":
                    self._handle_post_user_template()
                elif path == "/api/place":
                    self._handle_post_place()
                elif path == "/api/reset_instance":
                    self._handle_post_reset_instance()
                elif path == "/api/apply":
                    self._handle_post_apply()
                else:
                    self._send_error_json("Not found", 404)
            except PermissionError as exc:
                self._send_error_json(str(exc), 403)
            except (ValueError, KeyError) as exc:
                self._send_error_json(str(exc))
            except Exception as exc:
                self._send_error_json(str(exc), 500)

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
            prog = state.loader.program
            if prog is None:
                self._send_error_json("No program loaded", 400)
                return
            add_user_template(prog, tmpl)
            state.library.register(tmpl)
            self._send_json({
                "template_id": tmpl.template_id,
                "library": tmpl.library,
            })

        def _handle_post_place(self) -> None:
            data = self._read_json()
            tid = str(data.get("template_id", ""))
            tlib = str(data.get("library", "builtin"))
            iid = str(data.get("instance_id") or f"{tid}_{len(state.program_dict.get('instances',{}))}")
            x = float(data.get("x", 0.0))
            y = float(data.get("y", 0.0))
            tmpl = state.library.get(tlib, tid)
            if tmpl is None:
                prog = state.loader.program
                tmpl = (prog.user_templates or {}).get(tid) if prog else None
            if tmpl is None:
                self._send_error_json(f"Template {tlib!r}/{tid!r} not found", 404)
                return
            prog = state.loader.program
            if prog is None:
                self._send_error_json("No program loaded", 400)
                return
            inst = place_block(tmpl, iid, x=x, y=y)
            prog.instances[iid] = inst
            if iid not in prog.execution_order:
                prog.execution_order.append(iid)
            self._send_json(program_to_dict(prog))

        def _handle_post_reset_instance(self) -> None:
            data = self._read_json()
            iid = str(data.get("instance_id", ""))
            prog = state.loader.program
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
            self._send_json(program_to_dict(prog))

        def _handle_post_apply(self) -> None:
            data = self._read_json()
            mode = str(data.get("mode", "restart")).lower()
            # Client-supplied "superuser" field is intentionally ignored.
            # Authority comes solely from the server-side flag set at startup.
            prog = state.loader.program
            if prog is None:
                self._send_error_json("No program loaded", 400)
                return
            if mode == "restart":
                state.loader.restart_apply(prog)
                self._send_json({"applied": "restart"})
            elif mode == "hot":
                state.loader.hot_apply(prog, superuser=state.superuser_hot_apply)
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
    """Create and start the App HTTP server.

    Returns the ``HTTPServer`` instance (already started via ``serve_forever``
    in a thread when called from ``__main__``).
    For testing call ``server.handle_request()`` directly.
    """
    if state is None:
        state = AppState(initial_program, program_path=program_path)
    handler = make_handler(state)
    server = HTTPServer((host, port), handler)
    return server


__all__ = [
    "AppState",
    "make_handler",
    "run_app",
]
