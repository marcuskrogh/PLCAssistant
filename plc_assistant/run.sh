#!/usr/bin/env sh
# PLCAssistant HA App entry (SWD-123 / SWD-84 / SWD-128 / SWD-129).
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
APP_VERSION_FILE="${PLCASSISTANT_APP_VERSION_FILE:-/usr/share/plcassistant/APP_VERSION}"
MIGRATE_SCRIPT="${PLCASSISTANT_MIGRATE_SCRIPT:-/usr/share/plcassistant/migrate_legacy_mqtt_subscribe.py}"
INTEGRATION_STAMP="${DATA_DIR}/bundled_integration_from_app"

mkdir -p "${DATA_DIR}"

# Supervisor writes App options here; runtime parses mqtt_* / instance_id.
if [ -f "${OPTIONS_PATH}" ]; then
  export PLCASSISTANT_OPTIONS_PATH="${OPTIONS_PATH}"
fi
export PLCASSISTANT_PROGRAM_PATH="${PROGRAM_PATH}"
export PLCASSISTANT_HA_RUNTIME=1

app_version() {
  if [ -f "${APP_VERSION_FILE}" ]; then
    tr -d '[:space:]' < "${APP_VERSION_FILE}"
  else
    printf '%s\n' "unknown"
  fi
}

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

dst_has_legacy_hass_components() {
  [ -f "${INTEGRATION_DST}/__init__.py" ] || return 1
  grep -q "hass\\.components" "${INTEGRATION_DST}/__init__.py"
}

# Rewrite pre-0.1.5 mqtt subscribe that uses removed hass.components.
# Runs even when the App image itself is still a stale Docker layer.
migrate_legacy_mqtt_subscribe() {
  [ -f "${INTEGRATION_DST}/__init__.py" ] || return 0
  if [ -f "${MIGRATE_SCRIPT}" ]; then
    python3 "${MIGRATE_SCRIPT}" "${INTEGRATION_DST}/__init__.py"
  else
    # Local pytest / repo checkout: script lives next to run.sh.
    python3 "$(dirname "$0")/migrate_legacy_mqtt_subscribe.py" \
      "${INTEGRATION_DST}/__init__.py"
  fi
}

needs_integration_sync() {
  ver="$(app_version)"
  if [ ! -f "${INTEGRATION_STAMP}" ] || [ "$(cat "${INTEGRATION_STAMP}")" != "${ver}" ]; then
    echo "PLCAssistant: App version stamp ${ver} requires thin-integration sync."
    return 0
  fi
  if dst_has_legacy_hass_components; then
    echo "PLCAssistant: installed integration still uses hass.components; forcing sync."
    return 0
  fi
  if ! integration_up_to_date; then
    return 0
  fi
  return 1
}

# Copy bundled thin integration into HA config.
# Critical steps use `|| return 1` (errexit alone is unreliable when the caller
# temporarily disables it). Soft-PLC start must not abort if install fails.
install_thin_integration() {
  if [ ! -d "${HA_CONFIG}" ]; then
    echo "PLCAssistant: HA config not mounted at ${HA_CONFIG}; skip integration install."
    return 0
  fi
  if [ ! -d "${INTEGRATION_SRC}" ]; then
    echo "PLCAssistant: bundled integration missing at ${INTEGRATION_SRC}; skip install."
    # Still try to migrate whatever is already on disk (stale-image escape hatch).
    if dst_has_legacy_hass_components; then
      migrate_legacy_mqtt_subscribe || return 1
      date -u +"%Y-%m-%dT%H:%M:%SZ" > "${DATA_DIR}/integration_needs_core_restart" || true
    fi
    return 0
  fi

  if ! needs_integration_sync; then
    # Legacy hass.components already forces sync above, so this path is clean.
    echo "PLCAssistant: thin integration already up to date at ${INTEGRATION_DST}"
    rm -f "${DATA_DIR}/integration_needs_core_restart"
    return 0
  fi

  mkdir -p "${HA_CONFIG}/custom_components" || {
    echo "PLCAssistant: failed to create ${HA_CONFIG}/custom_components" >&2
    return 1
  }

  tmp="${INTEGRATION_DST}.new"
  bak="${INTEGRATION_DST}.bak"
  rm -rf "${tmp}" "${bak}"
  mkdir -p "${tmp}" || {
    echo "PLCAssistant: failed to create staging dir ${tmp}" >&2
    return 1
  }
  # Prefer cp -a over a tar pipe (no pipefail required on dash).
  cp -a "${INTEGRATION_SRC}/." "${tmp}/" || {
    echo "PLCAssistant: failed to stage integration from ${INTEGRATION_SRC}" >&2
    rm -rf "${tmp}"
    return 1
  }
  [ -f "${tmp}/manifest.json" ] || {
    echo "PLCAssistant: staged integration missing manifest.json" >&2
    rm -rf "${tmp}"
    return 1
  }

  if [ -e "${INTEGRATION_DST}" ]; then
    mv "${INTEGRATION_DST}" "${bak}" || {
      echo "PLCAssistant: failed to move existing integration aside" >&2
      rm -rf "${tmp}"
      return 1
    }
  fi
  if ! mv "${tmp}" "${INTEGRATION_DST}"; then
    echo "PLCAssistant: failed to activate staged integration at ${INTEGRATION_DST}" >&2
    rm -rf "${tmp}"
    if [ -e "${bak}" ]; then
      mv "${bak}" "${INTEGRATION_DST}" || \
        echo "PLCAssistant: also failed to restore previous integration" >&2
    fi
    return 1
  fi
  rm -rf "${bak}"

  # If the App image itself is stale, bundled SRC may still be broken — migrate DST.
  if dst_has_legacy_hass_components; then
    migrate_legacy_mqtt_subscribe || {
      echo "PLCAssistant: failed to migrate hass.components subscribe path" >&2
      return 1
    }
  fi

  # Drop any leftover bytecode from previous installs.
  rm -rf "${INTEGRATION_DST}/__pycache__"

  echo "PLCAssistant: thin integration installed/updated at ${INTEGRATION_DST}"
  echo "PLCAssistant: Restart Home Assistant Core, then add PLCAssistant under Devices & services (if not already)."
  printf '%s\n' "$(app_version)" > "${INTEGRATION_STAMP}" || \
    echo "PLCAssistant: warning: could not write ${INTEGRATION_STAMP}" >&2
  date -u +"%Y-%m-%dT%H:%M:%SZ" > "${DATA_DIR}/integration_needs_core_restart" || \
    echo "PLCAssistant: warning: could not write integration_needs_core_restart" >&2
  return 0
}

# Never abort Soft-PLC start on integration copy failure. A crash-loop here holds
# Supervisor's per-App job group and surfaces "Another job is running" / "not running"
# when the user tries to configure or restart the App.
set +e
install_thin_integration
install_rc=$?
set -e
if [ "${install_rc}" -ne 0 ]; then
  echo "PLCAssistant: thin integration install failed; continuing App start." >&2
fi

exec python3 -m plcassistant.app \
  --host "${HOST}" \
  --port "${PORT}" \
  --program-path "${PROGRAM_PATH}" \
  --options-path "${OPTIONS_PATH}" \
  --ha-runtime
