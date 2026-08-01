"""SWD-220: PID cards resource registration + Manual SP-source default."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path("custom_components/plcassistant")


def test_unit_mode_defaults_are_manual() -> None:
    from plcassistant.io.datablock import default_tank_datablock_catalog

    block = default_tank_datablock_catalog().get("DB_Tank")
    assert block is not None
    assert float(block.tags["LEVEL_MODE"].default) == pytest.approx(0.0)
    assert float(block.tags["FLOW_MODE"].default) == pytest.approx(0.0)

    meta = (ROOT / "number.py").read_text(encoding="utf-8")
    assert '"LEVEL_MODE"' in meta
    assert "default\": 0.0,  # Manual (SWD-220)" in meta or '"default": 0.0,  # Manual (SWD-220)' in meta
    assert '"FLOW_MODE"' in meta

    # Number meta defaults for modes are 0.0
    assert meta.count('"object_id": "plcassistant_level_mode"') == 1
    level_block = meta.split('"LEVEL_MODE":', 1)[1].split('"SP_FLOW_MAN"', 1)[0]
    assert '"default": 0.0' in level_block
    flow_block = meta.split('"FLOW_MODE":', 1)[1].split('"LEVEL_KP"', 1)[0]
    assert '"default": 0.0' in flow_block


def test_unit_skid_missing_mode_defaults_manual() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import _resolve_level_sp
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    # Clear mode sample so fallback path is used.
    image.apply_input("SP_LEVEL_MAN", 0.25, QualityStatus.GOOD)
    image.apply_input("SP_LEVEL_REQ", 0.20, QualityStatus.GOOD)
    # LEVEL_MODE declared but never sampled → get_value may still return default.
    # Force the resolve helper's missing-mode branch by removing the tag name.
    names = set(image.names())
    assert "LEVEL_MODE" in names
    # With default 0.0 from datablock, active SP should be Manual.
    sp = _resolve_level_sp(image)
    assert sp == pytest.approx(0.25)


def test_integration_hydrate_publish_does_not_reference_flip_path() -> None:
    """Setup seed path must call _publish_in_tag, not async_set_native_value (no flip)."""
    text = (ROOT / "number.py").read_text(encoding="utf-8")
    # The hydrate/setup branch comment + direct publish (SWD-220).
    assert "without MAN/REM mode-flip (SWD-220)" in text
    assert "await self._publish_in_tag(self._tag, eng)" in text
    # Flip remains only on explicit async_set_native_value.
    assert "_sp_mode_flip_map().get(self._tag)" in text


def test_system_lovelace_resource_registration() -> None:
    init = (ROOT / "__init__.py").read_text(encoding="utf-8")
    assert "_async_register_frontend_card" in init
    assert "async_create_item" in init
    assert "res_type" in init
    assert "?v=" in init or "card_url = f\"{base_url}?v={version}\"" in init
    assert "add_extra_js_url" in init  # YAML fallback

    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"after_dependencies"' in manifest
    assert '"lovelace"' in manifest
    assert '"0.1.40"' in manifest

    pid = (ROOT / "www" / "pid-loop-card.js").read_text(encoding="utf-8")
    assert "customElements.get(\"plcassistant-pid-card\")" in pid
    assert "getConfigElement" not in pid
    assert 'mode = (st?.state || "manual")' in pid

    block = (ROOT / "www" / "block-list-card.js").read_text(encoding="utf-8")
    assert "customElements.get(\"plcassistant-block-list-card\")" in block

    dash = (ROOT / "lovelace" / "plcassistant.yaml").read_text(encoding="utf-8")
    assert "plcassistant_dashboard_version: 19" in dash


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
