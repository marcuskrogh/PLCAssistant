"""SWD-146: integration dynamics core + skid plant simulator (HA-free)."""

from __future__ import annotations

import ast
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CC = ROOT / "custom_components" / "plcassistant"
DYN = CC / "dynamics"

# Load dynamics via the thin-integration path (avoid colliding with App package).
if str(CC) not in sys.path:
    sys.path.insert(0, str(CC))


def test_dynamics_package_layout_ha_free() -> None:
    assert (DYN / "__init__.py").is_file()
    assert (DYN / "core.py").is_file()
    assert (DYN / "skid.py").is_file()
    assert (DYN / "plant.py").is_file()
    assert (DYN / "simulator.py").is_file()
    for name in ("core.py", "skid.py", "plant.py", "__init__.py"):
        text = (DYN / name).read_text(encoding="utf-8")
        assert "homeassistant" not in text
    sim = (DYN / "simulator.py").read_text(encoding="utf-8")
    assert "homeassistant" in sim
    init = (DYN / "__init__.py").read_text(encoding="utf-8")
    assert "simulator" not in init


def test_parse_scan_period_s() -> None:
    from dynamics.core import parse_scan_period_s

    assert parse_scan_period_s({"scan_period_s": 0.05}) == pytest.approx(0.05)
    assert parse_scan_period_s('{"state":"running","scan_period_s":0.2}') == pytest.approx(
        0.2
    )
    assert parse_scan_period_s({"scan_period_s": -1}) == pytest.approx(0.1)
    assert parse_scan_period_s({"scan_period_s": "nope"}) == pytest.approx(0.1)
    assert parse_scan_period_s(None) == pytest.approx(0.1)


def test_skid_oracle_matches_mock_process() -> None:
    """Skid preset stays within tight tolerance of wedge MockProcess."""
    from dynamics.skid import SkidModel
    from plcassistant.wedge.process import MockProcess, ProcessConfig

    oracle = MockProcess(ProcessConfig())
    model = SkidModel()
    cmds = [0.0, 40.0, 40.0, 80.0, 0.0, 0.0]
    dt = 0.1
    for cmd in cmds * 5:
        o = oracle.step(dt, cmd)
        model.set_input("cmd_speed", cmd)
        s = model.step(dt)
        assert s["h_tank"] == pytest.approx(o.lt_tank, abs=1e-9)
        assert s["h_res"] == pytest.approx(o.lt_res, abs=1e-9)
        assert s["ft_inlet"] == pytest.approx(o.ft_inlet, abs=1e-9)
        assert s["sc_pump"] == pytest.approx(o.sc_pump, abs=1e-9)


def test_plant_simulator_publishes_and_moves() -> None:
    from dynamics.plant import PlantSimulator

    published: dict[str, dict] = {}

    def publish(tag: str, payload: str) -> None:
        published[tag] = json.loads(payload)

    plant = PlantSimulator.for_preset(publish, preset="skid")
    outs = plant.publish_now()
    assert outs["LT_TANK"] == pytest.approx(0.15)
    assert outs["LT_RES"] == pytest.approx(0.20)
    assert outs["FT_INLET"] == pytest.approx(0.0)
    assert set(published) == {"LT_TANK", "LT_RES", "FT_INLET"}

    tank0 = outs["LT_TANK"]
    plant.apply_cmd_speed(60.0)
    plant.tick(1.0)
    assert plant.frozen is True
    assert plant.model.outputs()["LT_TANK"] == pytest.approx(tank0)

    plant.apply_status_payload({"state": "running", "scan_period_s": 0.1})
    assert plant.frozen is False
    assert plant.period_s == pytest.approx(0.1)
    for _ in range(30):
        plant.tick(0.1)
    assert published["FT_INLET"]["value"] > 0.5
    assert published["LT_TANK"]["value"] != pytest.approx(tank0, abs=1e-4)

    tank1 = published["LT_TANK"]["value"]
    plant.apply_status_payload({"state": "offline", "scan_period_s": 0.1})
    plant.tick(1.0)
    assert plant.frozen is True
    assert plant.model.outputs()["LT_TANK"] == pytest.approx(tank1)


def test_plant_number_nudge_and_cmd_watchdog() -> None:
    from dynamics.plant import PlantSimulator

    published: dict[str, dict] = {}

    def publish(tag: str, payload: str) -> None:
        published[tag] = json.loads(payload)

    plant = PlantSimulator.for_preset(publish)
    plant.apply_status_payload('{"state":"stopped","scan_period_s":0.1}')
    plant.set_output_tag("LT_TANK", 0.30)
    assert published["LT_TANK"]["value"] == pytest.approx(0.30)

    plant.apply_cmd_speed(50.0, mono=100.0)
    plant.tick(0.1, mono=100.1)
    plant.tick(0.1, mono=103.0)
    assert plant.model._inputs["cmd_speed"] == pytest.approx(0.0)


def test_closed_loop_held_process_consumes_plant_in() -> None:
    """Soft-PLC HeldProcess + plant simulator MQTT-style coupling (in-memory)."""
    from dynamics.plant import PlantSimulator
    from plcassistant.app.default_image import declare_default_image
    from plcassistant.app.skid_scan import SkidImageLogic
    from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
    from plcassistant.io.mqtt_topics import tag_in_topic
    from plcassistant.io.quality import QualityStatus
    from plcassistant.wedge.process import HeldProcess

    bus = InMemoryMqttBus()
    image = declare_default_image()
    bridge = MqttIoBridge(bus, instance_id="default")
    bridge.start()
    logic = SkidImageLogic(period_s=0.1)
    assert isinstance(logic.skid.process, HeldProcess)

    def publish(tag: str, payload: str) -> None:
        bus.publish(tag_in_topic("default", tag), payload.encode("utf-8"))

    plant = PlantSimulator.for_preset(publish)
    plant.apply_status_payload({"state": "running", "scan_period_s": 0.1})
    plant.publish_now()
    bridge.apply_inputs(image, clear=False)

    tank0 = float(image.get_value("LT_TANK"))
    assert tank0 == pytest.approx(0.15)

    image.apply_input("SP_LEVEL_REQ", 0.25, QualityStatus.GOOD)
    logic.enqueue_operator("start")
    for _ in range(40):
        bridge.apply_inputs(image, clear=False)
        logic(image)
        cmd = float(image.get_value("CMD_SPEED") or 0.0)
        plant.apply_cmd_speed(cmd)
        plant.tick(0.1)

    assert float(image.get_value("FT_INLET")) > 0.1
    assert float(image.get_value("LT_TANK")) != pytest.approx(tank0, abs=1e-3)
    assert float(image.get_value("CMD_SPEED")) > 0.0
    assert isinstance(logic.skid.process, HeldProcess)


def test_integration_wires_plant_simulator_lifecycle() -> None:
    init_text = (CC / "__init__.py").read_text(encoding="utf-8")
    assert "HassPlantSimulator" in init_text
    assert "plant_simulator" in init_text
    tree = ast.parse(init_text)
    setup = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "async_setup_entry"
    )
    unload = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "async_unload_entry"
    )
    setup_src = ast.unparse(setup)
    unload_src = ast.unparse(unload)
    assert "HassPlantSimulator" in setup_src
    assert "async_start" in setup_src
    assert "status_payload" in setup_src
    assert "plant_simulator" in unload_src
    assert "async_stop" in unload_src

    number = (CC / "number.py").read_text(encoding="utf-8")
    assert "_simulator_owns" in number
    assert "set_tag" in number
    assert "do not compete" in number
    # SWD-169: readable HMI values (BOX) + hydrate from plant + bus updates.
    assert "NumberMode.BOX" in number
    assert "_plant_in" in number or "plant_in" in number
    assert "outputs()" in number
    assert "async_write_ha_state" in number

    sim = (CC / "dynamics" / "simulator.py").read_text(encoding="utf-8")
    assert "entry_id" in sim
    assert "_plant_in" in sim or "plant_in" in sim
    assert "async_fire" in sim
    init_text2 = (CC / "__init__.py").read_text(encoding="utf-8")
    assert "entry_id=entry.entry_id" in init_text2


def test_packaging_docs_mention_live_simulator() -> None:
    shape = (ROOT / "docs" / "packaging" / "01-shape.md").read_text(encoding="utf-8")
    assert "SWD-146" in shape
    assert "Owns" in shape
    assert "skid" in shape.lower() or "simulator" in shape.lower()
    # Gap language from SWD-145 must be retired once the simulator ships.
    assert "plant dark until then" not in shape.lower()
    assert "until swd-146, live process values stay static" not in shape.lower()
