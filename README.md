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
   https://github.com/marcuskrogh/PLCAssistant#main
   ```

   The `#main` pin selects the branch Supervisor shallow-clones; later
   **Check for updates** fetches that same branch.

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

Wait until the App shows **Started** (reinstall / first Start can take a while — local image build). Then open **Settings → Apps → PLCAssistant → Configuration** and set:

| Option | Default | Notes |
|--------|---------|--------|
| `instance_id` | `default` | Must match the thin integration |
| `mqtt_broker` | `core-mosquitto` | Supervisor DNS name for Mosquitto |
| `mqtt_port` | `1883` | |
| `mqtt_username` | _(empty)_ | Optional |
| `mqtt_password` | _(empty)_ | Optional |

Saving options restarts the App. Do not Save while Install/Start is still in progress (Supervisor will log job-group conflicts).

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

## Troubleshooting

### `Another job is running for job group app_…_plcassistant` / `App … is not running`

Supervisor allows only one start/stop/restart job at a time for the App. This usually appears right after **Install / Reinstall / Update** if Configuration is saved (or Start/Stop clicked) before the previous job finishes — or if the App crash-looped on boot.

1. Open **Settings → Apps → PLCAssistant** and wait until the status is **Started** (check the App log for `thin integration` / `HA runtime` lines).
2. Retry Configuration only after it is Started.
3. If it stays stuck for several minutes: **host reboot** (Settings → System → Hardware → Advanced → Reboot host), not only Core restart. Optional CLI: `ha jobs info`, `ha supervisor repair`.
4. After reboot, Start PLCAssistant once, wait for Started, then configure.

From **0.1.6**, thin-integration copy failures no longer abort Soft-PLC start (they are logged and the editor still comes up). From **0.1.7**, App builds bust Docker layer cache on each `version` bump, and App start migrates any remaining `hass.components` MQTT subscribe on disk (stale-image escape hatch). **Restart Home Assistant Core** after App Update/reinstall so Core reloads `custom_components/plcassistant`.

### Update button shows but installed version stays old

Local-build Apps can keep **stale Docker/containerd layers** on some HA OS versions.

1. **Settings → Apps → ⋮ → Check for updates**, then hard-refresh the browser.
2. Open PLCAssistant → **Update** (or uninstall + install).
3. Confirm App log shows the new version / `thin integration installed/updated` / migration line.
4. **Restart Home Assistant Core**.
5. If the installed version still does not move: host SSH/`ha` console → `docker builder prune` (or reboot host) → uninstall PLCAssistant → install again.

### Latest stuck at an old version (store / Updates dialog)

If GitHub already has a newer `version` in [`plc_assistant/config.yaml`](plc_assistant/config.yaml) but HA still shows **Latest = installed** (for example both `0.1.6`), either the Supervisor store clone is stale **or** the Core update entity has not refreshed yet (~15 minutes after store reload).

1. Confirm GitHub `main`: open [`plc_assistant/config.yaml`](https://github.com/marcuskrogh/PLCAssistant/blob/main/plc_assistant/config.yaml) and note `version`.
2. **Settings → Apps → ⋮ → Repositories** — if the URL is missing `#main`, remove it and re-add:

   ```text
   https://github.com/marcuskrogh/PLCAssistant#main
   ```

   Then hard-refresh and confirm **Latest** matches GitHub.
3. Otherwise: **Check for updates** → hard-refresh (**Ctrl/Cmd+Shift+R**) → **Restart Home Assistant Core**.
4. If **Latest** is still behind GitHub: remove the repository and re-add `#main` (step 2), then Check for updates again.
5. Check **Settings → System → Logs → Supervisor** for `Can't update … PLCAssistant` / corrupt repository errors.

## Updates

Home Assistant does **not** poll custom GitHub App repos continuously. After we bump
`version` in [`plc_assistant/config.yaml`](plc_assistant/config.yaml) on `main`:

1. **Settings → Apps → ⋮ → Check for updates** (this shallow-fetches the repository branch).
2. Hard-refresh the browser (**Ctrl/Cmd+Shift+R**) — the store UI is often cached.
3. Open PLCAssistant — an **Update** button appears when the store version is newer than the installed one.
4. If the Apps page and the Updates dialog disagree, restart Core (see “Latest stuck…”).

This works for **every** future release as long as the repo keeps a single App
`config.yaml` (enforced by CI). Full release checklist:
[`docs/packaging/04-updates.md`](docs/packaging/04-updates.md).

If an update still does not appear, check **Settings → System → Logs → Supervisor**.
Removing and re-adding the repository (`#main`) forces a fresh clone.

## Versioning

Bump `version` in [`plc_assistant/config.yaml`](plc_assistant/config.yaml) whenever the App image or runtime changes — that string is what Supervisor compares for updates. Tag releases as `ha-app-vX.Y.Z` optionally. After changing the Python package or thin integration, run `./scripts/sync-ha-app-package.sh` so [`plc_assistant/`](plc_assistant/) stays installable from the Supervisor build context.

There must be **exactly one** App `config.yaml` / `config.yml` / `config.json` in this repository (under `plc_assistant/`). Supervisor searches recursively; a second file with the same `slug` breaks update detection for all later releases.

---

## Further documentation

| Doc | Description |
|-----|-------------|
| [`docs/packaging/`](docs/packaging/) | Packaging shape, MQTT map, acceptance checklist, App updates |
| [`docs/control/`](docs/control/01-scan-scheduler.md) | Scan scheduler, FB/PID, safety, HA↔cyclic boundary |
| [`docs/io/`](docs/io/01-image-quality.md) | Soft-PLC I/O image, bindings, thin-integration stub |
| [`docs/surface/`](docs/surface/01-block-model.md) | Block program model, runtime, editor, apply policy |
| [`docs/wedge/`](docs/wedge/README.md) | Skid / process wedge specifications |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Product direction |
