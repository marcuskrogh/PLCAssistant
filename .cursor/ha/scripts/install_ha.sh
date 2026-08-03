#!/usr/bin/env bash
# Install Home Assistant Core (Python 3.12-compatible pin) for local integration tests.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
VENV="$ROOT/.venv-ha"
HA_VERSION="${HA_VERSION:-2025.1.4}"

mkdir -p "$ROOT/config/custom_components" "$ROOT/config/dashboards" "$ROOT/config/plcassistant" "$ROOT/data"

# Live-link the repo thin integration into HA config.
ln -sfn "$REPO/custom_components/plcassistant" \
  "$ROOT/config/custom_components/plcassistant"

if [[ ! -x "$VENV/bin/hass" ]]; then
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install -U pip wheel setuptools
python -m pip install "homeassistant==${HA_VERSION}" paho-mqtt

# Seed minimal YAML stubs if missing.
[[ -f "$ROOT/config/automations.yaml" ]] || printf '[]\n' >"$ROOT/config/automations.yaml"
[[ -f "$ROOT/config/scripts.yaml" ]] || : >"$ROOT/config/scripts.yaml"
[[ -f "$ROOT/config/scenes.yaml" ]] || : >"$ROOT/config/scenes.yaml"
[[ -f "$ROOT/config/secrets.yaml" ]] || : >"$ROOT/config/secrets.yaml"

python -c "from homeassistant.const import __version__; print('Home Assistant', __version__)"
