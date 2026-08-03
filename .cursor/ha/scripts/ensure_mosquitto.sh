#!/usr/bin/env bash
# Ensure Mosquitto is listening on :1883 for local Soft-PLC ↔ HA MQTT.
set -euo pipefail

port_open() {
  python3 - <<'PY'
import socket
s = socket.socket()
s.settimeout(1.0)
try:
    s.connect(("127.0.0.1", 1883))
except OSError:
    raise SystemExit(1)
finally:
    s.close()
raise SystemExit(0)
PY
}

if ! command -v mosquitto >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq mosquitto mosquitto-clients
fi

sudo mkdir -p /etc/mosquitto/conf.d /run/mosquitto /var/log/mosquitto
sudo tee /etc/mosquitto/conf.d/plcassistant-dev.conf >/dev/null <<'EOF'
listener 1883 0.0.0.0
allow_anonymous true
EOF

if ! port_open; then
  sudo pkill mosquitto 2>/dev/null || true
  sleep 0.5
  sudo mosquitto -c /etc/mosquitto/mosquitto.conf -d
  for _ in $(seq 1 20); do
    if port_open; then
      break
    fi
    sleep 0.25
  done
fi

mosquitto_pub -h 127.0.0.1 -t 'plcassistant/dev/ping' -m ok >/dev/null
echo "Mosquitto OK on 127.0.0.1:1883"
