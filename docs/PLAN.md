# Implementation plan: HA entity I/O bridge (SWD-71)

## Summary

Build the **Home Assistant side** of PLCAssistant’s entity↔PLC-tag bridge: a thin **HACS custom integration** that owns the binding registry and config UX, plus a shared **`plcassistant_contract`** library for schema, coercion, freshness, and fail-safe pure functions. Sync bindings to the future addon via the locked **`PutBindings`** control-plane op. Expose the named **diagnostic entities** from [IO_HAL.md](IO_HAL.md), fed by a mockable `GetStatus` client.

This phase does **not** host the scan loop or OpenPLC (that is [SWD-69](https://marcusknielsen.atlassian.net/browse/SWD-69)). Behavioural contracts remain [IO_HAL.md](IO_HAL.md), [PACKAGING.md](PACKAGING.md), and [HANDOFF.md](HANDOFF.md) from shipped [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70).

## Scope

### In

- Python package `plcassistant_contract`: binding model types/validation, coercion matrix, freshness/stale/cold-start, fail-safe policy application — **no** Home Assistant or OpenPLC imports
- HACS custom integration `plcassistant` (technical domain name):
  - Config entry (addon URL / discovery placeholder, auth secret reference)
  - Options: `scan_period_ms` (default **100**), global fail-safe defaults
  - Binding registry as source of truth (persist in config entry / store)
  - Config-flow / options **UI** to add/edit/disable bindings (all IO_HAL fields needed for MVP)
  - Control-plane client: `PutBindings`, `PutScanOptions`, `GetStatus` (HTTP adapter; mockable)
  - Diagnostic HA entities per IO_HAL diagnostics table
  - HA services: `start` / `stop` / `reload` → control-plane ops (may report “addon unavailable” until SWD-69)
- Table-driven unit tests for contract; integration tests with fake addon HTTP
- Docs: short developer note linking IO_HAL fields to UI + sync payload

### Out

- Addon process, WebSocket HAL loop, OpenPLC (SWD-69)
- Modbus TCP (post-MVP)
- Lovelace/Grafana dashboards (SWD-68)
- Full Supervisor packaging / HACS publish metadata polish (SWD-67 may harden)
- YAML-first binding authoring as the primary UX (optional import later)
- OpenPLC-specific address encoding beyond opaque `tag` strings

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Contract vs architecture** | Implement against [IO_HAL.md](IO_HAL.md); do not invent a second binding model | SWD-70 lock |
| **Ownership split** | Integration owns registry + UI + sync **client**; HAL loop stays in addon (SWD-69) | [HANDOFF.md](HANDOFF.md) |
| **Shared lib** | **Ship `plcassistant_contract`** in-repo | Testable pure functions; reusable by SWD-69 HAL |
| **Config UX** | **UI config entry / options** primary | Prefer UI from SWD-70 open items |
| **YAML** | Out of MVP; may add import later | Avoid dual SoT |
| **memory_mirror** | **In MVP** | Needed for setpoints; conflict rule below |
| **Mirror conflict** | UI→PLC every scan; PLC→HA only if `mirror_to_ha: true` | IO_HAL proposal locked |
| **Sync without addon** | Client + **test double** HTTP server; graceful “unavailable” in UI | Unblocks SWD-71 before SWD-69 |
| **Diagnostics** | Integration creates entities; values from `GetStatus` / last push | IO_HAL phase ownership |
| **Repo layout** | `packages/plcassistant_contract/` + `custom_components/plcassistant/` | HA convention + shared lib |
| **Transport** | Control plane over HTTP (addon base URL from config); Supervisor ingress details deferred to SWD-67/69 | PACKAGING adapters |

## Behaviour (MVP)

### Binding registry

- Persist list of bindings matching IO_HAL common + direction-specific fields.
- Validate: required fields; `safe_value` when policy is `force_value`; `service` when `write_mode: service`.
- On change (add/edit/delete/enable): persist, then call `PutBindings` (and `PutScanOptions` when options change).
- If addon unreachable: keep local SoT; set `bridge_connected`-related diagnostics false / error; retry on reload service.

### Coercion & fail-safe (contract lib)

- Implement IO_HAL coercion table and input/output policies including **cold_start_policy** (default `force_zero`).
- Pure functions: `(binding, raw_ha_value, context) → effective_value` and output fault application.
- Injectable clock for stale_after_s tests.

### Diagnostics entities

Create at least: `scan_period_ms`, `last_cycle_ms`, `overrun_count`, `bridge_connected`, `bridge_lag_ms`, `stale_binding_count`, `fail_safe_active`, `binding_error_count`, `runtime_state`. Until SWD-69 emits real metrics, client may return zeros / `stopped` / disconnected — entities still exist and update from mock/status.

### Services

| Service | Behaviour |
|---------|-----------|
| `plcassistant.reload` | Re-read options/bindings; `PutBindings` + `PutScanOptions` |
| `plcassistant.start` / `stop` | Forward `Start` / `Stop`; surface errors if addon missing |

## Constraints

- Must not reimplement scan HAL inside the HACS integration
- Must not embed long-lived passwords in git; secrets via config entry
- Soft real-time / non-safety messaging unchanged
- Tests required for all behavioural packages (contract + sync client + validation)

## Acceptance criteria

1. `plcassistant_contract` exists with table-driven tests covering coercion, cold-start, stale, and output `on_bridge_fault` / `critical` defaults.
2. HACS integration can create a config entry, manage bindings via UI (or options flow sufficient for MVP), and persist them as SoT.
3. Changing bindings triggers `PutBindings` to a configurable addon base URL; with a test double, payload matches the contract schema.
4. Named diagnostic entities from IO_HAL are registered and update from `GetStatus` (including mock).
5. `reload` / `start` / `stop` services exist and call the control-plane client (documented no-op/error without addon).
6. README or `docs/` note points implementers of SWD-69 at contract package + sync payload shape.
7. No Modbus path; no scan loop in the integration.

## Work packages

1. **Contract library** — `plcassistant_contract`: models, validation, coercion, freshness/fail-safe; pytest table-driven suites.
2. **Integration skeleton** — `custom_components/plcassistant`: manifest, config flow (addon URL + token), options (`scan_period_ms`, defaults), domain setup.
3. **Binding registry + UI** — store, CRUD/options UI for input/output/`memory_mirror` bindings per IO_HAL fields.
4. **Control-plane client** — `PutBindings` / `PutScanOptions` / `GetStatus` / `Start`/`Stop`/`Reload`; HTTP adapter + fake server tests; wire reload/start/stop services.
5. **Diagnostics entities** — expose IO_HAL sensors/binaries; poll or push from `GetStatus`; tests with fake status payloads.

## Open items

- Exact Supervisor ingress URL discovery vs manual base URL — default **manual URL** in SWD-71; auto-discovery in SWD-67.
- Whether options flow vs dedicated panel cards for many bindings — prefer **options / config flow lists** first; panel only if UX blocked.
- HA Core version pin for custom component — choose current stable at implement time.
- Real addon auth handshake — stub bearer token in SWD-71; finalize in SWD-69/67.

## Tracker

- Provider: jira
- Story: [SWD-66](https://marcusknielsen.atlassian.net/browse/SWD-66)
- Task: [SWD-71](https://marcusknielsen.atlassian.net/browse/SWD-71)
- Architecture (shipped): [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70) — [ARCHITECTURE.md](ARCHITECTURE.md), [IO_HAL.md](IO_HAL.md), [PACKAGING.md](PACKAGING.md), [HANDOFF.md](HANDOFF.md), [PLAN_SWD-70.md](PLAN_SWD-70.md)
- Sub-tasks: [SWD-78](https://marcusknielsen.atlassian.net/browse/SWD-78) (contract), [SWD-80](https://marcusknielsen.atlassian.net/browse/SWD-80) (skeleton), [SWD-77](https://marcusknielsen.atlassian.net/browse/SWD-77) (registry/UI), [SWD-76](https://marcusknielsen.atlassian.net/browse/SWD-76) (sync client), [SWD-79](https://marcusknielsen.atlassian.net/browse/SWD-79) (diagnostics)

## Next

`/review-fix SWD-71` — Review implementation and auto-fix until clean.
