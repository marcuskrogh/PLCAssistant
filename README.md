# PLCAssistant

Virtual / soft-PLC for **lab, hobby, and small-scale process equipment**, using [Home Assistant](https://www.home-assistant.io/) as the low-friction I/O, HMI, and logging surface.

**v1 installs on Home Assistant OS only** (Supervisor Apps). HA Container / Core / Supervised are not first-class targets yet. Publication is a **custom App from GitHub** — not the official Home Assistant Apps store.

```
Home Assistant OS
├── Mosquitto App          ← MQTT broker (required)
├── PLCAssistant App       ← Soft-PLC scan + block editor
└── Thin integration       ← auto-installed into config/custom_components/ on App start
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

### 5. Enable the thin integration

On **Start** (and on App updates), the App copies `custom_components/plcassistant` into your Home Assistant config (`/homeassistant` → host `/config`). Check the App log for `thin integration installed/updated`.

Then:

1. **Restart Home Assistant Core** once (Developer tools → Restart) so Core loads the new files.
2. Go to **Settings → Devices & services → Add integration**.
3. Search for **PLCAssistant** and add it.
4. Use the **same `instance_id`** as the App (default `default`).
5. Leave **mock mode** on for a first smoke test (creates writable Number IN entities and Number OUT sinks over MQTT).

Manual copy is no longer required on HA OS. Fallback if the config mount is unavailable: copy [`custom_components/plcassistant`](custom_components/plcassistant) into `/config/custom_components/` yourself (Samba / SSH / Studio Code Server).

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

## Updates

Home Assistant does **not** poll custom GitHub App repos continuously. After we bump
`version` in [`plc_assistant/config.yaml`](plc_assistant/config.yaml) on `main`:

1. **Settings → Apps → ⋮ → Check for updates** (this `git pull`s the repository).
2. Hard-refresh the browser (**Ctrl/Cmd+Shift+R**) — the store UI is often cached.
3. Open PLCAssistant — an **Update** button appears when the store version is newer than the installed one.

If an update still does not appear, check **Settings → System → Logs → Supervisor** for store/validation errors. Removing and re-adding the repository also forces a fresh clone, but should not be necessary once only one App `config.yaml` exists in the repo.

## Versioning

Bump `version` in [`plc_assistant/config.yaml`](plc_assistant/config.yaml) whenever the App image or runtime changes — that string is what Supervisor compares for updates. Tag releases as `ha-app-vX.Y.Z` optionally. After changing the Python package or thin integration, run `./scripts/sync-ha-app-package.sh` so [`plc_assistant/`](plc_assistant/) stays installable from the Supervisor build context.

There must be **exactly one** App `config.yaml` in this repository (under `plc_assistant/`). Supervisor searches recursively; a second file with the same `slug` breaks update detection.

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
