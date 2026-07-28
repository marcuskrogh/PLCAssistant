# PLCAssistant Home Assistant App

Supervisor App that runs the Soft-PLC scan runtime and block editor.

## Features

- **Ingress** on port 8099 (Apps panel)
- **Optional exposed port** `8099/tcp` for direct host access
- **Persistent `/data`** for program-of-record (`program.json`)
- **Auto-installs** the thin integration into HA `custom_components/` on start
- Options: `instance_id`, MQTT broker (`core-mosquitto` default)

## Requirements

- Home Assistant **OS**
- **Mosquitto** App (or equivalent MQTT broker) installed and running

## Build note

The Dockerfile installs `plcassistant` from the App build context and bakes
in `custom_components/`. After changing the Python package or integration at
the repo root, run:

```bash
./scripts/sync-ha-app-package.sh
```

before committing App releases.
