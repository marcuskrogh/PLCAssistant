"""Constants for PLCAssistant integration."""

from homeassistant.const import Platform

DOMAIN = "plcassistant"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

CONF_ADDON_URL = "addon_url"
CONF_TOKEN = "token"
CONF_SCAN_PERIOD_MS = "scan_period_ms"

DEFAULT_SCAN_PERIOD_MS = 100
DEFAULT_NAME = "PLCAssistant"

STORAGE_KEY = f"{DOMAIN}.bindings"
STORAGE_VERSION = 1

SERVICE_RELOAD = "reload"
SERVICE_START = "start"
SERVICE_STOP = "stop"

ATTR_BINDINGS = "bindings"
