#!/usr/bin/env sh
# PLCAssistant HA App entry (SWD-123).
# Supervisor mounts persistent storage at /data.
set -eu

DATA_DIR="${PLCASSISTANT_DATA:-/data}"
PROGRAM_PATH="${DATA_DIR}/program.json"
OPTIONS_PATH="${DATA_DIR}/options.json"
HOST="${PLCASSISTANT_HOST:-0.0.0.0}"
PORT="${PLCASSISTANT_PORT:-8099}"

mkdir -p "${DATA_DIR}"

# Export MQTT / instance options for future bridge wiring (read by helpers).
if [ -f "${OPTIONS_PATH}" ]; then
  export PLCASSISTANT_OPTIONS_PATH="${OPTIONS_PATH}"
fi
export PLCASSISTANT_PROGRAM_PATH="${PROGRAM_PATH}"

# Bundled thin integration is documented for a one-time copy into HA
# config/custom_components (see ha_app/INSTALL.md). Auto-copy requires a
# writable HA config mount and is intentionally not performed here in v1.

exec python3 -m plcassistant.app --host "${HOST}" --port "${PORT}" --program-path "${PROGRAM_PATH}"
