# PLCAssistant Lovelace dashboard

Bundled template (`plcassistant.yaml`) is the default Soft-PLC HMI.

## Sidebar (automatic)

When the PLCAssistant integration loads, it:

1. Installs this YAML under `/config/dashboards/plcassistant.yaml` if missing
   (or refreshes a **stock** board that still lacks the status card, or is
   explicitly on an older `plcassistant_dashboard_version`)
2. Registers a Lovelace panel **PLCAssistant** at `/plcassistant-skid` with
   **Show in sidebar** enabled

After **App Update → restart Home Assistant Core → add/reload PLCAssistant**,
open **PLCAssistant** in the sidebar. No copy/paste step.

You can still create additional Lovelace dashboards in HA and reuse these
entities for your own SCADA boards. Fully custom YAML under
`dashboards/plcassistant.yaml` is left alone; stock boards missing
`sensor.plcassistant_status`, or still marked on an older stock version, are
refreshed on update so the status card and help appear.

## Operate (SCADA HMI)

Operate is a compact SCADA screen — not an entity browser:

| Area | Contents |
|------|----------|
| **Status** | Soft-PLC, Mode (`STOP` / `RUNNING` / `TRIPPED`), Trip |
| **Commands** | Start / Stop / Reset |
| **Process** | Glance PVs (tank, reservoir, inlet flow, pump speed) — tap opens more-info / history |
| **PID** | Level + Flow analog-controller faceplates (PV/SP bars, MV bar; MAN writes MV, AUTO writes SP) |

Engineering surfaces stay on the **Dynamics** and **Datablocks** tabs.

Press **Start** → Soft-PLC status `running`, MODE `RUNNING`, and Soft-PLC CVs
update. Plant PVs are Soft-PLC **IN** sensors from the integration simulator;
PID cards edit mode / SP / CO (entities still exist for automation / custom boards).

## Writable vs read-only

| Entity | Role |
|--------|------|
| `number.plcassistant_sp_level_req` | Operator **level setpoint request** (writable; Automatic source; click SP bar or dialog) |
| `number.plcassistant_co_level_man` / `_co_flow_man` | Output Manual MV (writable in MAN; click MV bar or dialog) |
| `number.plcassistant_sp_level_man` / `_rem` / `level_mode` | Level PID legacy Manual/Remote SP + mode (0/1/2) |
| `number.plcassistant_sp_flow_man` / `_rem` / `flow_mode` | Flow PID Remote SP + mode (flow AUTO is cascade; MAN writes CO) |
| `sensor.plcassistant_pid_level` / `_pid_flow` | Compound PID faceplate (mode + attributes) |
| `sensor.plcassistant_lt_tank_in` / `_lt_res_in` / `_ft_inlet_in` | Plant PVs as Soft-PLC **IN** (Operate Process glance) |
| `number.plcassistant_lt_tank_in` / `_lt_res_in` / `_ft_inlet_in` | Plant PV **nudges** (writable; same tags) |
| `button.plcassistant_start` / `_stop` / `_reset` | Operator commands |
| `sensor.plcassistant_*` (other) | Soft-PLC OUT (CVs, active SPs, MODE / status) — read-only |

## Upgrading from App 0.1.10 / 0.1.19 / 0.1.28

**0.1.35** adds the inspectable Library editor and generic PID block: shipped PID edits/reset, custom math-equation blocks, copy-on-place equations/params, and automatic `level_pi`/`flow_pi` migration.

**0.1.34** adds the App Task scheduling editor: Task CRUD, ordered Program call lists, Save without live apply, and Apply (restart) for the saved schedule.

**0.1.33** adds the App Program engineering surface: Program cards, create, Diagram/Log/Settings, and selected-Program canvas APIs.

Entity IDs changed in **0.1.11** (OUT tags became sensors; setpoint request renamed),
again in **0.1.20** (plant PVs flipped back to Soft-PLC IN Numbers), and in
**0.1.32** (Soft-PLC project organization: Tasks → Programs; legacy flat program auto-migrates):

| Area | Behavior |
|------|----------|
| App `/api/project` | GET/PUT Soft-PLC Task + Program tree |
| Canvas `/api/program` | Main Task program (unchanged editor path) |

**0.1.31** (no LOS latch from settled/stale plant file timestamps):

| Tag | Behavior |
|-----|----------|
| Plant file IN | Hold last good when `ts` stale; plant heartbeat refreshes settled PVs |

**0.1.30** (Soft-PLC plant IN via file bridge when MQTT silent — level settles to SP):

| Tag | Entity |
|-----|--------|
| Plant IN → Soft-PLC | MQTT primary + `config/plcassistant/inputs.json` fallback |

**0.1.29** (Operate Process display uses plant IN **sensors**; Numbers stay for nudges):

| Era | Plant tags |
|-----|------------|
| 0.1.10 | `number.plcassistant_lt_tank_in` (early mock IN) |
| 0.1.11–0.1.19 | `sensor.plcassistant_lt_tank` (Soft-PLC plant OUT) |
| 0.1.20–0.1.28 | `number.plcassistant_lt_tank_in` (Soft-PLC plant IN display + nudge) |
| **0.1.29+** | `sensor.plcassistant_lt_tank_in` (Operate display) + `number.*_in` (nudge) |

After App Update + Core restart: stock Lovelace refreshes to dashboard version **15**.
If personal boards still show unavailable plant Numbers, delete stale unavailable
entities in the entity registry (or remove/re-add the integration). Update any
personal dashboards that still reference plant Numbers for Process display.

**0.1.65** PID faceplate: controller settings fields keep drafts while the dialog is open (live hass no longer restomps Kp/Ki/…). Stock Lovelace still dashboard version **28**.

**0.1.64** PID faceplate: SP ramping (`sp_ramp_max`) with an orange SP-bar segment from current SP to target. Stock Lovelace still dashboard version **28**.

**0.1.63** PID faceplate: settings gear panes for all standardised PID parameters (Gains / Structure / Output / Filter). Stock Lovelace still dashboard version **28**.

**0.1.62** PID faceplate: writable analog fill is a muted activity green. Stock Lovelace still dashboard version **28**.

**0.1.61** PID faceplate: focused analog popup (value/min/max), MV label, ε between PV and SP. Stock Lovelace still dashboard version **28**.

**0.1.60** PID faceplate: colour fill on the writable analog, values on the bars, numeric popup (no pointer-set), nudge arrows, settings gear for Kp/Ki/Kd. Stock Lovelace still dashboard version **28**.

**0.1.59** PID faceplate chrome is a shared element module plus a developer sandbox (`tools/pid-faceplate`). Lovelace card behaviour unchanged. Stock Lovelace still dashboard version **28**.

**0.1.58** Lovelace PID cards: analog-controller face (vertical PV/SP, horizontal CO), DCS MAN/AUTO/REM (MAN writes CO). Stock Lovelace still dashboard version **28**.

**0.1.57** Builtin PID follows the IFAC 2024 incremental reference (filter, Tx, auto/uman, windup). Lovelace faceplates unchanged. Stock Lovelace still dashboard version **28**.

**0.1.56** Lovelace PID cards: ISA-5.1 ε/P/I/D chrome, first-class ε, ISA-101 colour only for caution/abnormal. Stock Lovelace still dashboard version **28**.

**0.1.55** ISA-5.1 three-mode PID glyph on the Diagram; ISA-TR5.9 Parallel + Bauer hybrid PID; Lovelace faceplate labels PV / SP / CO. Stock Lovelace still dashboard version **28**.

**0.1.54** One Max pump flow knob: plant capacity writes Soft-PLC cascade level CV; pump block no longer desyncs. Stock Lovelace still dashboard version **28**.

**0.1.53** Operate is a SCADA HMI (status, Start/Stop/Reset, Mode, key PVs, PID cards) — not an entity dump. Tap Process values for history. Stock Lovelace refreshes to dashboard version **28**.

**0.1.48** Compact PID faceplate: 2dp KPIs, single-row mobile, tap opens edit popup. Stock Lovelace refreshes to dashboard version **27**.

**0.1.47** PID card Set SP no longer hijacked by data-mode (float error). Stock Lovelace refreshes to dashboard version **26**.

**0.1.46** PID faceplate climate-style refresh + stable SP text editing while RUNNING. Stock Lovelace refreshes to dashboard version **25**.

**0.1.45** File runtime mirrors SP_FLOW_AUTO; Program Apply syncs live Skid; missing cascade falls back so Start drives CVs. Stock Lovelace refreshes to dashboard version **24**.

**0.1.44** Start drives PID CVs via common tag↔pin io_wires; faceplate KP/KI sync into live instances. Stock Lovelace refreshes to dashboard version **23**.

**0.1.43** Flow Manual SP drives flow PI / CMD_SPEED; Level CV faceplate uses `SP_FLOW_AUTO`. Stock Lovelace refreshes to dashboard version **22**.

**0.1.42** Start/cascade reliability: file seed beats stale MQTT retain, awaited
qos1 Start/Stop + operator seed, honest Soft-PLC status (no optimistic running),
plant file writes ≤1 Hz + CMD watchdog pause while frozen, PID mux + Auto SP
mode flip + card draft preserve. Stock Lovelace refreshes to dashboard version
**21**.

**0.1.41** cascade defaults Level Manual / Flow Automatic, batch-seeds operator
IN (no cold-start Number publish storm), defers plant sim until after entity
setup, Level PID Auto writes ``SP_LEVEL_REQ``. Stock Lovelace refreshes to
dashboard version **20**.

**0.1.40** registers PID Lovelace cards as dashboard resources (fixes Configuration error),
defaults SP-source mode to **Manual**, and avoids mode-flip on Number setup hydration.
Stock Lovelace refreshes to dashboard version **19**.

**0.1.39** fixes HA Core integration setup: Datablock catalog is HA-local (no Soft-PLC
``plcassistant.io`` import on Core). Stock Lovelace still refreshes to dashboard version **18**.

**0.1.38** ships review-fix for PID faceplates: REQ remains Automatic writer,
Datablock Kp/Ki applied into Soft-PLC cascade each scan, KD bindings, Operate
board includes the generic block-list card, App online strip shows schedule
task/program counts. Stock Lovelace refreshes to dashboard version **18**.

**0.1.37** adds PID faceplates: Manual / Automatic / Remote SP sources,
`sensor.plcassistant_pid_level` / `_pid_flow`, Lovelace
`custom:plcassistant-pid-card` + `custom:plcassistant-block-list-card`, and Soft-PLC
App online strip (runtime + schedule status). Stock Lovelace refreshes to
dashboard version **17**.

**0.1.36** adds Datablock tag mapping: HA Datablocks configuration panel, `DB_Tank` example, Program↔Datablock access, store at `config/plcassistant/datablocks.json`.
