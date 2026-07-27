"""PLCAssistant thin integration constants (SWD-126).

No Home Assistant import at module import time beyond what __init__ needs —
topic helpers mirror ``plcassistant.io.mqtt_topics`` for HA Core (which may
not have the Soft-PLC package installed).
"""

DOMAIN = "plcassistant"
DEFAULT_INSTANCE_ID = "default"
DEFAULT_MQTT_BROKER = "core-mosquitto"
DEFAULT_MQTT_PORT = 1883
TOPIC_ROOT = "plcassistant"
CONF_INSTANCE_ID = "instance_id"
CONF_MQTT_BROKER = "mqtt_broker"
CONF_MQTT_PORT = "mqtt_port"
CONF_BINDINGS = "bindings"

# Service names exposed to operators (Start / Stop / Reset).
SERVICE_START = "start"
SERVICE_STOP = "stop"
SERVICE_RESET = "reset"
