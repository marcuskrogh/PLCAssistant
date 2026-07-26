# Packaging blueprint: addon + HACS integration

**Status:** Accepted  
**Task:** [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70) / Sub-task [SWD-75](https://marcusknielsen.atlassian.net/browse/SWD-75)  
**Architecture:** [docs/ARCHITECTURE.md](ARCHITECTURE.md)  
**I/O contract:** [docs/IO_HAL.md](IO_HAL.md)

## Goal

Split PLCAssistant so the **scan soft-PLC** runs isolated from Home Assistant Core, while configuration and diagnostics feel native inside HA.

## Components

| Component | Package type | Responsibility |
|-----------|--------------|----------------|
| **plcassistant** (name TBD) | Supervisor **addon** / app | Run OpenPLC Runtime; host I/O HAL loop; program upload API surface; optional Modbus later |
| **plcassistant** integration | **HACS** custom integration | Config entries; binding registry SoT; diagnostic entities; start/stop/reload services; discovery of addon |
| **plcassistant_contract** (optional shared lib) | Python package (no HA/OpenPLC imports) | Binding schema types + pure coercion / fail-safe / freshness functions only — usable by addon HAL and integration tests |
| **OpenPLC Editor** | External desktop app | Author LD/ST/FBD; upload to runtime (MVP) |
| **HA Core** | Existing | Entities, Lovelace, Influx export — unchanged |

If the shared lib is skipped, coercion/fail-safe code still lives behind the same pure-function seam **inside the addon**, with the integration owning only config serialization — do not scatter HAL logic into HACS.

## Responsibility matrix

| Concern | Addon | HACS integration |
|---------|-------|------------------|
| Scan cycle + OpenPLC process | ✓ | |
| WebSocket client to Core (entity read / service call) | ✓ | |
| Persist binding registry | | ✓ (config entry / storage) |
| Push/sync bindings to addon | ✓ consumes | ✓ publishes |
| User config UI | | ✓ |
| Diagnostic HA entities | | ✓ (may be fed by addon status API) |
| Program file storage | ✓ | may show status only |
| Start / stop / reload runtime | ✓ executes | ✓ exposes HA services |
| Lovelace / Grafana | | docs only (SWD-68) |

## Supervisor / Core communication

On HAOS / Supervised, the addon should use the Supervisor proxies ([app communication](https://developers.home-assistant.io/docs/apps/communication/)):

| Need | Mechanism |
|------|-----------|
| Call HA HTTP API | `http://supervisor/core/api/` + `Authorization: Bearer $SUPERVISOR_TOKEN` |
| HA WebSocket | `ws://supervisor/core/websocket` + supervisor token |
| Addon config | `config.yaml`: `homeassistant_api: true` (and related flags as required) |

The HACS integration talks to the addon over:

- Supervisor addon API / ingress, and/or  
- A small authenticated HTTP API on the addon (localhost / hassio network)

Transport is an **adapter**; the **control plane** is the contract below. Exact auth handshake is an SWD-67/69 detail; blueprint requirement: **integration must not embed long-lived user passwords in git**; prefer Supervisor token or HA long-lived token stored in config entry secrets.

### Control plane (abstract ops)

| Op | Direction | Purpose |
|----|-----------|---------|
| `PutBindings` | Integration → Addon | Push binding registry (integration is source of truth) |
| `GetStatus` / `StatusPush` | Addon → Integration | Metrics for diagnostic entities (`bridge_connected`, cycle times, …) |
| `Start` / `Stop` / `Reload` | Integration → Addon | Runtime lifecycle |
| `GetProgramStatus` | Integration → Addon | Program loaded/version/running |
| `PutScanOptions` | Integration → Addon | `scan_period`, global fail-safe defaults |

Do **not** invent a second binding schema or metrics model in either package. HTTP/ingress only carry these ops.

## Configuration ownership

| Data | Owner | Notes |
|------|-------|-------|
| Binding list | Integration config entry | Source of truth for entity↔tag maps |
| Scan period, fail-safe defaults | Integration (global options) | Pushed to addon on change |
| OpenPLC program blob | Addon storage | Version/status reported to integration |
| Runtime credentials / ports | Addon options | Documented for advanced users |

## Lifecycle

```text
Install addon (Supervisor) → Install HACS integration →
  Add integration config entry (point at addon) →
  Configure bindings (PutBindings) →
  Upload program (OpenPLC Editor) → Start / Reload runtime →
  Running (empty program: runtime may Start but logic is no-op until program loaded)

Update: addon update via Supervisor; integration update via HACS
Program deploy: upload then Reload (or Start) so SWD-67/69 share one state machine
Stop: HA service → addon stops scan / OpenPLC
Unload integration: stop commanding addon; bindings retained in config entry
```

## Install targets

| Target | MVP support |
|--------|-------------|
| Home Assistant OS / Supervised | **Primary** |
| Container / Docker Compose (Core only) | Documented path: run runtime container beside Core; integration uses URL + token (SWD-67) |
| Home Assistant Core venv bare metal | Same as container path; best-effort |

## Non-responsibilities

- Addon does **not** render HMI (Lovelace/FUXA do).  
- Integration does **not** execute scan logic.  
- Neither replaces InfluxDB/Grafana.

## Implementation seams (testability)

- Addon HAL: injectable HA client interface (see IO_HAL.md).  
- Integration: binding store as pure data; sync client mockable in tests.  
- No hard-wired wall-clock in coercion/fail-safe unit tests.

## Naming (provisional)

Use `plcassistant` as technical domain until branding is finalized in SWD-67. User-facing name remains **PLCAssistant**.
