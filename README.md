# PLCAssistant

Virtual / soft-PLC for **lab, hobby, and small-scale process equipment**, using [Home Assistant](https://www.home-assistant.io/) as the low-friction I/O, HMI, and logging surface.

## Docs

| Doc | Description |
|-----|-------------|
| [`docs/PLAN.md`](docs/PLAN.md) | Implementation plan for packaging shape (SWD-84) |
| [`docs/RESEARCH.md`](docs/RESEARCH.md) | Literature brief backing SWD-84 define |
| [`docs/control/`](docs/control/01-scan-scheduler.md) | Scan scheduler, FB/PID, safety precedence, HA↔cyclic boundary |
| [`docs/io/`](docs/io/01-image-quality.md) | Soft-PLC I/O image, bindings, thin-integration stub, acceptance checklist |
| [`docs/wedge/`](docs/wedge/README.md) | Skid specifications: process, I/O, control, safety, mock, packaging |
| [`docs/surface/`](docs/surface/01-block-model.md) | Block program surface: model, runtime, builtin library, apply policy, App editor, wedge migration, acceptance |
| [`docs/packaging/`](docs/packaging/) | HA packaging contract: hybrid App + thin integration, MQTT topics, acceptance |
| [`ha_app/`](ha_app/INSTALL.md) | Home Assistant OS App scaffold + install docs |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Product direction and theme roadmap |
