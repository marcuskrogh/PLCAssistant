"""SWD-219: thin integration must not import Soft-PLC on HA Core setup path."""

from __future__ import annotations

import ast
import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path("custom_components/plcassistant")


def _load_ha_datablock_catalog():
    """Load HA-local catalog without putting custom_components on sys.path."""
    pkg = types.ModuleType("ha_plcassistant_datablocks")
    pkg.__path__ = [str((ROOT / "datablocks").resolve())]  # type: ignore[attr-defined]
    sys.modules["ha_plcassistant_datablocks"] = pkg

    binding_path = ROOT / "datablocks" / "binding_types.py"
    spec_b = importlib.util.spec_from_file_location(
        "ha_plcassistant_datablocks.binding_types",
        binding_path,
        submodule_search_locations=[],
    )
    assert spec_b and spec_b.loader
    mod_b = importlib.util.module_from_spec(spec_b)
    sys.modules["ha_plcassistant_datablocks.binding_types"] = mod_b
    spec_b.loader.exec_module(mod_b)

    catalog_path = ROOT / "datablocks" / "catalog.py"
    # Rewrite relative import target by exec under package name.
    src = catalog_path.read_text(encoding="utf-8")
    src = src.replace(
        "from .binding_types import Binding, BindingTable, TagDecl",
        "from ha_plcassistant_datablocks.binding_types import Binding, BindingTable, TagDecl",
    )
    spec_c = importlib.util.spec_from_file_location(
        "ha_plcassistant_datablocks.catalog",
        catalog_path,
    )
    assert spec_c and spec_c.loader
    mod_c = importlib.util.module_from_spec(spec_c)
    sys.modules["ha_plcassistant_datablocks.catalog"] = mod_c
    exec(compile(src, str(catalog_path), "exec"), mod_c.__dict__)
    return mod_c


def _forbidden_plcassistant_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "plcassistant" or alias.name.startswith("plcassistant."):
                    hits.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "plcassistant" or mod.startswith("plcassistant."):
                hits.append(f"from {mod}")
    return hits


def test_unit_ha_catalog_loads_without_softplc(monkeypatch: pytest.MonkeyPatch) -> None:
    """HA catalog must not require Soft-PLC on import."""
    import builtins

    real_import = builtins.__import__

    def _guard(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: ANN001
        if name == "plcassistant" or name.startswith("plcassistant."):
            raise ModuleNotFoundError(name)
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _guard)
    # Drop any already-imported Soft-PLC modules from this guarded load path.
    for key in [k for k in list(sys.modules) if k == "plcassistant" or k.startswith("plcassistant.")]:
        monkeypatch.delitem(sys.modules, key, raising=False)

    catalog = _load_ha_datablock_catalog()
    table = catalog.default_tank_datablock_catalog().binding_table_for(
        catalog.union_program_access_ids(catalog.default_program_datablock_access())
    )
    rows = catalog.binding_rows_from_table(table)
    assert len(rows) == 45
    assert {r["tag"] for r in rows} >= {
        "SP_LEVEL_REQ",
        "LEVEL_MODE",
        "CMD_SPEED",
        "CO_LEVEL_MAN",
        "CO_FLOW_MAN",
    }


def test_integration_softplc_ha_default_binding_parity() -> None:
    from plcassistant.io.datablock import (
        binding_rows_from_table as soft_rows_fn,
        default_program_datablock_access as soft_access,
        default_tank_datablock_catalog as soft_catalog,
        union_program_access_ids as soft_union,
    )

    ha = _load_ha_datablock_catalog()
    soft = soft_rows_fn(
        soft_catalog().binding_table_for(soft_union(soft_access()))
    )
    ha_rows = ha.binding_rows_from_table(
        ha.default_tank_datablock_catalog().binding_table_for(
            ha.union_program_access_ids(ha.default_program_datablock_access())
        )
    )
    assert soft == ha_rows


def test_system_thin_integration_datablock_modules_forbid_softplc_imports() -> None:
    checked = [
        ROOT / "__init__.py",
        ROOT / "datablocks" / "store.py",
        ROOT / "datablocks" / "http_api.py",
        ROOT / "datablocks" / "catalog.py",
        ROOT / "datablocks" / "binding_types.py",
    ]
    for path in checked:
        hits = _forbidden_plcassistant_imports(path)
        assert hits == [], f"{path}: unexpected Soft-PLC imports {hits}"


def test_system_init_uses_ha_local_catalog() -> None:
    text = (ROOT / "__init__.py").read_text(encoding="utf-8")
    assert "from .datablocks.catalog import" in text
    assert "from plcassistant.io.datablock" not in text
