# 06 — PID faceplate contract (SWD-183)

**Tracker:** [SWD-183](https://marcusknielsen.atlassian.net/browse/SWD-183)  
**Depends on:** [`05-datablocks.md`](05-datablocks.md)

## Purpose

Operator faceplates for Soft-PLC PID loops use **SP-source modes**
(Manual / Automatic / Remote). The Datablock is system source of truth;
HA entities and Lovelace cards write into it.

Classic **output Manual** (operator sets CV directly) is deferred.

## Modes

| Mode | Code | Active SP source | How entered |
|------|------|------------------|-------------|
| Manual | `0` | `*_SP_MAN` | Write Man SP (auto-flip) or set mode |
| Automatic | `1` | `*_SP_AUTO` | Explicit mode only |
| Remote | `2` | `*_SP_REM` | Write Rem SP (auto-flip) or set mode |

Writing Automatic SP does **not** change mode.

## Demo tags (`DB_Tank`)

| Loop | Mode | SP Man / Auto / Rem | Active SP | PV | CV |
|------|------|---------------------|-----------|----|----|
| Level | `LEVEL_MODE` | `SP_LEVEL_MAN` / `SP_LEVEL_AUTO` / `SP_LEVEL_REM` | `SP_LEVEL` | `LT_TANK` | `SP_FLOW` (cascade) |
| Flow | `FLOW_MODE` | `SP_FLOW_MAN` / `SP_FLOW_AUTO` / `SP_FLOW_REM` | `SP_FLOW` | `FT_INLET` | `CMD_SPEED` |

Legacy `SP_LEVEL_REQ` is the **Automatic writer** for the level loop when
declared on the Datablock — it feeds the Automatic SP source even when
`SP_LEVEL_AUTO` also has a retained sample. When REQ is absent, Automatic
uses `SP_LEVEL_AUTO`. Writing REQ from the HMI also mirrors into
`SP_LEVEL_AUTO` (retained IN sync).

### Flow MAN/REM demo approximation

When flow SP-source mode is Manual or Remote, Soft-PLC publishes the muxed
`SP_FLOW` override for the faceplate, but `CMD_SPEED` for that scan still
comes from the cascade PI using the level loop CV as Automatic flow SP.
Full output-manual / bumpless flow override is deferred.

### Tunings

`LEVEL_KP`, `LEVEL_KI`, `FLOW_KP`, and `FLOW_KI` IN tags (defaults aligned
with `CascadeConfig`: 40 / 5 / 12 / 2) are applied into the live Soft-PLC
`Skid` cascade each scan when bound. `LEVEL_KD` / `FLOW_KD` are declared for
faceplate parity; the wedge cascade PI does not use D terms yet.

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

JS is served from `/plcassistant_static/` and registered via
`frontend.add_extra_js_url` on integration setup. Fallback entity rows remain
on the Operate board if custom cards are not loaded.
