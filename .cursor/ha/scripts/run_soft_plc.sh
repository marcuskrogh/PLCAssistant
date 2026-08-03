#!/usr/bin/env bash
# Start Soft-PLC with MQTT HA runtime against local Mosquitto + HA config bridge.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck disable=SC1091
source "$REPO/.venv/bin/activate"
export PLCASSISTANT_HA_CONFIG="$HA_ROOT/config"
export PLCASSISTANT_HA_RUNTIME=1
exec python -m plcassistant.app \
  --host 0.0.0.0 \
  --port 8099 \
  --options-path "$HA_ROOT/data/options.json" \
  --program-path "$HA_ROOT/data/program.json"
