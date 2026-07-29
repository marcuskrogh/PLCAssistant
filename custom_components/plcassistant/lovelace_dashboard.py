"""Register the default PLCAssistant Lovelace dashboard in the HA sidebar.

No copy/paste: on integration setup we ensure the YAML template exists under
``config/dashboards/`` and register it as a Lovelace YAML-mode panel with
``show_in_sidebar=True`` (url path ``plcassistant-skid``).

Mirrors how Core registers YAML dashboards from ``configuration.yaml``
(``lovelace.dashboards``), without requiring the user to edit that file.
"""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

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


def _is_stock_board_needing_status_upgrade(text: str) -> bool:
    """True when YAML looks like a prior stock board that should be refreshed.

    Preserves true operator customizations (no Start button). Stock boards are
    refreshed when missing the status card (SWD-135) or explicitly on an older
    ``plcassistant_dashboard_version`` of 1–4 (SWD-137/138/139 offline help). Boards
    that already have status but no version marker are left alone.
    """
    if "button.plcassistant_start" not in text:
        return False
    if "title: PLCAssistant" not in text and "PLCAssistant" not in text:
        return False
    if "sensor.plcassistant_status" not in text:
        return True
    # Only refresh when an explicit older stock version is present (not 10+).
    if re.search(r"plcassistant_dashboard_version:\s*[1234]\b", text):
        return True
    return False


def ensure_dashboard_yaml(hass: HomeAssistant) -> Path:
    """Copy bundled YAML into HA config when missing or stock upgrade needed.

    Never clobber boards that look operator-customized (no Start entity, or
    already include the status sensor).
    """
    dest = Path(hass.config.path(REL_FILENAME))
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = bundled_dashboard_yaml()
    if not src.is_file():
        raise FileNotFoundError(f"bundled Lovelace YAML missing: {src}")
    if not dest.is_file():
        shutil.copy2(src, dest)
        _LOGGER.info("PLCAssistant: installed default Lovelace YAML at %s", dest)
        return dest
    try:
        existing = dest.read_text(encoding="utf-8")
    except OSError as err:
        _LOGGER.warning("PLCAssistant: could not read %s (%s); leaving in place", dest, err)
        return dest
    if _is_stock_board_needing_status_upgrade(existing):
        shutil.copy2(src, dest)
        _LOGGER.info(
            "PLCAssistant: refreshed stock Lovelace YAML at %s (status card)",
            dest,
        )
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


def _panel_exists(hass: HomeAssistant, url_path: str) -> bool:
    """Return True if a frontend panel is already registered for url_path."""
    try:
        from homeassistant.components.frontend import async_panel_exists

        return bool(async_panel_exists(hass, url_path))
    except (ImportError, AttributeError, TypeError):
        return url_path in hass.data.get("frontend_panels", {})


def _lovelace_data_key() -> Any:
    """Resolve hass.data key for Lovelace (LOVELACE_DATA or domain string)."""
    try:
        from homeassistant.components.lovelace.const import LOVELACE_DATA

        return LOVELACE_DATA
    except ImportError:
        try:
            from homeassistant.components.lovelace.const import DOMAIN as LL_DOMAIN

            return LL_DOMAIN
        except ImportError:
            return "lovelace"


def _mode_yaml() -> str:
    try:
        from homeassistant.components.lovelace.const import MODE_YAML

        return MODE_YAML
    except ImportError:
        return "yaml"


def _register_lovelace_panel(hass: HomeAssistant, conf: dict[str, Any], *, update: bool) -> None:
    """Register (or refresh) the frontend Lovelace panel — Core-compatible kwargs."""
    from homeassistant.components.frontend import async_register_built_in_panel

    mode = conf.get("mode", "yaml")
    base_kwargs: dict[str, Any] = {
        "sidebar_title": conf.get("title", TITLE),
        "sidebar_icon": conf.get("icon", ICON),
        "frontend_url_path": URL_PATH,
        "config": {"mode": mode},
        "require_admin": bool(conf.get("require_admin", False)),
    }
    show = bool(conf.get("show_in_sidebar", True))

    # Try newest signature first (show_in_sidebar + update), then degrade.
    attempts: list[Callable[[], None]] = [
        lambda: async_register_built_in_panel(
            hass, "lovelace", show_in_sidebar=show, update=update, **base_kwargs
        ),
        lambda: async_register_built_in_panel(
            hass, "lovelace", update=update, **base_kwargs
        ),
        lambda: async_register_built_in_panel(hass, "lovelace", **base_kwargs),
    ]
    last_type_error: TypeError | None = None
    for attempt in attempts:
        try:
            attempt()
            return
        except TypeError as err:
            last_type_error = err
            continue
    if last_type_error is not None:
        raise last_type_error


async def async_setup_sidebar_dashboard(hass: HomeAssistant) -> bool:
    """Ensure YAML exists and register the PLCAssistant sidebar Lovelace panel.

    Returns True when the dashboard is available in the sidebar (or already was).
    """
    try:
        from homeassistant.components.lovelace.dashboard import LovelaceYAML
    except ImportError as err:
        _LOGGER.warning(
            "PLCAssistant: Lovelace APIs unavailable (%s); sidebar dashboard skipped",
            err,
        )
        return False

    ll_key = _lovelace_data_key()
    ll_data = hass.data.get(ll_key)
    if ll_data is None and ll_key != "lovelace":
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
    conf["mode"] = _mode_yaml()

    dashboards = getattr(ll_data, "dashboards", None)
    if not isinstance(dashboards, dict):
        _LOGGER.error("PLCAssistant: Lovelace dashboards map missing")
        return False

    yaml_dashboards = getattr(ll_data, "yaml_dashboards", None)
    if isinstance(yaml_dashboards, dict):
        yaml_dashboards[URL_PATH] = conf

    existing = dashboards.get(URL_PATH)
    panel_already = _panel_exists(hass, URL_PATH)
    update_panel = False

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
