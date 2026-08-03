#!/usr/bin/env bash
# Idempotent cloud-agent / local install for PLCAssistant.
# Syncs agent skills, Soft-PLC package, Mosquitto, and Home Assistant Core.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Syncing agent skills"
bash .agents/sync-skills.sh

echo "==> Ensuring python3-venv is available"
if ! python3 -c "import ensurepip" 2>/dev/null; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
      "python3-venv" "python3-pip" || \
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
        "python3.12-venv" "python3-pip"
  else
    echo "error: ensurepip missing and apt-get unavailable" >&2
    exit 1
  fi
fi

echo "==> Python venv (.venv) for Soft-PLC"
# Recreate a broken partial venv (e.g. ensurepip was missing on first try).
if [[ -d .venv ]] && [[ ! -x .venv/bin/python || ! -x .venv/bin/pip ]]; then
  rm -rf .venv
fi
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install -U pip setuptools wheel
python -m pip install -e ".[dev,mqtt]"

echo "==> Smoke: import Soft-PLC package"
python -c "import plcassistant; print('plcassistant OK', getattr(plcassistant, '__file__', ''))"

echo "==> Mosquitto (local MQTT broker)"
bash .cursor/ha/scripts/ensure_mosquitto.sh

echo "==> Home Assistant Core (integration test target)"
bash .cursor/ha/scripts/install_ha.sh

echo "==> Install complete"
python -c "import sys; print(sys.executable); print(sys.version)"
