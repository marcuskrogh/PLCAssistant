#!/usr/bin/env bash
# Serve the repo root so the sandbox can import www/pid-faceplate-elements.js.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PORT="${1:-8765}"
cd "$ROOT"
echo "PID faceplate sandbox: http://127.0.0.1:${PORT}/tools/pid-faceplate/"
exec python3 -m http.server "$PORT" --bind 127.0.0.1
