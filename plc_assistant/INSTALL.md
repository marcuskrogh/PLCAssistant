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

   Catalog metadata: root [`repository.yaml`](../repository.yaml). App folder: [`plc_assistant/`](../plc_assistant/) (Supervisor slug `plcassistant` in `config.yaml`). The Python package remains `plcassistant/` — the App folder uses a distinct directory name so HA can discover it as a direct child of the repository root.

3. Refresh the Apps list and install **PLCAssistant**.
4. Start the App. Open it via **Ingress** (Open UI) or the documented host port **8099**.

### Auth note (exposed port)

Ingress is gated by the Home Assistant session. The optional host port binds `0.0.0.0` with **no App-side auth** — treat it as LAN-trust only, disable the port mapping, or put a reverse proxy in front.

## Bundle the thin integration (v1)

The thin integration ships at `custom_components/plcassistant/`.

**v1 mechanism:** **documented one-time copy** into Home Assistant config — the App entrypoint does **not** auto-register into Core.

```bash
cp -a custom_components/plcassistant /config/custom_components/plcassistant
```

Restart Home Assistant Core and add the **PLCAssistant** integration. `instance_id` must match the App option (default `default`). Mosquitto / HA MQTT integration must be configured. Mock mode creates **Number** entities that publish tag IN (writable) and sink tag OUT over MQTT.

## Configure MQTT

| Side | Setting | Default |
|------|---------|---------|
| App options | `mqtt_broker` | `core-mosquitto` |
| App options | `mqtt_port` | `1883` |
| App options | `instance_id` | `default` |
| Integration | same `instance_id` | must match |

Topic map: [`docs/packaging/02-mqtt-topics.md`](../docs/packaging/02-mqtt-topics.md).

The App runtime starts `MqttIoBridge` + a scan loop when options/MQTT are available. The thin integration publishes `…/tag/{tag}/in` from mock sensors and subscribes `…/tag/{tag}/out` into mock numbers; operator services publish `…/cmd/{start|stop|reset}` (App consumes cmd pulses).

## Program persistence

Programs are stored at `/data/program.json` inside the App (atomic write) and survive App restart. Canvas place/library mutations persist to disk.

## Versioning

Tag releases as `ha-app-vX.Y.Z` (or reuse package version). Pin `PLCASSISTANT_PIP_REF` in the App Dockerfile for reproducible builds.

## Layout note

Authoritative App files are mirrored under `ha_app/plcassistant/` for docs continuity; keep them in sync with root `plc_assistant/` when editing.
