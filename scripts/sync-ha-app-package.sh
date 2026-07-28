#!/usr/bin/env bash
# Copy the installable Python package into HA App build contexts.
# Supervisor docker-builds only the App folder, so the package must live there.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

sync_into() {
  local dest="$1"
  mkdir -p "${dest}"
  rm -rf "${dest}/plcassistant"
  mkdir -p "${dest}/plcassistant"
  # Prefer rsync when available; fall back to tar to preserve layout.
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude '__pycache__/' \
      --exclude '*.py[cod]' \
      --exclude '.pytest_cache/' \
      "${ROOT}/plcassistant/" "${dest}/plcassistant/"
  else
    (cd "${ROOT}/plcassistant" && tar cf - \
      --exclude='__pycache__' \
      --exclude='*.pyc' \
      --exclude='*.pyo' \
      --exclude='.pytest_cache' \
      .) | (cd "${dest}/plcassistant" && tar xf -)
  fi
  cp "${ROOT}/pyproject.toml" "${dest}/pyproject.toml"
  echo "Synced package into ${dest}"
}

sync_into "${ROOT}/plc_assistant"
sync_into "${ROOT}/ha_app/plcassistant"
