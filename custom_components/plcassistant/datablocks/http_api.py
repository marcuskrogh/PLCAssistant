"""HTTP API + UI for Datablock configuration (SWD-184).

Requires ``homeassistant`` — unit tests must not import this module.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from plcassistant.io.datablock import (
    datablock_from_dict,
    datablock_to_dict,
    program_accessible_tags,
)

from ..const import CONF_BINDINGS, DOMAIN
from .store import (
    binding_rows_from_store,
    catalog_from_store,
    load_store,
    save_store,
)

_LOGGER = logging.getLogger(__name__)
_UI_REGISTERED = False


def _config_root(hass: HomeAssistant) -> Path:
    return Path(hass.config.path())


def _editor_html() -> str:
    path = Path(__file__).resolve().parent.parent / "www" / "datablock_editor.html"
    return path.read_text(encoding="utf-8")


def _first_entry(hass: HomeAssistant) -> ConfigEntry | None:
    entries = list(hass.config_entries.async_entries(DOMAIN))
    return entries[0] if entries else None


async def async_setup_datablock_api(hass: HomeAssistant) -> None:
    """Register Datablock HTTP views once and seed the store."""
    global _UI_REGISTERED
    root = _config_root(hass)
    try:
        await hass.async_add_executor_job(load_store, root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _LOGGER.warning("PLCAssistant: could not seed datablocks store (%s)", exc)

    if _UI_REGISTERED:
        return
    hass.http.register_view(DatablockEditorView)
    hass.http.register_view(DatablockCatalogView)
    hass.http.register_view(DatablockItemView)
    hass.http.register_view(DatablockAccessView)
    hass.http.register_view(DatablockApplyView)
    _UI_REGISTERED = True
    _LOGGER.info("PLCAssistant: Datablock configuration API registered")


def _json_error(message: str, status: int = 400) -> web.Response:
    return web.json_response({"ok": False, "error": message}, status=status)


class DatablockEditorView(HomeAssistantView):
    """Serve the Datablock configuration panel SPA.

    ``requires_auth`` is False so a Lovelace iframe can load the shell.
    Mutating/data APIs stay authenticated; the SPA prefers ``parent.hass.callApi``.
    """

    url = "/api/plcassistant/datablocks/ui"
    name = "api:plcassistant:datablocks:ui"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        try:
            html = await request.app["hass"].async_add_executor_job(_editor_html)
        except OSError as exc:
            return web.Response(text=f"editor missing: {exc}", status=500)
        return web.Response(text=html, content_type="text/html")


class DatablockCatalogView(HomeAssistantView):
    """List Datablocks + program access."""

    url = "/api/plcassistant/datablocks"
    name = "api:plcassistant:datablocks"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        try:
            payload = await hass.async_add_executor_job(load_store, _config_root(hass))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return _json_error(str(exc), 500)
        catalog = catalog_from_store(payload)
        return web.json_response(
            {
                "ok": True,
                "datablocks": [
                    datablock_to_dict(block) for block in catalog.datablocks.values()
                ],
                "program_access": payload.get("program_access") or {},
            }
        )

    async def post(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return _json_error("invalid JSON")
        if not isinstance(body, dict):
            return _json_error("payload must be an object")
        try:
            block = datablock_from_dict(body)
            payload = await hass.async_add_executor_job(load_store, _config_root(hass))
            catalog = catalog_from_store(payload)
            if catalog.get(block.datablock_id) is not None:
                return _json_error(
                    f"Datablock {block.datablock_id!r} already exists", 409
                )
            catalog.upsert(block)
            payload["datablocks"] = catalog.to_dict()["datablocks"]
            await hass.async_add_executor_job(save_store, _config_root(hass), payload)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return _json_error(str(exc))
        return web.json_response({"ok": True, "datablock": datablock_to_dict(block)})


class DatablockItemView(HomeAssistantView):
    """Update / delete one Datablock."""

    url = "/api/plcassistant/datablocks/{datablock_id}"
    name = "api:plcassistant:datablocks:item"
    requires_auth = True

    async def put(self, request: web.Request, datablock_id: str) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return _json_error("invalid JSON")
        try:
            block = datablock_from_dict(body, datablock_id=datablock_id)
            payload = await hass.async_add_executor_job(load_store, _config_root(hass))
            catalog = catalog_from_store(payload)
            if catalog.get(datablock_id) is None:
                return _json_error(f"Datablock {datablock_id!r} not found", 404)
            catalog.upsert(block)
            payload["datablocks"] = catalog.to_dict()["datablocks"]
            await hass.async_add_executor_job(save_store, _config_root(hass), payload)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return _json_error(str(exc))
        return web.json_response({"ok": True, "datablock": datablock_to_dict(block)})

    async def delete(self, request: web.Request, datablock_id: str) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        try:
            payload = await hass.async_add_executor_job(load_store, _config_root(hass))
            catalog = catalog_from_store(payload)
            catalog.delete(datablock_id)
            access = dict(payload.get("program_access") or {})
            for pid, dbs in list(access.items()):
                access[pid] = [d for d in dbs if d != datablock_id]
            payload["datablocks"] = catalog.to_dict()["datablocks"]
            payload["program_access"] = access
            await hass.async_add_executor_job(save_store, _config_root(hass), payload)
        except KeyError as exc:
            return _json_error(str(exc), 404)
        except (OSError, ValueError, TypeError) as exc:
            return _json_error(str(exc))
        return web.json_response({"ok": True, "deleted": datablock_id})


class DatablockAccessView(HomeAssistantView):
    """Program ↔ Datablock access map (HA source of truth for assignment).

    Soft-PLC ``Program.datablocks`` should mirror this map (demo ships aligned).
    """

    url = "/api/plcassistant/datablocks/access"
    name = "api:plcassistant:datablocks:access"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        try:
            payload = await hass.async_add_executor_job(load_store, _config_root(hass))
            catalog = catalog_from_store(payload)
            access = payload.get("program_access") or {}
            resolved = {
                pid: sorted(program_accessible_tags(catalog, dbs))
                for pid, dbs in access.items()
            }
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return _json_error(str(exc), 500)
        return web.json_response(
            {"ok": True, "program_access": access, "resolved_tags": resolved}
        )

    async def put(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return _json_error("invalid JSON")
        access = body.get("program_access") if isinstance(body, dict) else None
        if not isinstance(access, dict):
            return _json_error("'program_access' mapping required")
        try:
            payload = await hass.async_add_executor_job(load_store, _config_root(hass))
            catalog = catalog_from_store(payload)
            cleaned: dict[str, list[str]] = {}
            for pid, dbs in access.items():
                if not isinstance(dbs, list):
                    raise ValueError(f"access for {pid!r} must be a list")
                ids = [str(x) for x in dbs]
                # Validate ids exist (empty access allowed).
                if ids:
                    catalog.tag_names_for(ids)
                cleaned[str(pid)] = ids
            payload["program_access"] = cleaned
            await hass.async_add_executor_job(save_store, _config_root(hass), payload)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return _json_error(str(exc))
        return web.json_response({"ok": True, "program_access": cleaned})


class DatablockApplyView(HomeAssistantView):
    """Apply store bindings into CONF_BINDINGS and reload the config entry."""

    url = "/api/plcassistant/datablocks/apply"
    name = "api:plcassistant:datablocks:apply"
    requires_auth = True

    async def post(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        try:
            payload = await hass.async_add_executor_job(load_store, _config_root(hass))
            rows = binding_rows_from_store(payload)
            hass.data.setdefault(DOMAIN, {})
            hass.data[DOMAIN]["datablock_bindings"] = rows
            hass.data[DOMAIN]["datablock_store"] = payload
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return _json_error(str(exc))

        entry = _first_entry(hass)
        if entry is None:
            return _json_error("no PLCAssistant config entry", 404)

        new_data = {**dict(entry.data), CONF_BINDINGS: rows}
        bindings_unchanged = entry.data.get(CONF_BINDINGS) == rows
        hass.config_entries.async_update_entry(entry, data=new_data)
        # Listener reloads when data changes; re-apply same bindings must still
        # rebuild platforms from the updated store on disk (Dynamics pattern).
        if bindings_unchanged:
            await hass.config_entries.async_reload(entry.entry_id)
        return web.json_response(
            {"ok": True, "bindings": rows, "count": len(rows), "reloaded": True}
        )


__all__ = ["async_setup_datablock_api"]
