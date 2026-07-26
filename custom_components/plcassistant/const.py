"""Constants for PLCAssistant integration."""

from homeassistant.const import Platform

DOMAIN = "plcassistant"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

CONF_ADDON_URL = "addon_url"
CONF_TOKEN = "token"
CONF_SCAN_PERIOD_MS = "scan_period_ms"
CONF_DEFAULT_UNAVAILABLE_POLICY = "default_unavailable_policy"
CONF_DEFAULT_ON_BRIDGE_FAULT = "default_on_bridge_fault"

DEFAULT_SCAN_PERIOD_MS = 100
DEFAULT_UNAVAILABLE_POLICY = "hold_last"
DEFAULT_ON_BRIDGE_FAULT = "hold_last_command"
DEFAULT_NAME = "PLCAssistant"

STORAGE_KEY = f"{DOMAIN}.bindings"
STORAGE_VERSION = 1

SERVICE_RELOAD = "reload"
SERVICE_START = "start"
SERVICE_STOP = "stop"

ATTR_ENTRY_ID = "entry_id"
ATTR_BINDINGS = "bindings"

UNAVAILABLE_POLICY_CHOICES = ("hold_last", "force_zero", "force_value", "fault")
BRIDGE_FAULT_CHOICES = ("hold_last_command", "safe_off", "noop")
