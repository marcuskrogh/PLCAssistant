#!/usr/bin/env bash
# Copy the installable Python package + thin integration into HA App build contexts.
# Supervisor docker-builds only the App folder, so those trees must live there.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

copy_tree() {
  local src="$1"
  local dest="$2"
  mkdir -p "${dest}"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude '__pycache__/' \
      --exclude '*.py[cod]' \
      --exclude '.pytest_cache/' \
      "${src}/" "${dest}/"
  else
    # Clear destination contents without removing dest itself when empty-safe.
    find "${dest}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    (cd "${src}" && tar cf - \
      --exclude='__pycache__' \
      --exclude='*.pyc' \
      --exclude='*.pyo' \
      --exclude='.pytest_cache' \
      .) | (cd "${dest}" && tar xf -)
  fi
}

sync_into() {
  local dest="$1"
  mkdir -p "${dest}"

  rm -rf "${dest}/plcassistant"
  copy_tree "${ROOT}/plcassistant" "${dest}/plcassistant"
  cp "${ROOT}/pyproject.toml" "${dest}/pyproject.toml"

  rm -rf "${dest}/custom_components"
  mkdir -p "${dest}/custom_components/plcassistant"
  copy_tree \
    "${ROOT}/custom_components/plcassistant" \
    "${dest}/custom_components/plcassistant"

  echo "Synced package + integration into ${dest}"
}

sync_into "${ROOT}/plc_assistant"
sync_into "${ROOT}/ha_app/plcassistant"
