"""SWD-184 acceptance: Datablocks, Program access, store, example rebuild."""

from __future__ import annotations

from pathlib import Path

import pytest

from plcassistant.app.default_image import declare_default_image
from plcassistant.io.datablock import (
    DatablockCatalog,
    datablock_from_dict,
    default_program_datablock_access,
    default_tank_datablock_catalog,
    program_accessible_tags,
    union_program_access_ids,
)
from plcassistant.io.mqtt_entity_bridge import default_wedge_binding_config
from plcassistant.surface.builtin import wedge_softplc_project
from plcassistant.surface.schema import program_from_dict, project_from_dict


def _load_store_mod():
    import importlib.util

    store_path = Path("custom_components/plcassistant/datablocks/store.py")
    spec = importlib.util.spec_from_file_location("datablock_store", store_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_unit_db_tank_is_fully_defined() -> None:
    catalog = default_tank_datablock_catalog()
    block = catalog.get("DB_Tank")
    assert block is not None
    assert block.description
    assert "LT_TANK" in block.tags
    assert "CMD_SPEED" in block.tags
    table = block.binding_table()
    assert len(table.bindings) == 22
    assert {b.tag for b in table.bindings} <= set(block.tags)
    assert {"LEVEL_KD", "FLOW_KD"} <= set(block.tags)
    assert set(block.tags) - {b.tag for b in table.bindings} == {"LEVEL_KD", "FLOW_KD"}
    assert "LEVEL_MODE" in block.tags
    assert "SP_LEVEL_MAN" in block.tags


def test_unit_program_access_resolves_tag_set() -> None:
    catalog = default_tank_datablock_catalog()
    tags = program_accessible_tags(catalog, ["DB_Tank"])
    assert "LT_TANK" in tags
    assert "SP_LEVEL_REQ" in tags
    with pytest.raises(KeyError):
        program_accessible_tags(catalog, ["DB_Missing"])


def test_unit_catalog_rejects_duplicate_out_writer_on_merge() -> None:
    catalog = default_tank_datablock_catalog()
    catalog.upsert(
        datablock_from_dict(
            {
                "id": "DB_Dup",
                "tags": {
                    "CMD_SPEED": {"default": 0.0, "unit": "pct"},
                    "EXTRA": {"default": 0.0, "unit": "pct"},
                },
                "bindings": [
                    {
                        "tag": "EXTRA",
                        "entity": "sensor.plcassistant_cmd_speed",
                        "direction": "OUT",
                    }
                ],
            }
        )
    )
    with pytest.raises(ValueError, match="duplicate OUT writer"):
        catalog.binding_table_for(["DB_Tank", "DB_Dup"])


def test_unit_datablock_from_dict_rejects_within_block_dup_out() -> None:
    with pytest.raises(ValueError, match="duplicate OUT writer"):
        datablock_from_dict(
            {
                "id": "DB_Bad",
                "tags": {
                    "A": {"default": 0.0, "unit": "pct"},
                    "B": {"default": 0.0, "unit": "pct"},
                },
                "bindings": [
                    {
                        "tag": "A",
                        "entity": "sensor.x",
                        "direction": "OUT",
                    },
                    {
                        "tag": "B",
                        "entity": "sensor.x",
                        "direction": "OUT",
                    },
                ],
            }
        )


def test_unit_default_image_only_declares_accessible_tags() -> None:
    image = declare_default_image()
    catalog = default_tank_datablock_catalog()
    allowed = program_accessible_tags(
        catalog, union_program_access_ids(default_program_datablock_access())
    )
    assert set(image.names()) == set(allowed)
    assert "LT_TANK" in image.names()


def test_integration_store_round_trip(tmp_path: Path) -> None:
    mod = _load_store_mod()
    binding_rows_from_store = mod.binding_rows_from_store
    load_store = mod.load_store
    save_store = mod.save_store

    payload = load_store(tmp_path)
    assert "DB_Tank" in payload["datablocks"]
    assert payload["program_access"] == default_program_datablock_access()
    payload["program_access"]["tank"] = ["DB_Tank"]
    save_store(tmp_path, payload)
    reloaded = load_store(tmp_path)
    assert reloaded["program_access"]["tank"] == ["DB_Tank"]
    rows = binding_rows_from_store(reloaded)
    assert any(r["tag"] == "LT_TANK" for r in rows)
    assert all("entity_unit" in r for r in rows)


def test_integration_store_respects_program_access(tmp_path: Path) -> None:
    mod = _load_store_mod()
    binding_rows_from_store = mod.binding_rows_from_store
    load_store = mod.load_store
    save_store = mod.save_store

    payload = load_store(tmp_path)
    catalog = DatablockCatalog.from_dict(payload)
    catalog.upsert(
        datablock_from_dict(
            {
                "id": "DB_Other",
                "tags": {"OTHER": {"default": 0.0, "unit": None}},
                "bindings": [
                    {
                        "tag": "OTHER",
                        "entity": "sensor.plcassistant_other",
                        "direction": "IN",
                    }
                ],
            }
        )
    )
    payload["datablocks"] = catalog.to_dict()["datablocks"]
    payload["program_access"] = {"tank": ["DB_Tank"]}
    save_store(tmp_path, payload)
    rows = binding_rows_from_store(payload)
    tags = {r["tag"] for r in rows}
    assert "LT_TANK" in tags
    assert "OTHER" not in tags

    payload["program_access"] = {}
    assert binding_rows_from_store(payload) == []


def test_integration_store_raises_on_access_merge_conflict(tmp_path: Path) -> None:
    mod = _load_store_mod()
    binding_rows_from_store = mod.binding_rows_from_store
    load_store = mod.load_store

    payload = load_store(tmp_path)
    catalog = DatablockCatalog.from_dict(payload)
    catalog.upsert(
        datablock_from_dict(
            {
                "id": "DB_Dup",
                "tags": {
                    "EXTRA": {"default": 0.0, "unit": "pct"},
                },
                "bindings": [
                    {
                        "tag": "EXTRA",
                        "entity": "sensor.plcassistant_cmd_speed",
                        "direction": "OUT",
                    }
                ],
            }
        )
    )
    payload["datablocks"] = catalog.to_dict()["datablocks"]
    payload["program_access"] = {"tank": ["DB_Tank", "DB_Dup"]}
    with pytest.raises(ValueError, match="duplicate OUT writer"):
        binding_rows_from_store(payload)


def test_integration_flat_binding_config_comes_from_datablock() -> None:
    cfg = default_wedge_binding_config()
    catalog = default_tank_datablock_catalog()
    table = catalog.binding_table_for(["DB_Tank"])
    assert set(cfg["tags"]) == set(table.tags)
    assert {b["tag"] for b in cfg["bindings"]} == {b.tag for b in table.bindings}


def test_system_tank_program_declares_db_tank_and_sees_tags() -> None:
    project = project_from_dict(wedge_softplc_project())
    prog = project.programs["tank"]
    assert prog.datablocks == ["DB_Tank"]
    catalog = default_tank_datablock_catalog()
    tags = program_accessible_tags(catalog, prog.datablocks)
    assert "LT_TANK" in tags
    assert "CMD_SPEED" in tags
    # Round-trip preserves access.
    again = program_from_dict(
        {
            "version": "1.0",
            "name": prog.name,
            "instances": {},
            "wires": [],
            "execution_order": [],
            "datablocks": prog.datablocks,
        }
    )
    assert again.datablocks == ["DB_Tank"]


def test_system_mqtt_path_uses_datablock_bindings() -> None:
    from plcassistant.app.runtime import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.integration import MockEntityStore
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.io.mqtt_entity_bridge import MqttEntityBridge
    from plcassistant.wedge.safety import Mode

    catalog = default_tank_datablock_catalog()
    project = project_from_dict(wedge_softplc_project())
    table = catalog.binding_table_for(project.programs["tank"].datablocks)
    assert program_accessible_tags(catalog, project.programs["tank"].datablocks) == frozenset(
        table.tags
    )

    bus = InMemoryMqttBus()
    entities = MockEntityStore()
    entities.set("number.plcassistant_sp_level_req", 0.20)
    entities.set("number.plcassistant_lt_tank_in", 0.15)
    entities.set("number.plcassistant_lt_res_in", 0.20)
    entities.set("number.plcassistant_ft_inlet_in", 0.0)

    image = declare_default_image()
    assert set(image.names()) == set(table.tags)
    app = MqttIoBridge(bus, instance_id="default")
    app.start()
    integ = MqttEntityBridge(bus, table, entities, instance_id="default")
    integ.start()
    integ.publish_inputs()
    app.apply_inputs(image)
    logic = SkidImageLogic(period_s=0.1)
    logic.skid.program_loader.restart_apply(project)
    logic.enqueue_operator("start")
    for _ in range(6):
        logic(image)
    app.publish_outputs(image)
    integ.apply_outputs()

    assert logic.skid.last is not None
    assert logic.skid.last.mode is Mode.RUNNING
    assert entities.get("sensor.plcassistant_cmd_speed").value > 0.0


def test_system_editor_uses_callapi_pattern() -> None:
    html = Path("custom_components/plcassistant/www/datablock_editor.html").read_text(
        encoding="utf-8"
    )
    assert "hass.callApi" in html
    assert "plcassistant/datablocks" in html
    api = Path("custom_components/plcassistant/datablocks/http_api.py").read_text(
        encoding="utf-8"
    )
    assert "async_reload" in api
    assert "CONF_BINDINGS" in api
    assert "bindings_unchanged" in api
    init = Path("custom_components/plcassistant/__init__.py").read_text(encoding="utf-8")
    assert "if bindings is None" in init
