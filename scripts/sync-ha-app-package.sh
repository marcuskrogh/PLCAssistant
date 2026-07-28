#!/usr/bin/env bash
# Copy the installable Python package + thin integration into the HA App build context.
# Supervisor docker-builds only the App folder (plc_assistant/), so those trees must live there.
# Do NOT place a second config.yaml elsewhere in the repo — Supervisor discovers Apps
# recursively and duplicate slug "plcassistant" breaks update detection.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${ROOT}/plc_assistant"

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
    find "${dest}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    (cd "${src}" && tar cf - \
      --exclude='__pycache__' \
      --exclude='*.pyc' \
      --exclude='*.pyo' \
      --exclude='.pytest_cache' \
      .) | (cd "${dest}" && tar xf -)
  fi
}

mkdir -p "${DEST}"

rm -rf "${DEST}/plcassistant"
copy_tree "${ROOT}/plcassistant" "${DEST}/plcassistant"
cp "${ROOT}/pyproject.toml" "${DEST}/pyproject.toml"

rm -rf "${DEST}/custom_components"
mkdir -p "${DEST}/custom_components/plcassistant"
copy_tree \
  "${ROOT}/custom_components/plcassistant" \
  "${DEST}/custom_components/plcassistant"

echo "Synced package + integration into ${DEST}"
