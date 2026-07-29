"""PLCAssistant thin Home Assistant integration (SWD-126).

Owns tag declarations / entity↔tag bindings, mock entities, and operator
services. Talks to the Soft-PLC App over MQTT (Mosquitto required).

Unit tests in this repo do not import this module (no ``homeassistant`` in CI).
Testable MQTT mapping lives in ``plcassistant.io.mqtt_entity_bridge``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path

from homeassistant.components.mqtt import async_subscribe
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_BINDINGS,
    CONF_INSTANCE_ID,
    CONF_MOCK_MODE,
    DEFAULT_INSTANCE_ID,
    DOMAIN,
    SERVICE_RESET,
    SERVICE_START,
    SERVICE_STOP,
)
from .ha_config_bridge import read_runtime_snapshot, write_cmd
from .mqtt_topics import cmd_topic, status_topic, tag_in_topic, tag_out_topic

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SENSOR, Platform.BUTTON]
# Poll shared App runtime file when MQTT stays silent (SWD-139).
_FILE_BRIDGE_POLL_S = 1.0
_FILE_BRIDGE_FRESH_S = 3.0
_MQTT_SILENT_S = 3.0
# Soft-PLC OUT tags hydrated from HA-config runtime.json when MQTT is silent.
_HMI_TAGS = (
    "MODE",
    "PERM_OK",
    "TRIP_ACTIVE",
    "LT_TANK",
    "LT_RES",
    "FT_INLET",
    "CMD_SPEED",
    "SP_LEVEL",
    "SP_FLOW",
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


def _default_bindings() -> list[dict]:
    """Default mock bindings — keep in sync with ``default_wedge_binding_config``."""
    return [
        {
            "tag": "SP_LEVEL_REQ",
            "entity": "number.plcassistant_sp_level_req",
            "direction": "IN",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "LT_TANK",
            "entity": "sensor.plcassistant_lt_tank",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "LT_RES",
            "entity": "sensor.plcassistant_lt_res",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "FT_INLET",
            "entity": "sensor.plcassistant_ft_inlet",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "CMD_SPEED",
            "entity": "sensor.plcassistant_cmd_speed",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "SP_LEVEL",
            "entity": "sensor.plcassistant_sp_level",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "SP_FLOW",
            "entity": "sensor.plcassistant_sp_flow",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "MODE",
            "entity": "sensor.plcassistant_mode",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "PERM_OK",
            "entity": "sensor.plcassistant_perm_ok",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
        {
            "tag": "TRIP_ACTIVE",
            "entity": "sensor.plcassistant_trip_active",
            "direction": "OUT",
            "scale": 1.0,
            "offset": 0.0,
        },
    ]


def _apply_file_runtime(hass: HomeAssistant, entry_id: str, snap: dict) -> None:
    """Hydrate MQTT caches + fire bus events from a shared runtime snapshot."""
    store = hass.data.get(DOMAIN, {}).get(entry_id)
    if store is None:
        return
    status = str(snap.get("status") or "").strip().lower()
    if status in ("running", "stopped", "fault", "offline"):
        extras = {}
        if snap.get("mode") is not None:
            extras["mode"] = snap.get("mode")
        payload = json.dumps({"state": status, **extras})
        store["status_payload"] = payload
        hass.bus.async_fire(
            f"{DOMAIN}_status",
            {"payload": payload, "entry_id": entry_id},
        )
    tags = snap.get("tags") if isinstance(snap.get("tags"), dict) else {}
    out_values = store.setdefault("out_values", {})
    for tag in _HMI_TAGS:
        tag_body = tags.get(tag)
        if not isinstance(tag_body, dict) or "value" not in tag_body:
            continue
        text = json.dumps(
            {
                "value": tag_body.get("value"),
                "status": tag_body.get("status") or "GOOD",
                "reason": tag_body.get("reason"),
                "ts": snap.get("ts"),
            }
        )
        out_values[tag] = text
        hass.bus.async_fire(
            f"{DOMAIN}_tag_out",
            {"tag": tag, "payload": text, "entry_id": entry_id},
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    instance_id = entry.data.get(CONF_INSTANCE_ID, DEFAULT_INSTANCE_ID)
    bindings = entry.data.get(CONF_BINDINGS) or _default_bindings()
    mock_mode = entry.data.get(CONF_MOCK_MODE, True)
    config_root = Path(hass.config.path())

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_INSTANCE_ID: instance_id,
        CONF_BINDINGS: bindings,
        CONF_MOCK_MODE: mock_mode,
        # MQTT payload caches — filled on subscribe (incl. retained) before
        # platform entities listen on the HA bus (SWD-136 hydrate-on-add).
        "out_values": {},
        "status_payload": None,
        "unsubs": [],
        "config_root": config_root,
    }

    async def _publish_cmd(name: str, call: ServiceCall) -> None:
        # Prefer explicit instance_id in the service call; else first entry.
        target = call.data.get(CONF_INSTANCE_ID)
        data = None
        if target:
            for entry_data in hass.data[DOMAIN].values():
                if isinstance(entry_data, dict) and entry_data.get(CONF_INSTANCE_ID) == target:
                    data = entry_data
                    break
        if data is None:
            data = hass.data[DOMAIN].get(entry.entry_id)
        if data is None:
            return
        topic = cmd_topic(data[CONF_INSTANCE_ID], name)
        await hass.services.async_call(
            "mqtt",
            "publish",
            {
                "topic": topic,
                "payload": call.data.get("payload", "1"),
                "qos": 1,
                "retain": False,
            },
            blocking=False,
        )
        # Shared-config fallback when MQTT never reaches Soft-PLC (SWD-139).
        root = data.get("config_root")
        if isinstance(root, Path):
            await hass.async_add_executor_job(write_cmd, name, root)

    async def handle_start(call: ServiceCall) -> None:
        await _publish_cmd(SERVICE_START, call)

    async def handle_stop(call: ServiceCall) -> None:
        await _publish_cmd(SERVICE_STOP, call)

    async def handle_reset(call: ServiceCall) -> None:
        await _publish_cmd(SERVICE_RESET, call)

    if not hass.services.has_service(DOMAIN, SERVICE_START):
        hass.services.async_register(DOMAIN, SERVICE_START, handle_start)
        hass.services.async_register(DOMAIN, SERVICE_STOP, handle_stop)
        hass.services.async_register(DOMAIN, SERVICE_RESET, handle_reset)

    for binding in bindings:
        direction = str(binding.get("direction", "")).upper()
        if direction not in ("OUT", "INOUT"):
            continue
        tag = binding["tag"]
        topic = tag_out_topic(instance_id, tag)

        def _make_out_handler(tag_name: str, entry_id: str):
            async def _on_out(msg) -> None:
                try:
                    payload = msg.payload
                    if isinstance(payload, bytes):
                        text = payload.decode("utf-8")
                    else:
                        text = str(payload)
                except UnicodeDecodeError:
                    return
                store = hass.data[DOMAIN].get(entry_id)
                if store is None:
                    return
                store["out_values"][tag_name] = text
                hass.bus.async_fire(
                    f"{DOMAIN}_tag_out",
                    {"tag": tag_name, "payload": text, "entry_id": entry_id},
                )

            return _on_out

        unsub = await async_subscribe(
            hass, topic, _make_out_handler(tag, entry.entry_id), qos=1
        )
        hass.data[DOMAIN][entry.entry_id]["unsubs"].append(unsub)

    # App scan status (retained) — powers sensor.plcassistant_status on the HMI.
    # Cache the payload before firing so sensors that register later can hydrate
    # (retained delivery often lands before async_forward_entry_setups).
    async def _on_status(msg) -> None:
        try:
            payload = msg.payload
            if isinstance(payload, bytes):
                text = payload.decode("utf-8")
            else:
                text = str(payload)
        except UnicodeDecodeError:
            return
        store = hass.data[DOMAIN].get(entry.entry_id)
        if store is not None:
            store["status_payload"] = text
            store["last_mqtt_status_mono"] = time.monotonic()
        hass.bus.async_fire(
            f"{DOMAIN}_status",
            {"payload": text, "entry_id": entry.entry_id},
        )

    status_unsub = await async_subscribe(
        hass, status_topic(instance_id), _on_status, qos=1
    )
    hass.data[DOMAIN][entry.entry_id]["unsubs"].append(status_unsub)

    async def _poll_file_bridge() -> None:
        entry_id = entry.entry_id
        while True:
            try:
                store = hass.data.get(DOMAIN, {}).get(entry_id) or {}
                last_mqtt = store.get("last_mqtt_status_mono")
                # MQTT remains primary — only use the file when status is silent.
                if last_mqtt is not None and (
                    time.monotonic() - float(last_mqtt)
                ) < _MQTT_SILENT_S:
                    await asyncio.sleep(_FILE_BRIDGE_POLL_S)
                    continue
                snap = await hass.async_add_executor_job(
                    read_runtime_snapshot, config_root
                )
                if snap:
                    try:
                        age = time.time() - float(snap.get("ts") or 0.0)
                    except (TypeError, ValueError):
                        age = _FILE_BRIDGE_FRESH_S + 1.0
                    if age <= _FILE_BRIDGE_FRESH_S:
                        _apply_file_runtime(hass, entry_id, snap)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 — never crash the poll loop
                _LOGGER.debug("PLCAssistant: file-bridge poll failed", exc_info=True)
            await asyncio.sleep(_FILE_BRIDGE_POLL_S)

    # Prefer create_task; background helper may be unavailable on older Core.
    try:
        poll_task = hass.async_create_background_task(
            _poll_file_bridge(), name=f"{DOMAIN}_file_bridge_{entry.entry_id}"
        )
    except AttributeError:
        poll_task = hass.async_create_task(_poll_file_bridge())
    hass.data[DOMAIN][entry.entry_id]["poll_task"] = poll_task

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Default Lovelace board in the HA sidebar (SWD-134) — no copy/paste.
    try:
        from .lovelace_dashboard import async_setup_sidebar_dashboard

        await async_setup_sidebar_dashboard(hass)
    except Exception:  # noqa: BLE001 — never block entity setup on dashboard
        _LOGGER.exception("PLCAssistant: sidebar Lovelace dashboard setup failed")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id) or {}
    poll_task = data.get("poll_task")
    if poll_task is not None:
        poll_task.cancel()
    for unsub in data.get("unsubs") or []:
        unsub()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


__all__ = [
    "PLATFORMS",
    "async_setup",
    "async_setup_entry",
    "async_unload_entry",
    "tag_in_topic",
    "tag_out_topic",
    "cmd_topic",
]
