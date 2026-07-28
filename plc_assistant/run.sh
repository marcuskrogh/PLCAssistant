#!/usr/bin/env sh
# PLCAssistant HA App entry (SWD-123 / SWD-84 fix-forward).
# Supervisor mounts persistent storage at /data and HA config at /homeassistant.
set -eu

DATA_DIR="${PLCASSISTANT_DATA:-/data}"
PROGRAM_PATH="${DATA_DIR}/program.json"
OPTIONS_PATH="${DATA_DIR}/options.json"
HOST="${PLCASSISTANT_HOST:-0.0.0.0}"
PORT="${PLCASSISTANT_PORT:-8099}"
HA_CONFIG="${PLCASSISTANT_HA_CONFIG:-/homeassistant}"
INTEGRATION_SRC="${PLCASSISTANT_INTEGRATION_SRC:-/usr/share/plcassistant/custom_components/plcassistant}"
INTEGRATION_DST="${HA_CONFIG}/custom_components/plcassistant"

mkdir -p "${DATA_DIR}"

# Supervisor writes App options here; runtime parses mqtt_* / instance_id.
if [ -f "${OPTIONS_PATH}" ]; then
  export PLCASSISTANT_OPTIONS_PATH="${OPTIONS_PATH}"
fi
export PLCASSISTANT_PROGRAM_PATH="${PROGRAM_PATH}"
export PLCASSISTANT_HA_RUNTIME=1

integration_up_to_date() {
  [ -d "${INTEGRATION_DST}" ] || return 1
  python3 - "${INTEGRATION_SRC}" "${INTEGRATION_DST}" <<'PY'
import sys
from pathlib import Path

def files(root: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        out[str(path.relative_to(root))] = path.read_bytes()
    return out

sys.exit(0 if files(Path(sys.argv[1])) == files(Path(sys.argv[2])) else 1)
PY
}

install_thin_integration() {
  if [ ! -d "${HA_CONFIG}" ]; then
    echo "PLCAssistant: HA config not mounted at ${HA_CONFIG}; skip integration install."
    return 0
  fi
  if [ ! -d "${INTEGRATION_SRC}" ]; then
    echo "PLCAssistant: bundled integration missing at ${INTEGRATION_SRC}; skip install."
    return 0
  fi

  mkdir -p "${HA_CONFIG}/custom_components"

  needs_restart=1
  if integration_up_to_date; then
    needs_restart=0
  fi

  tmp="${INTEGRATION_DST}.new"
  rm -rf "${tmp}"
  mkdir -p "${tmp}"
  (cd "${INTEGRATION_SRC}" && tar cf - .) | (cd "${tmp}" && tar xf -)
  rm -rf "${INTEGRATION_DST}"
  mv "${tmp}" "${INTEGRATION_DST}"

  if [ "${needs_restart}" -eq 1 ]; then
    echo "PLCAssistant: thin integration installed/updated at ${INTEGRATION_DST}"
    echo "PLCAssistant: Restart Home Assistant Core, then add PLCAssistant under Devices & services (if not already)."
    date -u +"%Y-%m-%dT%H:%M:%SZ" > "${DATA_DIR}/integration_needs_core_restart"
  else
    echo "PLCAssistant: thin integration already up to date at ${INTEGRATION_DST}"
    rm -f "${DATA_DIR}/integration_needs_core_restart"
  fi
}

install_thin_integration

exec python3 -m plcassistant.app \
  --host "${HOST}" \
  --port "${PORT}" \
  --program-path "${PROGRAM_PATH}" \
  --options-path "${OPTIONS_PATH}" \
  --ha-runtime
