"""SWD-369: ISA-101 / DCS analog-controller PID faceplate."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
from pathlib import Path

import pytest

from plcassistant.io.pid_loop import (
    FLOW_LOOP,
    LEVEL_LOOP,
    SpSourceMode,
    apply_co_write,
    faceplate_from_image_tags,
    is_output_manual,
    operator_write_target,
)

ROOT = Path("custom_components/plcassistant")
CARD = ROOT / "www" / "pid-loop-card.js"
FACEPLATE = Path("docs/io/06-pid-faceplate.md")
JS_CONTRACT = Path("tests/js/pid_faceplate_contract.test.mjs")


def test_unit_dcs_mode_write_targets() -> None:
    assert operator_write_target(SpSourceMode.MANUAL) == "co"
    assert operator_write_target("auto") == "sp"
    assert operator_write_target("rem") is None
    assert operator_write_target("cas") is None
    assert is_output_manual(0) is True
    assert is_output_manual(1) is False
    held = apply_co_write(value=3.5)
    assert held["mode"] == "manual"
    assert held["cv"] == pytest.approx(3.5)
    assert held["write_target"] == "co"


def test_unit_faceplate_defaults_automatic_and_co_man() -> None:
    fp = faceplate_from_image_tags(LEVEL_LOOP, {})
    assert fp["mode"] == "automatic"
    assert fp["write_target"] == "sp"
    assert fp["tags"]["co_man"] == "CO_LEVEL_MAN"
    assert LEVEL_LOOP.co_man == "CO_LEVEL_MAN"
    assert FLOW_LOOP.co_man == "CO_FLOW_MAN"
    man = faceplate_from_image_tags(LEVEL_LOOP, {"LEVEL_MODE": 0.0, "CO_LEVEL_MAN": 2.5})
    assert man["mode"] == "manual"
    assert man["write_target"] == "co"
    assert man["co_man"] == pytest.approx(2.5)


def test_unit_level_and_flow_mode_defaults_are_automatic() -> None:
    from plcassistant.io.datablock import default_tank_datablock_catalog

    block = default_tank_datablock_catalog().get("DB_Tank")
    assert block is not None
    assert float(block.tags["LEVEL_MODE"].default) == pytest.approx(1.0)
    assert float(block.tags["FLOW_MODE"].default) == pytest.approx(1.0)
    assert "CO_LEVEL_MAN" in block.tags
    assert "CO_FLOW_MAN" in block.tags
    bindings = {b.tag for b in block.bindings}
    assert "CO_LEVEL_MAN" in bindings
    assert "CO_FLOW_MAN" in bindings

    meta = (ROOT / "number.py").read_text(encoding="utf-8")
    level = meta.split('"LEVEL_MODE":', 1)[1].split('"CO_LEVEL_MAN":', 1)[0]
    assert '"default": 1.0' in level
    assert "plcassistant_co_level_man" in meta
    assert "plcassistant_co_flow_man" in meta


def test_unit_pid_card_analog_controller_geometry() -> None:
    text = CARD.read_text(encoding="utf-8")
    assert 'data-bar="pv"' in text
    assert 'data-bar="sp"' in text
    assert 'data-bar="co"' in text
    assert "pid-vbars" in text
    assert "pid-vbar-track" in text
    assert "pid-hbar" in text
    assert "pidOperatorWriteTarget" in text
    assert "pidBarValueFromPointer" in text
    assert 'data-apply="co"' in text
    assert 'data-writable="1"' in text
    assert "--pid-man" not in text
    assert "--pid-auto" not in text
    assert "--pid-rem" not in text
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in text
    assert "Tap to adjust" in text
    assert 'getCardSize() {\n    return 3;' in text or "return 3;" in text
    assert 'closest("button[data-mode]")' in text
    # Face modes plus dialog modes; still button[data-mode] only.
    assert 'data-mode="0"' in text
    assert "pid-face-modes" in text


def test_unit_faceplate_doc_dcs_modes() -> None:
    text = FACEPLATE.read_text(encoding="utf-8")
    assert "output Manual" in text
    assert "ISA-101" in text
    assert "ISA-112" in text
    assert "CO_LEVEL_MAN" in text
    assert "CO_FLOW_MAN" in text
    assert "two vertical" in text.lower() or "vertical bars" in text.lower()
    assert "horizontal" in text.lower()
    assert "climate-inspired" not in text


def test_system_level_auto_still_computes_cascade_co() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 1.0),
        ("FLOW_MODE", 1.0),
        ("SP_LEVEL_REQ", 0.30),
        ("LT_TANK", 0.15),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    for _ in range(30):
        logic(image)
    assert image.get_value("MODE") == "RUNNING"
    assert float(image.get_value("SP_FLOW_AUTO")) > 0.5
    assert float(image.get_value("CMD_SPEED")) > 0.0


def test_system_level_man_holds_co() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 0.0),
        ("FLOW_MODE", 1.0),
        ("CO_LEVEL_MAN", 3.0),
        ("SP_LEVEL_REQ", 0.30),
        ("LT_TANK", 0.15),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    for _ in range(20):
        logic(image)
    assert float(image.get_value("SP_FLOW_AUTO")) == pytest.approx(3.0, abs=0.15)


def test_system_flow_man_holds_cmd_from_co() -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 1.0),
        ("FLOW_MODE", 0.0),
        ("SP_LEVEL_REQ", 0.15),
        ("CO_FLOW_MAN", 40.0),
        ("LT_TANK", 0.15),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    for _ in range(20):
        logic(image)
    assert float(image.get_value("CMD_SPEED")) == pytest.approx(40.0, abs=1.0)


def test_system_faceplate_js_write_target_contract() -> None:
    assert JS_CONTRACT.is_file()
    proc = subprocess.run(
        [
            "node",
            "--experimental-default-type=module",
            str(JS_CONTRACT),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )
    if proc.returncode != 0:
        pytest.fail(
            "pid faceplate JS contract failed:\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )


def test_system_app_version_is_0_1_58() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.58"' in manifest
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.58"' in config
    docker = Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.58" in docker
    dual = Path("plc_assistant/custom_components/plcassistant/manifest.json")
    assert '"0.1.58"' in dual.read_text(encoding="utf-8")


def test_dual_tree_pid_card_synced() -> None:
    app_card = Path("plc_assistant/custom_components/plcassistant/www/pid-loop-card.js")
    assert CARD.read_bytes() == app_card.read_bytes()
    ha_pid = (ROOT / "pid_loop.py").read_text(encoding="utf-8")
    assert '"cv_man_entity": "number.plcassistant_co_level_man"' in ha_pid
    assert '"co_man": "CO_LEVEL_MAN"' in ha_pid


def test_unit_ha_pid_loop_parses() -> None:
    """Compound PID sensors must load: one real ``_payload_value``, no stub."""
    src_path = ROOT / "pid_loop.py"
    tree = ast.parse(src_path.read_text(encoding="utf-8"), filename=str(src_path))
    defs = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_payload_value"
    ]
    assert len(defs) == 1
    assert any(isinstance(node, ast.If) for node in defs[0].body)
    app_path = Path("plc_assistant/custom_components/plcassistant/pid_loop.py")
    ast.parse(app_path.read_text(encoding="utf-8"), filename=str(app_path))


def test_unit_mode_zero_seeds_co_before_publish() -> None:
    """Bumpless MAN: seed live CO into CO_*_MAN before publishing MODE=0."""
    body = (ROOT / "number.py").read_text(encoding="utf-8").split(
        "async def async_set_native_value", 1
    )[1]
    seed = body.find("_seed_co_hold()")
    publish = body.find("_publish_in_tag(self._tag, eng)")
    assert 0 <= seed < publish


def _ha_store_mod():
    spec = importlib.util.spec_from_file_location(
        "test_swd184_acceptance",
        Path("tests/test_swd184_acceptance.py"),
    )
    assert spec is not None and spec.loader is not None
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper._load_store_mod()


def test_integration_load_store_merges_missing_co_man(tmp_path: Path) -> None:
    """Existing datablocks.json gains CO_*_MAN without overwriting user tags."""
    mod = _ha_store_mod()
    payload = mod.default_store_payload()
    tank = payload["datablocks"]["DB_Tank"]
    tank["tags"]["LEVEL_MODE"]["default"] = 0.0
    for name in ("CO_LEVEL_MAN", "CO_FLOW_MAN"):
        tank["tags"].pop(name, None)
        tank["bindings"] = [b for b in tank["bindings"] if b["tag"] != name]
    mod.save_store(tmp_path, payload)

    reloaded = mod.load_store(tmp_path)
    tank2 = reloaded["datablocks"]["DB_Tank"]
    assert "CO_LEVEL_MAN" in tank2["tags"]
    assert "CO_FLOW_MAN" in tank2["tags"]
    bound = {b["tag"] for b in tank2["bindings"]}
    assert "CO_LEVEL_MAN" in bound
    assert "CO_FLOW_MAN" in bound
    assert tank2["tags"]["LEVEL_MODE"]["default"] == 0.0
    persisted = mod.load_store(tmp_path)
    assert "CO_LEVEL_MAN" in persisted["datablocks"]["DB_Tank"]["tags"]
