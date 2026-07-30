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

### 3. Open the Soft-PLC program editor

After the App is running:

| Path | How |
|------|-----|
| **Ingress (recommended)** | Apps → PLCAssistant → **Open UI** (uses your HA session) |
| **Host port** | `http://<ha-host>:8099` |

The App is the **block / program editor**. Operator HMI (Start/Stop/Reset, setpoints, live PVs) is in **Home Assistant Lovelace** — not inside the Soft-PLC App.

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
5. Leave **mock mode** on for a first smoke test (creates a writable **Level setpoint** Number, read-only **sensors** for tank/flow/speed/active SPs/status/MODE, and Start/Stop/Reset **buttons** over MQTT).

The App and thin integration **share one version** (`plc_assistant/config.yaml` ≡ `custom_components/plcassistant/manifest.json`). After an App Update, restart Core so HA reloads the matching integration.

On Start the App also copies a Lovelace template to `/config/dashboards/plcassistant.yaml`. The thin integration **registers it in the HA sidebar** automatically (no paste) — look for **PLCAssistant** after Core restart.

Manual copy is no longer required on HA OS. Fallback if the config mount is unavailable: copy [`custom_components/plcassistant`](custom_components/plcassistant) into `/config/custom_components/` yourself (Samba / SSH / Studio Code Server).

### 6. Verify the install

1. Open the App UI (Ingress or port 8099) — the **program editor** should load with a populated **Block Library** (if Ingress shows `Error: 404`, Update the App and hard-refresh).
2. In HA, confirm **Level setpoint** (`number.plcassistant_sp_level_req`), process **sensors** (including **Status** / **Mode**), and Start/Stop/Reset buttons under the PLCAssistant integration.
3. Open **PLCAssistant** in the HA **sidebar** — status is at the top. After Core restart with the App **Started**, Soft-PLC should show `stopped` (not stuck `offline`) with Start ready On when healthy. Set the level setpoint, press **Start** — Soft-PLC status becomes `running`, MODE `RUNNING`, and tank/flow/speed/active SPs move. Start ready correctly shows Off while RUNNING.
4. Press **Stop** / **Reset** (or call services `plcassistant.start` / `stop` / `reset`) — these publish command pulses to the App.
5. Place or edit a program in the App editor, restart the App, and confirm it reloads from persistent storage (`/data/program.json` inside the App).

---

## Toy example setup (skid plant)

This walkthrough gets the bundled tank/reservoir skid mock running end-to-end, then shows how to open the **Dynamics** block editor.

### A. Install (once)

1. Install **Mosquitto**, configure HA **MQTT**, add the PLCAssistant App repo (`#main`), **Install** / **Start** the App (see [Installation](#installation-home-assistant-os) above).
2. Wait for App **Started** and a Core restart after thin-integration sync (App **0.1.26+** auto-requests Core restart after sync; **0.1.27+** also shows **Restart required** on Settings → System → Updates for later syncs once that version is loaded).
3. **Settings → Devices & services → Add integration → PLCAssistant** with matching `instance_id` and **mock mode** enabled.

### B. Operate the skid HMI

1. Open the HA sidebar item **PLCAssistant** (url path `plcassistant-skid`).
2. Stay on the **Operate** tab. Soft-PLC should show **stopped** (not offline) with Start ready **On**.
3. Confirm **Dynamics preset** reads `skid` (code default) or the last applied model.
4. Set **Level setpoint**, press **Start**. Tank / reservoir / inlet flow Numbers should move; Soft-PLC Mode becomes **RUNNING**.

### C. Edit plant dynamics (state & measurement equations)

1. In the same sidebar board, open the **Dynamics** tab.
2. The block editor loads the `skid_composed` toy document (seeded under `/config/plcassistant/models/`).
3. Add blocks from the left palette (`tank`, `pump`, `orifice`, `lag`, `custom_ode`). Predefined blocks show their underlying dynamical equations in the inspector.
4. Select a **Custom ODE** block to enter **state equations one row at a time** (`state` + `d(state)/dt` expression). Optionally add **algebraic** rows for non-integrated signals.
5. Under **Measurement equations**, map Soft-PLC IN tags one row at a time (`TAG = expression` over state / inputs / params) — distinct from the ODEs.
6. Edit **Model I/O** (inputs, global params, initial state) as needed.
7. **Validate** → **Save** → **Apply & reload**. The plant simulator rebuilds from model initials and the Dynamics preset sensor updates.
8. Return to **Operate**, press **Start** again, and confirm motion still matches the composed model.

Soft-PLC’s App Ingress editor is for **control programs** only — plant math stays in the integration Dynamics editor. Soft-PLC remains mock-unaware (`HeldProcess` + MQTT plant IN). The Dynamics tab iframe loads the editor shell; API calls use the Home Assistant session via the parent frontend (`hass.callApi`).

### D. Optional: Options flow / service

You can still pick a saved preset without the editor:

- **Settings → Devices → PLCAssistant → Configure** (`dynamics_preset` / JSON param overrides), or
- Service `plcassistant.set_dynamics_preset` with `preset: skid_composed`.

---

## MQTT topics (quick reference)

All topics use prefix `plcassistant/{instance_id}/…` (default instance `default`).

| Direction | Topic | Who publishes |
|-----------|-------|---------------|
| Entity → Soft-PLC (IN) | `plcassistant/{id}/tag/{tag}/in` | Thin integration |
| Soft-PLC → Entity (OUT) | `plcassistant/{id}/tag/{tag}/out` | App |
| Operator commands | `plcassistant/{id}/cmd/{start\|stop\|reset}` | Thin integration |
| App status (optional) | `plcassistant/{id}/status` | App |

Payload (JSON), QoS **1**, retain **false** for most scan tags (retain **true** for HMI state OUT: `MODE`, `PERM_OK`, `TRIP_ACTIVE`):

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

### Soft-PLC stuck `offline` / Start does nothing

If the Lovelace board shows Soft-PLC **offline**, Mode **STOP**, Start ready **Off**, and pressing Start has no effect:

1. Confirm **Mosquitto** is running and HA’s **MQTT** integration is connected to that broker.
2. Confirm **PLCAssistant** App is **Started**. Soft-PLC and the thin integration must share the same `instance_id` (default `default`).
3. Open the App log and look for `Soft-PLC MQTT connecting` / `Soft-PLC MQTT scan attached`. Connect failures usually mean Mosquitto is down or App MQTT username/password do not match the broker.
4. **Update** the App to **0.1.27+**. From **0.1.16**, App Start that syncs the thin integration **requests a Core restart** automatically (opt out with `PLCASSISTANT_AUTO_CORE_RESTART=0`). From **0.1.27**, after that version is loaded, later App syncs that leave a newer on-disk integration show **Restart of Home Assistant required** on Settings → System → Updates until Core reloads. From **0.1.17**, Soft-PLC also writes `config/plcassistant/runtime.json` and the HMI polls it when MQTT is silent. From **0.1.18**, that file bridge also mirrors active setpoints and reservoir level. From **0.1.19**, Level setpoint requests also write `config/plcassistant/inputs.json` so Active level SP tracks the HMI when MQTT is silent. From **0.1.21**, Soft-PLC no longer owns plant physics — plant tags are MQTT **IN**, and MQTT status includes `scan_period_s`. From **0.1.22**, the thin integration runs the **skid plant simulator** and publishes live tank/reservoir/flow IN. From **0.1.23**, the simulator also supports **unit-op / custom-ODE model documents**. From **0.1.24**, presets are selectable via Options / `set_dynamics_preset`. From **0.1.25**, use the sidebar **Dynamics** tab for the block editor. From **0.1.26**, enter **state equations** and **measurement equations** one row at a time; predefined blocks expose their dynamics.
5. Re-open the **PLCAssistant** sidebar — Soft-PLC should show `stopped` and Start ready **On** when healthy; then press **Start**.

From **0.1.14**, the App heartbeats retained status and publishes an MQTT last-will `offline`; the integration caches MQTT payloads and hydrates sensors on add. From **0.1.15**, HA runtime always attempts Mosquitto even when `/data/options.json` is missing/empty (seeds defaults on App Start) and retains MODE / PERM_OK / TRIP_ACTIVE for hydrate. From **0.1.16**, thin-integration sync requests Core restart so the HMI picks up Soft-PLC status without a missed manual step. From **0.1.17**, a shared HA-config file bridge hydrates the HMI when MQTT never reaches Core. From **0.1.18**, the bridge includes `SP_LEVEL` / `SP_FLOW` / `LT_RES` so active setpoints and reservoir are not stuck at 0 when MQTT is silent. From **0.1.19**, the Level setpoint request (`SP_LEVEL_REQ`) also crosses the file bridge so Active level SP follows the HMI slider. From **0.1.21**, plant PVs flip to Soft-PLC IN and the live App drops `MockProcess`. From **0.1.22**, the integration skid simulator restores live plant motion over MQTT. From **0.1.23**, unit-op / custom-ODE model documents compile into the same dynamics core. From **0.1.24**, operators select presets from Options flow / `set_dynamics_preset`. From **0.1.25**, the sidebar **Dynamics** view hosts a unit-op / ODE block editor that saves under `config/plcassistant/models/` and applies via plant reload. From **0.1.26**, Custom ODE uses per-row state/algebraic equations and Soft-PLC tags are authored as measurement equations (`y = g(x,u,θ)`). From **0.1.27**, Settings → System → Updates shows **Restart required** when a later App sync leaves a newer thin integration on disk than Core has loaded. From **0.1.28**, Operate plant level/flow Numbers use box mode and hydrate from the live simulator so values stay readable on the HMI.

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
