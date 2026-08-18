# 06 — PID faceplate contract (SWD-183 / SWD-369)

**Tracker:** [SWD-369](https://marcusknielsen.atlassian.net/browse/SWD-369)  
**Depends on:** [`05-datablocks.md`](05-datablocks.md)

## Purpose

Operator faceplates for Soft-PLC PID loops follow **DCS analog-controller**
practice under **ISA-101** high-performance HMI rules (grayscale normal chrome;
colour only for caution/abnormal). **ANSI/ISA-112.00.01-2025** is the SCADA
lifecycle / terminology standard; it tells organisations to keep an HMI style
guide and points that guide at ISA-101. It does **not** specify PID bar
geometry. ISA-TR5.9 names stay on the Datablock: **PV**, **SP**, **CO**.
Faceplates label the controller output **MV** (manipulated variable).

The Datablock is system source of truth; HA entities and Lovelace cards write
into it. The `cv` pin name is unchanged; faceplates label that signal **MV**.

## Modes

DCS controller modes (not three parallel SP sources while the PID still computes CO):

| Mode | Code | Operator write | Algorithm |
|------|------|----------------|-----------|
| Manual | `0` | **MV** (`CO_*_MAN` → Bauer `uman`) | PID `auto=false`; output holds |
| Automatic | `1` | **SP** when the Auto entity is a Number | PID computes CO from local SP |
| Remote | `2` | none (cascade / remote SP) | PID stays in auto; faceplate does not write SP or CO |

Highlight the writable analog by colouring its **fill** (`--primary-color`).
Mode buttons stay grayscale invert — **do not** colour-code Man / Auto / Rem.
Caution / abnormal still override the fill. Writing CO Set flips the loop to
Manual. Writing Auto SP Set flips to Automatic (SWD-222). Remote Set is
disabled on the faceplate.

Flow **Automatic** remains **cascade** (slave CAS behaviour, SWD-221): the Auto
SP entity is `sensor.plcassistant_sp_flow_auto`, so the flow SP bar is not
operator-writable in AUTO.

Level loop **CO** is published as `SP_FLOW_AUTO` (cascade request into flow).
Active flow SP is muxed onto `SP_FLOW` for display. Flow Remote SP is applied to
the flow PI each scan (SWD-223). Flow Manual is output Manual, not an SP
override.

## Faceplate geometry

Compact analog-controller face:

1. ISA-5.1 three-mode chrome (ε / P / I / D) matching the App Diagram glyph
2. Header: title and settings gear
3. two thin tall vertical bars: PV (left) and SP (right), with values on the bars
4. Signed **ε** between the PV and SP bars (caution/abnormal colour)
5. A thicker horizontal **MV** bar below, with its value beside the bar
6. `<< < > >>` nudges (±1.0 / ±0.1) on the writable analog
7. MAN / AUTO / REM on the face (grayscale active invert)
8. Focused numeric popup for the clicked analog (current value, min, max; no pointer-position set)
9. Settings popup for Kp / Ki / Kd

Click any analog bar to open a popup for **that** analog (value, min, max, unit).
Set is shown only when the analog is the operator write target. Nudge arrows
change the writable analog directly.

Scales: level PV/SP 0–0.40 m; flow PV/SP 0–8 L/min; level MV 0–8 L/min; flow MV
0–100%.

## Demo tags (`DB_Tank`)

| Loop | Mode | SP Man / Auto / Rem | Active SP | PV | CO | Manual CO |
|------|------|---------------------|-----------|----|----|-----------|
| Level | `LEVEL_MODE` | `SP_LEVEL_MAN` / `SP_LEVEL_AUTO` / `SP_LEVEL_REM` | `SP_LEVEL` | `LT_TANK` | `SP_FLOW_AUTO` (level CO / `cv`) | `CO_LEVEL_MAN` |
| Flow | `FLOW_MODE` | `SP_FLOW_MAN` / `SP_FLOW_AUTO` / `SP_FLOW_REM` | `SP_FLOW` | `FT_INLET` | `CMD_SPEED` | `CO_FLOW_MAN` |

Legacy `SP_LEVEL_REQ` is the **Automatic writer** for the level loop when
declared on the Datablock — it feeds the Automatic SP source even when
`SP_LEVEL_AUTO` also has a retained sample. When REQ is absent, Automatic
uses `SP_LEVEL_AUTO`. Writing REQ from the HMI also mirrors into
`SP_LEVEL_AUTO` (retained IN sync).

Demo defaults: Level **Automatic**, Flow **Automatic** (cascade). Level Manual
is available so the operator can hold cascade CO. Selecting Manual copies live
CO into `CO_*_MAN` (bumpless hold).

### Flow Remote SP (SWD-223)

When flow mode is Remote, Soft-PLC applies `SP_FLOW_REM` to `flow_pi.sp` for
that scan via runtime `prefer_context` (cascade wire left intact on the
Program) so `CMD_SPEED` tracks the remote SP. Automatic mode keeps the level
CO → flow SP wire. Manual mode holds `CO_FLOW_MAN` (`uman`). Level faceplate
CO reads `SP_FLOW_AUTO` (true level `cv`), not the muxed active `SP_FLOW`.

### Tunings

`LEVEL_KP`, `LEVEL_KI`, `FLOW_KP`, and `FLOW_KI` IN tags (defaults aligned
with `CascadeConfig`: 40 / 5 / 12 / 2) are applied into the live Soft-PLC
`Skid` cascade **and synced into executing PID instance params** each scan
when bound (SWD-224). `LEVEL_KD` / `FLOW_KD` are declared for
faceplate parity; the wedge cascade PI does not use D terms yet.

Process tag ↔ PID pin bridging uses the common `TagPinWire` format
(`plcassistant.surface.io_wires`) so Start → `running` → CV is one
testable map rather than hardcoded per-pin assignments. Bauer `auto` /
`uman` arrive as `_SHELL.LEVEL_AUTO` / `_SHELL.LEVEL_UMAN` (and flow twins).

Soft-PLC helpers live in
`plcassistant.io.pid_loop` (`select_active_sp`, `apply_sp_write`,
`apply_co_write`, `operator_write_target`, `faceplate_from_image_tags`).

## HA compound entity

| Entity | State | Attributes |
|--------|-------|------------|
| `sensor.plcassistant_pid_level` | `manual` / `automatic` / `remote` | `pv`, `sp`, `sp_man`, `sp_auto`, `sp_rem`, `cv`, `co_man`, `write_target`, `kp`, `ki`, `kd`, `loop_id`, related `*_entity` ids including `cv_man_entity`, `kp_entity`, `ki_entity`, `kd_entity` |
| `sensor.plcassistant_pid_flow` | same | same |

## Lovelace cards

| Card | Config |
|------|--------|
| `custom:plcassistant-pid-card` | `{ entity: sensor.plcassistant_pid_level }` |
| `custom:plcassistant-block-list-card` | `{ entity: <sensor>, include?: [...] }` |

JS is served from `/plcassistant_static/` and registered as Lovelace
**resources** on integration setup (storage mode, with `?v=` cache-bust;
YAML mode falls back to `frontend.add_extra_js_url`). Stock Operate (SWD-229)
is a SCADA layout with PID cards only — no fallback entity dump. Custom boards
may still list the underlying Number/sensor entities if cards fail to load.

Chrome (glyph, KPI row, analog bars, mode row) lives in
`www/pid-faceplate-elements.js`. The Lovelace card imports that module. Iterate
the elements in a browser without the App:

```bash
./tools/pid-faceplate/serve.sh
```

Then open http://127.0.0.1:8765/tools/pid-faceplate/. Ship an App build only
when operators should receive chrome changes.

The PID card uses an ISA-5.1 three-mode chrome strip (ε / P / I / D) matching the
App Diagram glyph, analog bars (thin tall vertical PV/SP, thicker horizontal MV)
with values on the bars, **ε** between PV and SP, nudge arrows, and a settings
gear for Kp / Ki / Kd. Clicking a bar opens a focused numeric popup for that
analog (value, min, max, unit). Set is shown only when the analog is writable.
Man / Auto / Rem are controller modes; the active button stays grayscale invert.
The writable analog **fill** uses `--primary-color`. Colour otherwise follows
ISA-101 high-performance HMI practice: caution uses Home Assistant
`--warning-color`, abnormal uses `--error-color`, applied to relative |ε| and
to an MV bar at clamp (~0% or ~100% of scale). Text+`inputmode=decimal` editors
keep intermediate edits alive across live Soft-PLC hass updates. Typography uses
Home Assistant Lovelace design tokens (`--ha-font-family-body`,
`--ha-card-header-font-size`, `--ha-font-size-*`) so the faceplate matches
surrounding entities / glance cards. Compound PID attributes are rounded to 2dp
when published. **Set** (or Enter) commits; Esc cancels a dirty draft.

Cascade demo defaults (SWD-369): Level **Automatic**, Flow **Automatic**.
Operator IN defaults are batch-seeded once at setup (no per-Number MQTT/file
storm). Level faceplate Automatic writes ``SP_LEVEL_REQ`` (the mux Automatic
writer). Setup hydration of Man/Rem SP Numbers must not mode-flip.
