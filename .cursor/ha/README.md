# Local Home Assistant + Mosquitto for PLCAssistant integration testing

This is a **Core** (not HA OS / Supervisor) stack for cloud agents and local
dev. Production remains HA OS + Mosquitto App + PLCAssistant App (see root
README).

## Stack

| Piece | How |
|-------|-----|
| Mosquitto | apt `mosquitto` on `127.0.0.1:1883` (anonymous) |
| Home Assistant Core | `.venv-ha` with `homeassistant==2025.1.4` (Python 3.12) on `:8123` |
| Thin integration | symlink `custom_components/plcassistant` → repo |
| Soft-PLC | `python -m plcassistant.app` HA runtime → MQTT + config bridge |

## Commands

```bash
bash .cursor/install.sh                          # Soft-PLC + HA venv + Mosquitto
bash .cursor/ha/scripts/ensure_mosquitto.sh
bash .cursor/ha/scripts/run_ha_with_bootstrap.sh # HA + MQTT + PLCAssistant config flow
bash .cursor/ha/scripts/run_soft_plc.sh          # Soft-PLC editor + MQTT scan
```

Default HA owner after bootstrap: `dev` / `devpass123` (local only).

## Ports

- `8123` — Home Assistant
- `8099` — Soft-PLC program editor
- `1883` — MQTT
