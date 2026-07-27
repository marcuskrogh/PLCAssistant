# Install PLCAssistant on Home Assistant OS (SWD-127)

Custom **App from GitHub** — not the official Home Assistant Apps store.

## Prerequisites

1. Home Assistant **OS** (Supervisor).
2. Install the **Mosquitto** App (Settings → Apps) and note that PLCAssistant defaults to broker hostname `core-mosquitto`.
3. This repository available as a GitHub URL you can paste into HA.

## Add the App repository

1. Settings → Apps → ⋮ → **Repositories**
2. Add:

   ```text
   https://github.com/marcuskrogh/PLCAssistant
   ```

   The App catalog entry is defined by [`repository.yaml`](repository.yaml) and the App folder [`plcassistant/`](plcassistant/).

   > **Monorepo note:** HA expects `repository.yaml` at the **repository root**. Until this tree is published as a dedicated Apps repo (or `repository.yaml` is copied to the git root), point a fork/branch that places `ha_app/repository.yaml` + `ha_app/plcassistant/` at the root, **or** use a release that documents the mirrored layout. The authoritative App files live under `ha_app/` in this monorepo.

3. Refresh the Apps list and install **PLCAssistant**.
4. Start the App. Open it via **Ingress** (Open UI) or the documented host port **8099**.

## Bundle the thin integration (v1)

The thin integration ships in this repo at `custom_components/plcassistant/`.

**v1 mechanism (locked for SWD-126):** **documented one-time copy** into Home Assistant config — the App entrypoint does **not** auto-register into Core.

```bash
# On the HA host / Samba / Studio Code Server — adjust paths to your config:
cp -a custom_components/plcassistant /config/custom_components/plcassistant
```

Then restart Home Assistant Core and add the **PLCAssistant** integration (MQTT instance id must match the App option `instance_id`, default `default`).

## Configure MQTT

| Side | Setting | Default |
|------|---------|---------|
| App options | `mqtt_broker` | `core-mosquitto` |
| App options | `mqtt_port` | `1883` |
| App options | `instance_id` | `default` |
| Integration | same `instance_id` + broker | must match |

Topic map: [`docs/packaging/02-mqtt-topics.md`](../docs/packaging/02-mqtt-topics.md).

## Program persistence

Programs are stored at `/data/program.json` inside the App and survive App restart.

## Versioning

Tag releases as `ha-app-vX.Y.Z` (or reuse package version). Pin `PLCASSISTANT_PIP_REF` in the App Dockerfile for reproducible builds.
