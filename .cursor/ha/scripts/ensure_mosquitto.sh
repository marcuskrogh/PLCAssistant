#!/usr/bin/env bash
# Ensure Mosquitto is listening on :1883 for local Soft-PLC ↔ HA MQTT.
set -euo pipefail

if ! command -v mosquitto >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq mosquitto mosquitto-clients
fi

sudo mkdir -p /etc/mosquitto/conf.d /run/mosquitto /var/log/mosquitto
sudo tee /etc/mosquitto/conf.d/plcassistant-dev.conf >/dev/null <<'EOF'
listener 1883 0.0.0.0
allow_anonymous true
EOF

if ! ss -ltn 2>/dev/null | grep -q ':1883 '; then
  sudo pkill mosquitto 2>/dev/null || true
  sudo mosquitto -c /etc/mosquitto/mosquitto.conf -d
  sleep 1
fi

mosquitto_pub -h 127.0.0.1 -t 'plcassistant/dev/ping' -m ok >/dev/null
echo "Mosquitto OK on 127.0.0.1:1883"
