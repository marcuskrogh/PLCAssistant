# PLCAssistant Home Assistant App

Supervisor App that runs the Soft-PLC scan runtime and block editor.

## Features

- **Ingress** on port 8099 (Apps panel)
- **Optional exposed port** `8099/tcp` for direct host access
- **Persistent `/data`** for program-of-record (`program.json`)
- Options: `instance_id`, MQTT broker (`core-mosquitto` default)

## Requirements

- Home Assistant **OS**
- **Mosquitto** App (or equivalent MQTT broker) installed and running
- Bundled thin integration copied into `config/custom_components/plcassistant/` (see root [`README.md`](../../README.md))

## Build note

The Dockerfile installs `plcassistant` from GitHub via pip (`git+https`), so the
image build installs Alpine `git` for that step and removes it afterward. Pin
`PLCASSISTANT_PIP_REF` to a tag/commit for production builds.
