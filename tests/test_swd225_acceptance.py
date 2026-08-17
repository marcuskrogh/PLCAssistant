"""SWD-225: Start still leaves PID CVs at 0 — file mirror + Apply→Skid sync."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path("custom_components/plcassistant")


def test_unit_file_runtime_mirrors_sp_flow_auto() -> None:
    text = Path("plcassistant/app/runtime.py").read_text(encoding="utf-8")
    write = text.split("def _write_ha_config_runtime", 1)[1].split(
        "def _apply_file_inputs", 1
    )[0]
    assert '"SP_FLOW_AUTO"' in write
    assert '"CMD_SPEED"' in write
    init = (ROOT / "__init__.py").read_text(encoding="utf-8")
    assert "SP_FLOW_AUTO" in init.split("_HMI_TAGS", 1)[1].split(")", 1)[0]


def test_unit_api_apply_syncs_live_skid() -> None:
    server = Path("plcassistant/app/server.py").read_text(encoding="utf-8")
    sync_def = server.split("def _sync_applied_project_to_runtime", 1)[1].split(
        "@property", 1
    )[0]
    assert 'mode: str = "restart"' in sync_def
    assert "live.hot_apply" in sync_def
    apply = server.split("def _handle_post_apply", 1)[1].split(
        "return Handler", 1
    )[0]
    assert '_sync_applied_project_to_runtime(mode="restart")' in apply
    assert '_sync_applied_project_to_runtime(mode="hot")' in apply
    sync_live = server.split("def _sync_program_to_live", 1)[1].split(
        "def _ensure_program_logs", 1
    )[0]
    assert "_sync_applied_project_to_runtime" in sync_live
    project_put = server.split('path == "/api/project"', 1)[1].split(
        "elif (parts := self._task_path_parts())", 1
    )[0]
    assert "_sync_applied_project_to_runtime(mode=mode)" in project_put


def test_system_missing_cascade_instances_still_drive_cv_on_start() -> None:
    """Empty/renamed program must not leave RUNNING with CV stuck at 0."""
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus
    from plcassistant.surface.model import Program, SoftPlcProject, Task

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 0.0),
        ("FLOW_MODE", 1.0),
        ("SP_LEVEL_MAN", 0.30),
        ("LT_TANK", 0.0),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    # Simulate a canvas Apply that wiped cascade instances from the live Skid.
    empty = SoftPlcProject(
        programs={
            "tank": Program(
                name="Tank", instances={}, wires=[], execution_order=[]
            )
        },
        tasks=[Task(task_id="main", priority=0, programs=["tank"])],
        scan_period_s=0.1,
    )
    assert logic.skid.program_loader is not None
    logic.skid.program_loader.restart_apply(empty)
    assert not logic.skid._cascade_instances_ready()
    logic.enqueue_operator("start")
    logic(image)
    assert image.get_value("MODE") == "RUNNING"
    for _ in range(25):
        logic(image)
    assert float(image.get_value("SP_FLOW_AUTO")) > 0.5
    assert float(image.get_value("CMD_SPEED")) > 0.0


def test_system_screenshot_level_man_pv0_drives_cvs() -> None:
    """Reproduce HMI screenshot: Level Man SP=0.3, PV=0, Flow Auto → CVs rise."""
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 0.0),
        ("FLOW_MODE", 1.0),
        ("SP_LEVEL_MAN", 0.30),
        ("LT_TANK", 0.0),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    logic(image)
    for _ in range(10):
        logic(image)
    assert float(image.get_value("SP_FLOW_AUTO")) > 0.5
    assert float(image.get_value("CMD_SPEED")) > 0.0
    assert float(image.get_value("SP_FLOW")) == pytest.approx(
        float(image.get_value("SP_FLOW_AUTO")), abs=1e-6
    )


def test_system_fallback_flow_man_keeps_level_cv_as_sp_flow_auto() -> None:
    """Missing cascade instances + Flow Man must not overwrite SP_FLOW_AUTO."""
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus
    from plcassistant.surface.model import Program, SoftPlcProject, Task

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 0.0),
        ("FLOW_MODE", 0.0),
        ("SP_LEVEL_MAN", 0.30),
        ("SP_FLOW_MAN", 2.0),
        ("LT_TANK", 0.0),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.5),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    empty = SoftPlcProject(
        programs={
            "tank": Program(
                name="Tank", instances={}, wires=[], execution_order=[]
            )
        },
        tasks=[Task(task_id="main", priority=0, programs=["tank"])],
        scan_period_s=0.1,
    )
    logic.skid.program_loader.restart_apply(empty)
    logic.enqueue_operator("start")
    logic(image)
    for _ in range(20):
        logic(image)
    level_cv = float(image.get_value("SP_FLOW_AUTO"))
    assert level_cv > 0.5
    # Active flow SP is Man; Level CV faceplate stays on cascade sp_flow.
    assert float(image.get_value("SP_FLOW")) == pytest.approx(2.0, abs=1e-6)
    assert level_cv != pytest.approx(2.0, abs=0.05)
    assert float(image.get_value("CMD_SPEED")) > 0.0


def test_system_hot_sync_does_not_rebumpless_while_running() -> None:
    """App hot-apply sync must not force live Skid restart bumpless to 0."""
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.server import AppState
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.quality import QualityStatus

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 0.0),
        ("FLOW_MODE", 1.0),
        ("SP_LEVEL_MAN", 0.30),
        ("LT_TANK", 0.0),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)
    logic = SkidImageLogic(period_s=0.1)
    logic.enqueue_operator("start")
    for _ in range(15):
        logic(image)
    cmd_before = float(image.get_value("CMD_SPEED"))
    assert cmd_before > 0.0

    from types import SimpleNamespace

    loop = SimpleNamespace(logic=logic)
    # OperatorRuntime._scan_loop reads ``lifecycle.loop`` (not a method).
    lifecycle = SimpleNamespace(loop=loop)

    state = AppState()
    state.superuser_hot_apply = True
    state.operator.attach(lifecycle)
    # Seed App loader from the live Skid project, then hot-sync a clone.
    live = logic.skid.program_loader
    assert live is not None and live.project is not None
    state.loader.restart_apply(live.project)
    state._reapply_library_state()
    state.saved_project = live.project
    assert state._live_skid_loader() is live
    # Hot sync of unchanged structure must preserve running CVs.
    state._sync_applied_project_to_runtime(mode="hot")
    logic(image)
    cmd_after = float(image.get_value("CMD_SPEED"))
    assert cmd_after > 0.0
    assert abs(cmd_after - cmd_before) < max(0.5, 0.25 * cmd_before)

    # Contrast: restart sync re-bumplesses toward 0 on the next scan.
    state._sync_applied_project_to_runtime(mode="restart")
    logic(image)
    assert float(image.get_value("CMD_SPEED")) < cmd_after * 0.5



def test_system_file_runtime_snapshot_includes_level_cv(tmp_path, monkeypatch) -> None:
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.runtime import MqttScanLoop
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io import ha_config_bridge as bridge
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.io.quality import QualityStatus

    def _write(snapshot, root=None):
        return bridge.write_runtime_snapshot(snapshot, root=tmp_path)

    monkeypatch.setattr(
        "plcassistant.app.runtime.write_runtime_snapshot", _write
    )

    image = declare_default_image()
    image.begin_inputs()
    for tag, val in (
        ("LEVEL_MODE", 0.0),
        ("FLOW_MODE", 1.0),
        ("SP_LEVEL_MAN", 0.30),
        ("LT_TANK", 0.0),
        ("LT_RES", 0.20),
        ("FT_INLET", 0.0),
    ):
        image.apply_input(tag, val, QualityStatus.GOOD)

    logic = SkidImageLogic(period_s=0.1)
    mqtt = MqttIoBridge(InMemoryMqttBus(), instance_id="default")
    loop = MqttScanLoop(mqtt, image, logic=logic, period_s=0.1)
    logic.enqueue_operator("start")
    for _ in range(16):
        loop.scan_once()
    snap = bridge.read_runtime_snapshot(root=tmp_path)
    assert snap is not None
    tags = snap.get("tags") or {}
    assert "SP_FLOW_AUTO" in tags
    assert float(tags["SP_FLOW_AUTO"]["value"]) > 0.5
    assert float(tags["CMD_SPEED"]["value"]) > 0.0


def test_system_app_version_0_1_45() -> None:
    manifest = (ROOT / "manifest.json").read_text(encoding="utf-8")
    assert '"0.1.55"' in manifest
    config = Path("plc_assistant/config.yaml").read_text(encoding="utf-8")
    assert 'version: "0.1.55"' in config
    docker = Path("plc_assistant/Dockerfile").read_text(encoding="utf-8")
    assert "BUILD_VERSION=0.1.55" in docker
