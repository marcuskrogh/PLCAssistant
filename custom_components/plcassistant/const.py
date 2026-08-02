"""PLCAssistant thin integration constants (SWD-126 / SWD-230)."""

from __future__ import annotations

import math
from typing import Any

DOMAIN = "plcassistant"
DEFAULT_INSTANCE_ID = "default"
DEFAULT_MQTT_BROKER = "core-mosquitto"
DEFAULT_MQTT_PORT = 1883
TOPIC_ROOT = "plcassistant"
MQTT_QOS = 1
CONF_INSTANCE_ID = "instance_id"
CONF_MQTT_BROKER = "mqtt_broker"
CONF_MQTT_PORT = "mqtt_port"
CONF_BINDINGS = "bindings"
CONF_MOCK_MODE = "mock_mode"
CONF_DYNAMICS_PRESET = "dynamics_preset"
CONF_DYNAMICS_PARAMS = "dynamics_params"
DEFAULT_DYNAMICS_PRESET = "skid"

# HMI / Lovelace display precision — keep in sync with PID_DISPLAY_DIGITS in
# www/pid-loop-card.js (SWD-230).
DISPLAY_PRECISION = 2

SERVICE_START = "start"
SERVICE_STOP = "stop"
SERVICE_RESET = "reset"
SERVICE_SET_DYNAMICS_PRESET = "set_dynamics_preset"


def round_display(value: Any, digits: int = DISPLAY_PRECISION) -> float | None:
    """Round a numeric faceplate/Process value to ``digits`` dp, or None if absent.

    SWD-230: shared by compound PID attributes, sensors, and Numbers so 2dp
    policy cannot drift across modules.
    """
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(num):
        return None
    return round(num, digits)
