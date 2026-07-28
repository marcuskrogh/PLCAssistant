# Install PLCAssistant on Home Assistant OS

The full installation guide lives in the repository root:

**→ [`../README.md`](../README.md)**

That guide covers prerequisites (HA OS + Mosquitto), adding the GitHub App repository, Ingress / port **8099**, auto-install of the thin integration (`custom_components/plcassistant` on App start), checking for App updates, MQTT configuration, and local development.

The Supervisor App itself lives only in [`../plc_assistant/`](../plc_assistant/) (do not add another `config.yaml` under `ha_app/`).
