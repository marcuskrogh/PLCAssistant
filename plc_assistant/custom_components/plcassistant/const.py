"""PLCAssistant thin integration constants (SWD-126)."""

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

SERVICE_START = "start"
SERVICE_STOP = "stop"
SERVICE_RESET = "reset"
SERVICE_SET_DYNAMICS_PRESET = "set_dynamics_preset"
