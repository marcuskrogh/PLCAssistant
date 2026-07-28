#!/usr/bin/env bash
# Copy the installable Python package + thin integration into the HA App build context.
# Supervisor docker-builds only the App folder (plc_assistant/), so those trees must live there.
#
# INVARIANT: this repository must contain exactly one Supervisor App config
# (plc_assistant/config.yaml). Supervisor recursively discovers config.yaml|yml|json;
# a second App with slug plcassistant breaks update detection for every future release.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${ROOT}/plc_assistant"
CANONICAL_CONFIG="${DEST}/config.yaml"

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

assert_single_app_config() {
  local -a configs=()
  while IFS= read -r -d '' path; do
    case "${path}" in
      */.git/*|*/.venv/*|*/venv/*|*/node_modules/*|*/__pycache__/*) continue ;;
    esac
    configs+=("${path}")
  done < <(find "${ROOT}" \( -name 'config.yaml' -o -name 'config.yml' -o -name 'config.json' \) -type f -print0)

  if [ "${#configs[@]}" -ne 1 ] || [ "${configs[0]}" != "${CANONICAL_CONFIG}" ]; then
    echo "ERROR: expected exactly one App config at ${CANONICAL_CONFIG}" >&2
    printf '  found: %s\n' "${configs[@]:-}" >&2
    echo "Remove extras — duplicate slug breaks Supervisor update detection." >&2
    exit 1
  fi
}

if [ ! -f "${CANONICAL_CONFIG}" ]; then
  echo "ERROR: missing ${CANONICAL_CONFIG}" >&2
  exit 1
fi

mkdir -p "${DEST}"

rm -rf "${DEST}/plcassistant"
copy_tree "${ROOT}/plcassistant" "${DEST}/plcassistant"
cp "${ROOT}/pyproject.toml" "${DEST}/pyproject.toml"

rm -rf "${DEST}/custom_components"
mkdir -p "${DEST}/custom_components/plcassistant"
copy_tree \
  "${ROOT}/custom_components/plcassistant" \
  "${DEST}/custom_components/plcassistant"

# Never recreate a second App under ha_app/ (historical footgun).
rm -rf "${ROOT}/ha_app/plcassistant"

assert_single_app_config
# App and thin-integration versions must stay identical (SWD-131).
python3 - "${CANONICAL_CONFIG}" "${ROOT}/custom_components/plcassistant/manifest.json" \
  "${DEST}/custom_components/plcassistant/manifest.json" <<'PY'
import json, sys, pathlib
try:
    import yaml
except ImportError:
    # Minimal fallback: parse "version: \"x\"" from config.yaml
    text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    app_ver = None
    for line in text.splitlines():
        if line.strip().startswith("version:"):
            app_ver = line.split(":", 1)[1].strip().strip('"').strip("'")
            break
else:
    app_ver = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))["version"]
for path in sys.argv[2:]:
    man = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if man.get("version") != app_ver:
        raise SystemExit(
            f"version mismatch: App {app_ver!r} vs {path} {man.get('version')!r}"
        )
print(f"OK: App + integration version {app_ver}")
PY
echo "Synced package + integration into ${DEST}"
echo "OK: single App config ${CANONICAL_CONFIG}"
