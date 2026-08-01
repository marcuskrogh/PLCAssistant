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
    CONF_DYNAMICS_PARAMS,
    CONF_DYNAMICS_PRESET,
    CONF_INSTANCE_ID,
    CONF_MOCK_MODE,
    DEFAULT_INSTANCE_ID,
    DOMAIN,
    SERVICE_RESET,
    SERVICE_SET_DYNAMICS_PRESET,
    SERVICE_START,
    SERVICE_STOP,
)
from .ha_config_bridge import read_runtime_snapshot, write_cmd
from .mqtt_topics import cmd_topic, status_topic, tag_in_topic, tag_out_topic

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.UPDATE,
]
# Poll shared App runtime file when MQTT stays silent (SWD-139).
_FILE_BRIDGE_POLL_S = 1.0
_FILE_BRIDGE_FRESH_S = 3.0
_MQTT_SILENT_S = 3.0
# Soft-PLC OUT tags hydrated from HA-config runtime.json when MQTT is silent.
# Plant PVs are Soft-PLC IN (SWD-145) — not mirrored from Soft-PLC runtime.
_HMI_TAGS = (
    "MODE",
    "PERM_OK",
    "TRIP_ACTIVE",
    "CMD_SPEED",
    "SP_LEVEL",
    "SP_FLOW",
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


def _default_bindings() -> list[dict]:
    """Default mock bindings from the rebuilt ``DB_Tank`` Datablock (SWD-184)."""
    from plcassistant.io.datablock import default_tank_datablock_catalog

    table = default_tank_datablock_catalog().binding_table_for(["DB_Tank"])
    return [
        {
            "tag": b.tag,
            "entity": b.entity,
            "direction": b.direction.value,
            "scale": b.scale,
            "offset": b.offset,
        }
        for b in table.bindings
    ]


def _apply_file_runtime(hass: HomeAssistant, entry_id: str, snap: dict) -> None:
    """Hydrate MQTT caches + fire bus events from a shared runtime snapshot."""
    store = hass.data.get(DOMAIN, {}).get(entry_id)
    if store is None:
        return
    sim = store.get("plant_simulator")
    status = str(snap.get("status") or "").strip().lower()
    if status in ("running", "stopped", "fault", "offline"):
        extras = {}
        if snap.get("mode") is not None:
            extras["mode"] = snap.get("mode")
        if snap.get("scan_period_s") is not None:
            extras["scan_period_s"] = snap.get("scan_period_s")
        payload = json.dumps({"state": status, **extras})
        store["status_payload"] = payload
        if sim is not None:
            sim.apply_status(payload)
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
        if tag == "CMD_SPEED" and sim is not None:
            sim.apply_cmd_from_payload(text)
        hass.bus.async_fire(
            f"{DOMAIN}_tag_out",
            {"tag": tag, "payload": text, "entry_id": entry_id},
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    instance_id = entry.data.get(CONF_INSTANCE_ID, DEFAULT_INSTANCE_ID)
    config_root = Path(hass.config.path())
    bindings = entry.data.get(CONF_BINDINGS) or _default_bindings()
    # Prefer Datablock store when present (SWD-184).
    try:
        from .datablocks.store import binding_rows_from_store, load_store

        store_payload = await hass.async_add_executor_job(load_store, config_root)
        store_rows = binding_rows_from_store(store_payload)
        if store_rows:
            bindings = store_rows
            hass.data[DOMAIN]["datablock_store"] = store_payload
            hass.data[DOMAIN]["datablock_bindings"] = store_rows
    except Exception:  # noqa: BLE001 — fall back to entry/default bindings
        _LOGGER.exception("PLCAssistant: Datablock store load failed; using entry bindings")
    mock_mode = entry.data.get(CONF_MOCK_MODE, True)

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_INSTANCE_ID: instance_id,
        CONF_BINDINGS: bindings,
        CONF_MOCK_MODE: mock_mode,
        # MQTT payload caches — filled on subscribe (incl. retained) before
        # platform entities listen on the HA bus (SWD-136 hydrate-on-add).
        "out_values": {},
        # Plant IN cache (SWD-170) — simulator flush before entity listeners.
        "in_values": {},
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

    async def handle_set_dynamics_preset(call: ServiceCall) -> None:
        target = call.data.get(CONF_INSTANCE_ID)
        entry_obj: ConfigEntry | None = None
        entries = list(hass.config_entries.async_entries(DOMAIN))
        if target:
            for cand in entries:
                if cand.data.get(CONF_INSTANCE_ID) == target:
                    entry_obj = cand
                    break
        elif entries:
            entry_obj = entries[0]
        if entry_obj is None:
            _LOGGER.warning("set_dynamics_preset: no matching config entry")
            return
        from .dynamics.options import parse_dynamics_params, validate_preset
        from .dynamics.registry import get_preset

        try:
            preset = validate_preset(call.data.get("preset"))
            params = parse_dynamics_params(call.data.get("params"))
            get_preset(preset, params=params)
        except (KeyError, ValueError, TypeError) as exc:
            _LOGGER.error("set_dynamics_preset rejected: %s", exc)
            return
        new_options = {
            **dict(entry_obj.options),
            CONF_DYNAMICS_PRESET: preset,
            CONF_DYNAMICS_PARAMS: params,
        }
        # Update listener reloads the entry (rebuilds plant from initials).
        hass.config_entries.async_update_entry(entry_obj, options=new_options)

    if not hass.services.has_service(DOMAIN, SERVICE_START):
        hass.services.async_register(DOMAIN, SERVICE_START, handle_start)
        hass.services.async_register(DOMAIN, SERVICE_STOP, handle_stop)
        hass.services.async_register(DOMAIN, SERVICE_RESET, handle_reset)
    if not hass.services.has_service(DOMAIN, SERVICE_SET_DYNAMICS_PRESET):
        hass.services.async_register(
            DOMAIN, SERVICE_SET_DYNAMICS_PRESET, handle_set_dynamics_preset
        )

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
                sim = store.get("plant_simulator")
                if tag_name == "CMD_SPEED" and sim is not None:
                    sim.apply_cmd_from_payload(text)
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
            sim = store.get("plant_simulator")
            if sim is not None:
                sim.apply_status(text)
        hass.bus.async_fire(
            f"{DOMAIN}_status",
            {"payload": text, "entry_id": entry.entry_id},
        )

    status_unsub = await async_subscribe(
        hass, status_topic(instance_id), _on_status, qos=1
    )
    hass.data[DOMAIN][entry.entry_id]["unsubs"].append(status_unsub)

    # SWD-166: register user model dir before plant loads presets.
    try:
        from .dynamics.http_api import async_setup_dynamics_api

        await async_setup_dynamics_api(hass)
    except Exception:  # noqa: BLE001 — never block setup on editor
        _LOGGER.exception("PLCAssistant: dynamics editor API setup failed")

    # SWD-184: Datablock configuration panel + store API.
    try:
        from .datablocks.http_api import async_setup_datablock_api

        await async_setup_datablock_api(hass)
    except Exception:  # noqa: BLE001 — never block setup on panel
        _LOGGER.exception("PLCAssistant: Datablock API setup failed")

    # SWD-146/143: integration-owned plant simulator (mock_mode only).
    if mock_mode:
        from .dynamics.options import resolve_dynamics_options, validate_preset
        from .dynamics.simulator import HassPlantSimulator

        preset, params = resolve_dynamics_options(entry.options)
        try:
            preset = validate_preset(preset)
        except KeyError as exc:
            _LOGGER.error("Invalid dynamics preset in options: %s", exc)
            raise
        plant_sim = HassPlantSimulator(
            hass,
            instance_id,
            entry_id=entry.entry_id,
            preset=preset,
            params=params,
        )
        store = hass.data[DOMAIN][entry.entry_id]
        store["plant_simulator"] = plant_sim
        store[CONF_DYNAMICS_PRESET] = preset
        store[CONF_DYNAMICS_PARAMS] = dict(params)
        # Retained status/CMD may have arrived on subscribe before the simulator
        # existed — hydrate so we do not wait for the next Soft-PLC heartbeat.
        cached_status = store.get("status_payload")
        if cached_status is not None:
            plant_sim.apply_status(cached_status)
        cached_cmd = (store.get("out_values") or {}).get("CMD_SPEED")
        if cached_cmd is not None:
            plant_sim.apply_cmd_from_payload(cached_cmd)
        await plant_sim.async_start()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # SWD-170: drop orphaned plant Number registry rows that block contracted IDs.
    if mock_mode:
        try:
            from .entity_cleanup import async_purge_orphaned_plant_numbers

            await async_purge_orphaned_plant_numbers(hass, instance_id)
        except Exception:  # noqa: BLE001 — never block setup on registry cleanup
            _LOGGER.debug(
                "PLCAssistant: plant Number registry cleanup failed", exc_info=True
            )

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
    plant_sim = data.get("plant_simulator")
    if plant_sim is not None:
        await plant_sim.async_stop()
    poll_task = data.get("poll_task")
    if poll_task is not None:
        poll_task.cancel()
    for unsub in data.get("unsubs") or []:
        unsub()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when Options flow (or service) updates dynamics options."""
    await hass.config_entries.async_reload(entry.entry_id)


__all__ = [
    "PLATFORMS",
    "async_setup",
    "async_setup_entry",
    "async_unload_entry",
    "tag_in_topic",
    "tag_out_topic",
    "cmd_topic",
]
