# PLCAssistant

Virtual / soft-PLC for **lab, hobby, and small-scale process equipment**, using [Home Assistant](https://www.home-assistant.io/) as the low-friction I/O, HMI, and logging surface.

**v1 installs on Home Assistant OS only** (Supervisor Apps). HA Container / Core / Supervised are not first-class targets yet. Publication is a **custom App from GitHub** — not the official Home Assistant Apps store.

```
Home Assistant OS
├── Mosquitto App          ← MQTT broker (required)
├── PLCAssistant App       ← Soft-PLC scan + block editor
└── Thin integration       ← bindings, mock entities, start/stop/reset
        (manual copy into config/custom_components/)
```

---

## Installation (Home Assistant OS)

### 1. Prerequisites

1. A running **Home Assistant OS** install (with Supervisor).
2. The **Mosquitto** App installed and running:  
   **Settings → Apps → Mosquitto broker** (official App).  
   PLCAssistant defaults to broker hostname `core-mosquitto`.
3. Home Assistant’s **MQTT** integration configured to talk to that broker  
   (**Settings → Devices & services → MQTT**).

### 2. Add the App repository

1. Go to **Settings → Apps**.
2. Open the overflow menu (⋮) → **Repositories**.
3. Add this URL and confirm:

   ```text
   https://github.com/marcuskrogh/PLCAssistant
   ```

4. Refresh the Apps list.
5. Find **PLCAssistant** and **Install**, then **Start**.

Catalog metadata lives in root [`repository.yaml`](repository.yaml). The Supervisor App folder is [`plc_assistant/`](plc_assistant/) (slug `plcassistant`).

### 3. Open the block editor

After the App is running:

| Path | How |
|------|-----|
| **Ingress (recommended)** | Apps → PLCAssistant → **Open UI** (uses your HA session) |
| **Host port** | `http://<ha-host>:8099` |

#### Auth note (exposed port)

Ingress is gated by the Home Assistant session. The optional host port binds `0.0.0.0` with **no App-side auth** — treat it as LAN-trust only, disable the port mapping in App options, or put a reverse proxy in front.

### 4. Configure the App

In **Settings → Apps → PLCAssistant → Configuration**, set:

| Option | Default | Notes |
|--------|---------|--------|
| `instance_id` | `default` | Must match the thin integration |
| `mqtt_broker` | `core-mosquitto` | Supervisor DNS name for Mosquitto |
| `mqtt_port` | `1883` | |
| `mqtt_username` | _(empty)_ | Optional |
| `mqtt_password` | _(empty)_ | Optional |

Restart the App after changing options.

### 5. Install the thin integration (one-time copy)

The Soft-PLC App does **not** auto-register into Core. Copy the bundled integration into your Home Assistant config:

```bash
# From a machine that can reach this repo and your HA /config share
cp -a custom_components/plcassistant /config/custom_components/plcassistant
```

On HA OS you can do this via the **Samba** / **Studio Code Server** / **SSH** App, or by cloning the repo and copying the folder into `/config/custom_components/`.

Then:

1. **Restart Home Assistant Core** (Developer tools → Restart, or reboot the host).
2. Go to **Settings → Devices & services → Add integration**.
3. Search for **PLCAssistant** and add it.
4. Use the **same `instance_id`** as the App (default `default`).
5. Leave **mock mode** on for a first smoke test (creates writable Number IN entities and Number OUT sinks over MQTT).

### 6. Verify the install

1. Open the App UI (Ingress or port 8099) — the block editor should load.
2. In HA, confirm mock Number entities appear under the PLCAssistant integration.
3. Change a mock IN value; the Soft-PLC should see it on the corresponding tag (and OUT entities update when the program writes).
4. Call services `plcassistant.start`, `plcassistant.stop`, or `plcassistant.reset` (Developer tools → Services) — these publish command pulses to the App.
5. Place or edit a program in the editor, restart the App, and confirm it reloads from persistent storage (`/data/program.json` inside the App).

---

## MQTT topics (quick reference)

All topics use prefix `plcassistant/{instance_id}/…` (default instance `default`).

| Direction | Topic | Who publishes |
|-----------|-------|---------------|
| Entity → Soft-PLC (IN) | `plcassistant/{id}/tag/{tag}/in` | Thin integration |
| Soft-PLC → Entity (OUT) | `plcassistant/{id}/tag/{tag}/out` | App |
| Operator commands | `plcassistant/{id}/cmd/{start\|stop\|reset}` | Thin integration |
| App status (optional) | `plcassistant/{id}/status` | App |

Payload (JSON), QoS **1**, retain **false** for scan tags:

```json
{
  "value": 0.15,
  "status": "GOOD",
  "reason": null,
  "ts": 1710000000.0
}
```

Full contract: [`docs/packaging/02-mqtt-topics.md`](docs/packaging/02-mqtt-topics.md).

---

## Program persistence

Programs are stored at `/data/program.json` inside the App (atomic write) and survive App restart. Canvas / library mutations persist to that volume.

---

## Develop / run tests locally

For contributing or running the Soft-PLC package outside HA:

```bash
git clone https://github.com/marcuskrogh/PLCAssistant.git
cd PLCAssistant
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,mqtt]"
pytest
```

Requires **Python 3.10+**. Unit tests use an in-memory MQTT bus — no live Home Assistant or Mosquitto needed.

Optional: run the local App/editor surface (without Supervisor):

```bash
python3 -m plcassistant.app --host 127.0.0.1 --port 8099
```

---

## Versioning

Tag App releases as `ha-app-vX.Y.Z` (or reuse the package version). Pin `PLCASSISTANT_PIP_REF` in [`plc_assistant/Dockerfile`](plc_assistant/Dockerfile) for reproducible builds. That Dockerfile installs Alpine `git` only for the `pip git+https` step (Supervisor build context is the App folder).

Authoritative App files live in [`plc_assistant/`](plc_assistant/); keep [`ha_app/plcassistant/`](ha_app/plcassistant/) in sync when editing.

---

## Further documentation

| Doc | Description |
|-----|-------------|
| [`docs/packaging/`](docs/packaging/) | Packaging shape, MQTT map, acceptance checklist |
| [`docs/control/`](docs/control/01-scan-scheduler.md) | Scan scheduler, FB/PID, safety, HA↔cyclic boundary |
| [`docs/io/`](docs/io/01-image-quality.md) | Soft-PLC I/O image, bindings, thin-integration stub |
| [`docs/surface/`](docs/surface/01-block-model.md) | Block program model, runtime, editor, apply policy |
| [`docs/wedge/`](docs/wedge/README.md) | Skid / process wedge specifications |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Product direction |
