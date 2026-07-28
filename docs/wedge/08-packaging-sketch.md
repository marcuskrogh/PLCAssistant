# Packaging sketch → freeze (SWD-84)

> **Status:** Frozen for SWD-84. Authoritative contract: [`docs/packaging/`](../packaging/README.md). This page is a short pointer plus residual open items.

## Locked (see packaging docs)

| Topic | Decision |
|-------|----------|
| Shape | Hybrid App + thin integration |
| Platform | HA OS only |
| Bridge | MQTT (Mosquitto required) |
| Program-of-record | App `/data` |
| Deliverable | Custom App from GitHub |
| Integration | Bundled with App |
| Editor access | Ingress + exposed port |

## Residual open items (post-implement)

1. Exact auth between Ingress and exposed port (token / network-only).
2. App repository versioning / release tagging convention (see `ha_app/INSTALL.md`).

**Locked in implement (updated):** v1+ bundle = App auto-syncs into `custom_components` on start (`homeassistant_config` map); Core restart still required once.

Do not re-litigate closed decisions in [`docs/PLAN.md`](../PLAN.md) without a new define pass.
