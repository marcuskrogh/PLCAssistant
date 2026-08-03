#!/usr/bin/env bash
# Start Home Assistant and auto-bootstrap MQTT + PLCAssistant once ready.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bash "$ROOT/scripts/ensure_mosquitto.sh"

(
  for _ in $(seq 1 90); do
    if curl -sf http://127.0.0.1:8123/api/onboarding >/dev/null 2>&1; then
      python3 "$ROOT/scripts/bootstrap_ha.py" && exit 0
    fi
    sleep 2
  done
  echo "bootstrap: HA onboarding API never became ready" >&2
  exit 1
) &

exec bash "$ROOT/scripts/run_ha.sh"
