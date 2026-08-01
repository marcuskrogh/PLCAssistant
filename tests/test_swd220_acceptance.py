"""SWD-220: PID cards resource registration + Manual level default (updated SWD-221)."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path("custom_components/plcassistant")


def test_unit_mode_defaults_are_manual() -> None:
    from plcassistant.io.datablock import default_tank_datablock_catalog

    block = default_tank_datablock_catalog().get("DB_Tank")
    assert block is not None
    assert float(block.tags["LEVEL_MODE"].default) == pytest.approx(0.0)
    assert float(block.tags["FLOW_MODE"].default) == pytest.approx(1.0)  # cascade slave (SWD-221)

    meta = (ROOT / "number.py").read_text(encoding="utf-8")
    assert '"object_id": "plcassistant_level_mode"' in meta
    assert '"object_id": "plcassistant_flow_mode"' in meta
    level_block = meta.split('"LEVEL_MODE":', 1)[1].split('"SP_FLOW_MAN"', 1)[0]
    assert '"default": 0.0' in level_block
    flow_block = meta.split('"FLOW_MODE":', 1)[1].split('"LEVEL_KP"', 1)[0]
    assert '"default": 1.0' in flow_block


def test_unit_skid_missing_mode_defaults_manual() -> None:
    """Missing or invalid LEVEL_MODE must select Manual SP (mux fallback)."""
    from plcassistant.app.skid_scan import _resolve_level_sp

    class _FakeImage:
        def __init__(self, names: tuple[str, ...], values: dict[str, float | str]) -> None:
            self._names = names
            self._values = values

        def names(self) -> tuple[str, ...]:
            return self._names

        def get_value(self, name: str) -> float | str:
            return self._values[name]

    missing_mode = _FakeImage(
        ("SP_LEVEL_MAN", "SP_LEVEL_REQ", "SP_LEVEL_REM"),
        {"SP_LEVEL_MAN": 0.25, "SP_LEVEL_REQ": 0.20, "SP_LEVEL_REM": 0.99},
    )
    assert _resolve_level_sp(missing_mode) == pytest.approx(0.25)

    invalid_mode = _FakeImage(
        ("SP_LEVEL_MAN", "SP_LEVEL_REQ", "SP_LEVEL_REM", "LEVEL_MODE"),
        {
            "SP_LEVEL_MAN": 0.25,
            "SP_LEVEL_REQ": 0.20,
            "SP_LEVEL_REM": 0.99,
            "LEVEL_MODE": "bogus",
        },
    )
    assert _resolve_level_sp(invalid_mode) == pytest.approx(0.25)


def test_integration_hydrate_publish_does_not_reference_flip_path() -> None:
    """Setup must not mode-flip: batch seed + hydrate-only async_added_to_hass."""
    text = (ROOT / "number.py").read_text(encoding="utf-8")
    assert "async def async_seed_operator_defaults" in text
    added = text.split("async def async_added_to_hass", 1)[1]
    seed = added.split("async def _on_tag_in", 1)[0]
    assert "await self._publish_in_tag(self._tag, eng)" not in seed
    assert "async_set_native_value" not in seed
    assert "_sp_mode_flip_map" not in seed
    set_fn = text.split("async def async_set_native_value", 1)[1].split(
        "async def async_added_to_hass", 1
    )[0]
    assert "_sp_mode_flip_map().get(self._tag)" in set_fn


def test_system_lovelace_resource_registration() -> None:
    init = (ROOT / "__init__.py").read_text(encoding="utf-8")
    assert "_async_register_frontend_card" in init
    assert "async_create_item" in init
    assert "res_type" in init
    assert "?v=" in init or 'card_url = f"{base_url}?v={version}"' in init
    assert "add_extra_js_url" in init  # YAML fallback only
    assert "not falling back to add_extra_js_url" in init
    assert "_lovelace_data_key" in init
    assert "async_load" in init

    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"after_dependencies"' in manifest
    assert '"lovelace"' in manifest
    assert '"0.1.42"' in manifest

    pid = (ROOT / "www" / "pid-loop-card.js").read_text(encoding="utf-8")
    assert 'customElements.get("plcassistant-pid-card")' in pid
    assert "getConfigElement" not in pid
    assert 'mode = (st?.state || "manual")' in pid

    block = (ROOT / "www" / "block-list-card.js").read_text(encoding="utf-8")
    assert 'customElements.get("plcassistant-block-list-card")' in block

    dash = (ROOT / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 21" in dash


def test_integration_ha_catalog_mode_default_parity() -> None:
    from plcassistant.io.datablock import default_tank_datablock_catalog as soft
    import importlib.util
    import sys
    import types

    pkg = "ha_db_swd220"
    sys.modules[pkg] = types.ModuleType(pkg)
    binding = ROOT / "datablocks" / "binding_types.py"
    catalog = ROOT / "datablocks" / "catalog.py"
    spec_b = importlib.util.spec_from_file_location(f"{pkg}.binding_types", binding)
    assert spec_b and spec_b.loader
    mod_b = importlib.util.module_from_spec(spec_b)
    sys.modules[f"{pkg}.binding_types"] = mod_b
    spec_b.loader.exec_module(mod_b)
    src = catalog.read_text(encoding="utf-8").replace(
        "from .binding_types import Binding, BindingTable, TagDecl",
        f"from {pkg}.binding_types import Binding, BindingTable, TagDecl",
    )
    mod_c = types.ModuleType(f"{pkg}.catalog")
    sys.modules[f"{pkg}.catalog"] = mod_c
    exec(compile(src, str(catalog), "exec"), mod_c.__dict__)

    soft_block = soft().get("DB_Tank")
    ha_block = mod_c.default_tank_datablock_catalog().get("DB_Tank")
    assert float(soft_block.tags["LEVEL_MODE"].default) == float(
        ha_block.tags["LEVEL_MODE"].default
    ) == pytest.approx(0.0)
    assert float(soft_block.tags["FLOW_MODE"].default) == float(
        ha_block.tags["FLOW_MODE"].default
    ) == pytest.approx(1.0)
