#!/usr/bin/env bash
# Start Home Assistant Core against .cursor/ha/config (foreground).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/.venv-ha/bin/activate"
exec hass -c "$ROOT/config"
