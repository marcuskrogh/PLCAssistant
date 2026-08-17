# 06 — PID faceplate contract (SWD-183)

**Tracker:** [SWD-183](https://marcusknielsen.atlassian.net/browse/SWD-183)  
**Depends on:** [`05-datablocks.md`](05-datablocks.md)

## Purpose

Operator faceplates for Soft-PLC PID loops use **SP-source modes**
(Manual / Automatic / Remote). The Datablock is system source of truth;
HA entities and Lovelace cards write into it.

Classic **output Manual** (operator sets CO directly) is deferred. The `cv`
pin name is unchanged; faceplates label that signal **CO**.

## Modes

| Mode | Code | Active SP source | How entered |
|------|------|------------------|-------------|
| Manual | `0` | `*_SP_MAN` | Write Man SP (auto-flip) or set mode |
| Automatic | `1` | `*_SP_AUTO` | Write Auto SP (auto-flip) or set mode |
| Remote | `2` | `*_SP_REM` | Write Rem SP (auto-flip) or set mode |

Writing Man / Auto / Rem SP Set flips the loop into that source mode (SWD-222).

Level loop **CO** is published as `SP_FLOW_AUTO` (cascade request into flow).
Active flow SP is muxed onto `SP_FLOW` (Manual / Automatic / Remote). Flow Manual
or Remote SP is applied to the flow PI each scan (SWD-223) — not display-only.

## Demo tags (`DB_Tank`)

| Loop | Mode | SP Man / Auto / Rem | Active SP | PV | CO |
|------|------|---------------------|-----------|----|----|
| Level | `LEVEL_MODE` | `SP_LEVEL_MAN` / `SP_LEVEL_AUTO` / `SP_LEVEL_REM` | `SP_LEVEL` | `LT_TANK` | `SP_FLOW_AUTO` (level CO / `cv`) |
| Flow | `FLOW_MODE` | `SP_FLOW_MAN` / `SP_FLOW_AUTO` / `SP_FLOW_REM` | `SP_FLOW` | `FT_INLET` | `CMD_SPEED` |

Legacy `SP_LEVEL_REQ` is the **Automatic writer** for the level loop when
declared on the Datablock — it feeds the Automatic SP source even when
`SP_LEVEL_AUTO` also has a retained sample. When REQ is absent, Automatic
uses `SP_LEVEL_AUTO`. Writing REQ from the HMI also mirrors into
`SP_LEVEL_AUTO` (retained IN sync).

### Flow Manual / Remote SP (SWD-223)

When flow SP-source mode is Manual or Remote, Soft-PLC applies the muxed
`SP_FLOW` to `flow_pi.sp` for that scan via runtime `prefer_context` (cascade
wire left intact on the Program) so `CMD_SPEED` tracks the operator SP.
Automatic mode keeps the level CO → flow SP wire. Level faceplate CO reads
`SP_FLOW_AUTO` (true level `cv`), not the muxed active `SP_FLOW`.

### Tunings

`LEVEL_KP`, `LEVEL_KI`, `FLOW_KP`, and `FLOW_KI` IN tags (defaults aligned
with `CascadeConfig`: 40 / 5 / 12 / 2) are applied into the live Soft-PLC
`Skid` cascade **and synced into executing PID instance params** each scan
when bound (SWD-224). `LEVEL_KD` / `FLOW_KD` are declared for
faceplate parity; the wedge cascade PI does not use D terms yet.

Process tag ↔ PID pin bridging uses the common `TagPinWire` format
(`plcassistant.surface.io_wires`) so Start → `running` → CV is one
testable map rather than hardcoded per-pin assignments.

Soft-PLC helpers live in
`plcassistant.io.pid_loop` (`select_active_sp`, `apply_sp_write`,
`faceplate_from_image_tags`).

## HA compound entity

| Entity | State | Attributes |
|--------|-------|------------|
| `sensor.plcassistant_pid_level` | `manual` / `automatic` / `remote` | `pv`, `sp`, `sp_man`, `sp_auto`, `sp_rem`, `cv`, `kp`, `ki`, `kd`, `loop_id`, related `*_entity` ids |
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

The PID card (SWD-226 / SWD-228 / SWD-230) uses climate-inspired mode colours
(Man / Auto / Rem), a hero strip for PV / active SP / CO at **two decimal places**,
and text+`inputmode=decimal` SP editors so intermediate edits survive live Soft-PLC
hass updates. Typography uses Home Assistant Lovelace design tokens
(`--ha-font-family-body`, `--ha-card-header-font-size`, `--ha-font-size-*`) so the
faceplate matches surrounding entities / glance cards. Compound PID attributes are
rounded to 2dp when published. **Set** (or Enter) commits; Esc cancels a dirty draft.

Cascade demo defaults (SWD-221): Level **Manual**, Flow **Automatic**.
Operator IN defaults are batch-seeded once at setup (no per-Number MQTT/file
storm). Level faceplate Automatic writes ``SP_LEVEL_REQ`` (the mux Automatic
writer). Setup hydration of Man/Rem SP Numbers must not mode-flip.
