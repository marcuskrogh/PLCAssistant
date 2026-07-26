#!/usr/bin/env bash
# Sync packages/plcassistant_contract pure modules into the HACS vendor tree.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/packages/plcassistant_contract/plcassistant_contract"
DST="$ROOT/custom_components/plcassistant/vendor/plcassistant_contract"
mkdir -p "$DST"
for f in models.py coerce.py failsafe.py validate.py; do
  cp "$SRC/$f" "$DST/$f"
done
echo "Synced pure contract modules → $DST"
echo "Note: vendor/__init__.py is HACS-specific (no HTTP client); edit it separately."
