"""HTTP API + UI for the dynamics block editor (SWD-166).

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

from ..const import (
    CONF_DYNAMICS_PARAMS,
    CONF_DYNAMICS_PRESET,
    DOMAIN,
)
from .registry import add_model_dir, get_preset, list_presets
from .store import (
    catalog_payload,
    list_user_models,
    load_user_model,
    save_user_model,
    seed_skid_composed,
    validate_document,
)

_LOGGER = logging.getLogger(__name__)

_UI_REGISTERED = False


def _config_root(hass: HomeAssistant) -> Path:
    return Path(hass.config.path())


def _bundled_skid_composed() -> Path:
    return Path(__file__).resolve().parent / "models" / "skid_composed.json"


def _editor_html() -> str:
    path = Path(__file__).resolve().parent.parent / "www" / "dynamics_editor.html"
    return path.read_text(encoding="utf-8")


async def async_setup_dynamics_api(hass: HomeAssistant) -> None:
    """Register HTTP views once and seed the user models directory."""
    global _UI_REGISTERED
    root = _config_root(hass)
    add_model_dir(root / "plcassistant" / "models")
    try:
        seed_skid_composed(root, _bundled_skid_composed())
    except OSError as exc:
        _LOGGER.warning("PLCAssistant: could not seed skid_composed model (%s)", exc)

    if _UI_REGISTERED:
        return
    hass.http.register_view(DynamicsEditorView)
    hass.http.register_view(DynamicsCatalogView)
    hass.http.register_view(DynamicsModelView)
    hass.http.register_view(DynamicsValidateView)
    hass.http.register_view(DynamicsSaveView)
    hass.http.register_view(DynamicsApplyView)
    hass.http.register_view(DynamicsPresetsView)
    _UI_REGISTERED = True
    _LOGGER.info("PLCAssistant: dynamics editor API registered")


def _json_error(message: str, status: int = 400) -> web.Response:
    return web.json_response({"ok": False, "error": message}, status=status)


def _first_entry(hass: HomeAssistant) -> ConfigEntry | None:
    entries = list(hass.config_entries.async_entries(DOMAIN))
    return entries[0] if entries else None


class DynamicsEditorView(HomeAssistantView):
    """Serve the block-like dynamics editor SPA."""

    url = "/api/plcassistant/dynamics/ui"
    name = "api:plcassistant:dynamics:ui"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        try:
            html = await request.app["hass"].async_add_executor_job(_editor_html)
        except OSError as exc:
            return web.Response(text=f"editor missing: {exc}", status=500)
        return web.Response(text=html, content_type="text/html")


class DynamicsCatalogView(HomeAssistantView):
    url = "/api/plcassistant/dynamics/catalog"
    name = "api:plcassistant:dynamics:catalog"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        return web.json_response(catalog_payload())


class DynamicsPresetsView(HomeAssistantView):
    url = "/api/plcassistant/dynamics/presets"
    name = "api:plcassistant:dynamics:presets"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        root = _config_root(hass)
        return web.json_response(
            {
                "presets": list(list_presets()),
                "user_models": list_user_models(root),
            }
        )


class DynamicsModelView(HomeAssistantView):
    url = "/api/plcassistant/dynamics/model"
    name = "api:plcassistant:dynamics:model"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        name = request.query.get("name") or "skid_composed"
        root = _config_root(hass)

        def _load() -> dict[str, Any]:
            try:
                return load_user_model(root, name)
            except FileNotFoundError:
                bundled = _bundled_skid_composed()
                if name == "skid_composed" and bundled.is_file():
                    return json.loads(bundled.read_text(encoding="utf-8"))
                raise

        try:
            doc = await hass.async_add_executor_job(_load)
        except FileNotFoundError:
            return _json_error(f"model not found: {name}", 404)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            return _json_error(str(exc))
        return web.json_response({"ok": True, "document": doc})


class DynamicsValidateView(HomeAssistantView):
    url = "/api/plcassistant/dynamics/validate"
    name = "api:plcassistant:dynamics:validate"
    requires_auth = True

    async def post(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return _json_error("invalid JSON body")
        doc = body.get("document") if isinstance(body, dict) else None
        if not isinstance(doc, dict):
            return _json_error("document object required")
        try:
            validated = validate_document(doc)
        except ValueError as exc:
            return _json_error(str(exc))
        return web.json_response({"ok": True, "document": validated})


class DynamicsSaveView(HomeAssistantView):
    url = "/api/plcassistant/dynamics/save"
    name = "api:plcassistant:dynamics:save"
    requires_auth = True

    async def post(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return _json_error("invalid JSON body")
        if not isinstance(body, dict):
            return _json_error("object body required")
        name = body.get("name") or (body.get("document") or {}).get("name")
        doc = body.get("document")
        if not isinstance(doc, dict):
            return _json_error("document object required")
        root = _config_root(hass)

        def _save() -> str:
            path = save_user_model(root, str(name), doc)
            return str(path)

        try:
            path = await hass.async_add_executor_job(_save)
        except ValueError as exc:
            return _json_error(str(exc))
        except OSError as exc:
            return _json_error(f"save failed: {exc}", 500)
        return web.json_response({"ok": True, "path": path, "name": str(name).lower()})


class DynamicsApplyView(HomeAssistantView):
    """Save model, set config-entry preset, reload entry (rebuild plant)."""

    url = "/api/plcassistant/dynamics/apply"
    name = "api:plcassistant:dynamics:apply"
    requires_auth = True

    async def post(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return _json_error("invalid JSON body")
        if not isinstance(body, dict):
            return _json_error("object body required")
        name = str(body.get("name") or (body.get("document") or {}).get("name") or "").strip()
        doc = body.get("document")
        if not name:
            return _json_error("name required")
        if not isinstance(doc, dict):
            return _json_error("document object required")
        root = _config_root(hass)

        def _save() -> str:
            path = save_user_model(root, name, doc)
            # Ensure registry can load it before reload.
            get_preset(name)
            return str(path)

        try:
            path = await hass.async_add_executor_job(_save)
        except (ValueError, KeyError) as exc:
            return _json_error(str(exc))
        except OSError as exc:
            return _json_error(f"save failed: {exc}", 500)

        entry = _first_entry(hass)
        if entry is None:
            return _json_error("no PLCAssistant config entry", 404)
        new_options = {
            **dict(entry.options),
            CONF_DYNAMICS_PRESET: name.lower(),
            CONF_DYNAMICS_PARAMS: dict(entry.options.get(CONF_DYNAMICS_PARAMS) or {}),
        }
        hass.config_entries.async_update_entry(entry, options=new_options)
        # Update listener reloads the entry (rebuilds plant from initials).
        return web.json_response(
            {"ok": True, "path": path, "preset": name.lower(), "reloaded": True}
        )


__all__ = ["async_setup_dynamics_api"]
