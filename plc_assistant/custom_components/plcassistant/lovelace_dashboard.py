"""Register the default PLCAssistant Lovelace dashboard in the HA sidebar.

No copy/paste: on integration setup we ensure the YAML template exists under
``config/dashboards/`` and register it as a Lovelace YAML-mode panel with
``show_in_sidebar=True`` (url path ``plcassistant-skid``).

Mirrors how Core registers YAML dashboards from ``configuration.yaml``
(``lovelace.dashboards``), without requiring the user to edit that file.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# url_path must contain a hyphen (Lovelace rule for non-default dashboards).
URL_PATH = "plcassistant-skid"
TITLE = "PLCAssistant"
ICON = "mdi:cup-water"
REL_FILENAME = "dashboards/plcassistant.yaml"


def bundled_dashboard_yaml() -> Path:
    """Path to the dashboard template shipped inside the integration package."""
    return Path(__file__).resolve().parent / "lovelace" / "plcassistant.yaml"


def ensure_dashboard_yaml(hass: HomeAssistant) -> Path:
    """Copy bundled YAML into HA config when missing (never clobber user edits)."""
    dest = Path(hass.config.path(REL_FILENAME))
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = bundled_dashboard_yaml()
    if not src.is_file():
        raise FileNotFoundError(f"bundled Lovelace YAML missing: {src}")
    if not dest.is_file():
        shutil.copy2(src, dest)
        _LOGGER.info("PLCAssistant: installed default Lovelace YAML at %s", dest)
    return dest


def default_dashboard_config() -> dict[str, Any]:
    """Lovelace YAML dashboard panel config (mirrors configuration.yaml shape)."""
    return {
        "mode": "yaml",
        "title": TITLE,
        "icon": ICON,
        "show_in_sidebar": True,
        "require_admin": False,
        "filename": REL_FILENAME,
    }


def _register_lovelace_panel(hass: HomeAssistant, conf: dict[str, Any], *, update: bool) -> None:
    """Register (or refresh) the frontend Lovelace panel — Core-compatible kwargs."""
    from homeassistant.components.frontend import async_register_built_in_panel

    mode = conf.get("mode", "yaml")
    kwargs: dict[str, Any] = {
        "frontend_url_path": URL_PATH,
        "require_admin": bool(conf.get("require_admin", False)),
        "sidebar_title": conf.get("title", TITLE),
        "sidebar_icon": conf.get("icon", ICON),
        "config": {"mode": mode},
        "update": update,
    }
    # Newer Core accepts show_in_sidebar; older builds omit it (title ⇒ sidebar).
    try:
        async_register_built_in_panel(
            hass,
            "lovelace",
            show_in_sidebar=bool(conf.get("show_in_sidebar", True)),
            **kwargs,
        )
    except TypeError:
        kwargs.pop("update", None)
        try:
            async_register_built_in_panel(hass, "lovelace", **kwargs, update=update)
        except TypeError:
            async_register_built_in_panel(
                hass,
                "lovelace",
                sidebar_title=kwargs["sidebar_title"],
                sidebar_icon=kwargs["sidebar_icon"],
                frontend_url_path=URL_PATH,
                config={"mode": mode},
                require_admin=bool(conf.get("require_admin", False)),
            )


async def async_setup_sidebar_dashboard(hass: HomeAssistant) -> bool:
    """Ensure YAML exists and register the PLCAssistant sidebar Lovelace panel.

    Returns True when the dashboard is available in the sidebar (or already was).
    """
    try:
        from homeassistant.components.frontend import async_panel_exists
        from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_YAML
        from homeassistant.components.lovelace.dashboard import LovelaceYAML
    except ImportError as err:
        _LOGGER.warning(
            "PLCAssistant: Lovelace APIs unavailable (%s); sidebar dashboard skipped",
            err,
        )
        return False

    ll_data = hass.data.get(LOVELACE_DATA)
    if ll_data is None:
        # Older Core keyed Lovelace under the domain string only.
        ll_data = hass.data.get("lovelace")
    if ll_data is None:
        _LOGGER.warning(
            "PLCAssistant: Lovelace not ready yet; sidebar dashboard skipped "
            "(restart Core after App install)"
        )
        return False

    try:
        await hass.async_add_executor_job(ensure_dashboard_yaml, hass)
    except OSError as err:
        _LOGGER.error("PLCAssistant: could not install dashboard YAML: %s", err)
        return False

    conf = default_dashboard_config()
    conf["mode"] = MODE_YAML

    dashboards = getattr(ll_data, "dashboards", None)
    if not isinstance(dashboards, dict):
        _LOGGER.error("PLCAssistant: Lovelace dashboards map missing")
        return False

    yaml_dashboards = getattr(ll_data, "yaml_dashboards", None)
    if isinstance(yaml_dashboards, dict):
        yaml_dashboards[URL_PATH] = conf

    existing = dashboards.get(URL_PATH)
    update_panel = False
    try:
        panel_already = async_panel_exists(hass, URL_PATH)
    except (AttributeError, TypeError):
        panel_already = URL_PATH in hass.data.get("frontend_panels", {})

    if existing is None:
        dashboards[URL_PATH] = LovelaceYAML(hass, URL_PATH, conf)
        update_panel = panel_already
    elif type(existing).__name__ != "LovelaceYAML":
        # Storage-mode board already owns this path — leave it; still ensure sidebar.
        _LOGGER.warning(
            "PLCAssistant: url_path %s already used by %s; not replacing",
            URL_PATH,
            type(existing).__name__,
        )
        if panel_already:
            return True
        update_panel = False
    else:
        # Refresh YAML config reference (filename/title/icon) without clobbering file.
        # LovelaceConfig.url_path reads config["url_path"].
        existing.config = {**conf, "url_path": URL_PATH}  # type: ignore[attr-defined]
        update_panel = panel_already

    try:
        _register_lovelace_panel(hass, conf, update=update_panel)
    except ValueError as err:
        # Panel path collision — treat as already registered.
        _LOGGER.debug("PLCAssistant: panel register ValueError (%s)", err)
        if not panel_already and not update_panel:
            try:
                _register_lovelace_panel(hass, conf, update=True)
            except Exception:  # noqa: BLE001
                _LOGGER.exception(
                    "PLCAssistant: failed to register sidebar dashboard %s", URL_PATH
                )
                return False
    except Exception:  # noqa: BLE001
        _LOGGER.exception(
            "PLCAssistant: failed to register sidebar dashboard %s", URL_PATH
        )
        return False

    _LOGGER.info(
        "PLCAssistant: Lovelace dashboard '%s' is in the sidebar (/%s)",
        TITLE,
        URL_PATH,
    )
    return True


__all__ = [
    "ICON",
    "REL_FILENAME",
    "TITLE",
    "URL_PATH",
    "async_setup_sidebar_dashboard",
    "bundled_dashboard_yaml",
    "default_dashboard_config",
    "ensure_dashboard_yaml",
]
