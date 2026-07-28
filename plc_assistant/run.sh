#!/usr/bin/env sh
# PLCAssistant HA App entry (SWD-123 / SWD-84 fix-forward).
# Supervisor mounts persistent storage at /data.
set -eu

DATA_DIR="${PLCASSISTANT_DATA:-/data}"
PROGRAM_PATH="${DATA_DIR}/program.json"
OPTIONS_PATH="${DATA_DIR}/options.json"
HOST="${PLCASSISTANT_HOST:-0.0.0.0}"
PORT="${PLCASSISTANT_PORT:-8099}"

mkdir -p "${DATA_DIR}"

# Supervisor writes App options here; runtime parses mqtt_* / instance_id.
if [ -f "${OPTIONS_PATH}" ]; then
  export PLCASSISTANT_OPTIONS_PATH="${OPTIONS_PATH}"
fi
export PLCASSISTANT_PROGRAM_PATH="${PROGRAM_PATH}"
export PLCASSISTANT_HA_RUNTIME=1

# Bundled thin integration: documented one-time copy into HA
# config/custom_components (see README.md). Not auto-copied in v1.

exec python3 -m plcassistant.app \
  --host "${HOST}" \
  --port "${PORT}" \
  --program-path "${PROGRAM_PATH}" \
  --options-path "${OPTIONS_PATH}" \
  --ha-runtime
