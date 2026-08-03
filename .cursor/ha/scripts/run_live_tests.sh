#!/usr/bin/env bash
# Ensure Mosquitto + HA Core + Soft-PLC are up, then run live pytest markers.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HA_ROOT="$REPO/.cursor/ha"
cd "$REPO"

# shellcheck disable=SC1091
source "$REPO/.venv/bin/activate"

bash "$HA_ROOT/scripts/ensure_mosquitto.sh"

mkdir -p "$HA_ROOT/data/logs" "$HA_ROOT/data/pids"

start_bg() {
  local name="$1"
  local pidfile="$HA_ROOT/data/pids/${name}.pid"
  local logfile="$HA_ROOT/data/logs/${name}.log"
  local cmd="$2"

  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "$name already running (pid $(cat "$pidfile"))"
    return 0
  fi
  # Port-based reuse if started outside this script.
  if [[ "$name" == "homeassistant" ]] \
    && curl -sf http://127.0.0.1:8123/api/onboarding >/dev/null 2>&1; then
    echo "homeassistant already listening on :8123"
    return 0
  fi
  if [[ "$name" == "soft-plc" ]] \
    && curl -sf http://127.0.0.1:8099/api/runtime >/dev/null 2>&1; then
    echo "soft-plc already listening on :8099"
    return 0
  fi

  echo "starting $name …"
  # shellcheck disable=SC2086
  nohup bash -c "$cmd" >"$logfile" 2>&1 &
  echo $! >"$pidfile"
  echo "  pid $(cat "$pidfile") log $logfile"
}

start_bg "homeassistant" "bash '$HA_ROOT/scripts/run_ha_with_bootstrap.sh'"
start_bg "soft-plc" "bash '$HA_ROOT/scripts/run_soft_plc.sh'"

echo "waiting for HA API …"
ha_ready=0
for _ in $(seq 1 120); do
  if curl -sf http://127.0.0.1:8123/api/ >/dev/null 2>&1 \
    || curl -sf http://127.0.0.1:8123/api/onboarding >/dev/null 2>&1; then
    ha_ready=1
    break
  fi
  sleep 2
done
if [[ "$ha_ready" -ne 1 ]]; then
  echo "error: Home Assistant never became ready on :8123" >&2
  echo "--- homeassistant.log (tail) ---" >&2
  tail -n 40 "$HA_ROOT/data/logs/homeassistant.log" 2>/dev/null || true
  exit 1
fi

echo "waiting for Soft-PLC /api/runtime …"
soft_ready=0
for _ in $(seq 1 90); do
  if curl -sf http://127.0.0.1:8099/api/runtime >/dev/null 2>&1; then
    soft_ready=1
    break
  fi
  sleep 2
done
if [[ "$soft_ready" -ne 1 ]]; then
  echo "error: Soft-PLC never became ready on :8099" >&2
  echo "--- soft-plc.log (tail) ---" >&2
  tail -n 40 "$HA_ROOT/data/logs/soft-plc.log" 2>/dev/null || true
  exit 1
fi

# Bootstrap (idempotent) so ha_token.json exists even if HA was already onboarded.
python3 "$HA_ROOT/scripts/bootstrap_ha.py"

echo "running live tests …"
exec pytest -m live "$@" tests/live
