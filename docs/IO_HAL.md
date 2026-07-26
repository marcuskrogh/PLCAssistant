# I/O HAL contract: HA entities ↔ PLC tags

**Status:** Accepted (contract for implementation)  
**Task:** [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70) / Sub-task [SWD-74](https://marcusknielsen.atlassian.net/browse/SWD-74)  
**Consumers:** [SWD-71](https://marcusknielsen.atlassian.net/browse/SWD-71) (bridge), [SWD-69](https://marcusknielsen.atlassian.net/browse/SWD-69) (runtime)  
**Architecture:** [docs/ARCHITECTURE.md](ARCHITECTURE.md)

## Purpose

Define how PLCAssistant maps Home Assistant **entities** to soft-PLC **tags** each scan cycle, including coercion, freshness, fail-safe behaviour, and diagnostics. UI layout is deferred to SWD-71; this document is the behavioural contract.

## Roles

| Component | Role |
|-----------|------|
| **Binding registry** | Configured mappings (owned by HACS integration; consumed by addon) |
| **I/O HAL** | Process in the addon that samples HA and applies outputs |
| **Soft-PLC runtime** | OpenPLC (MVP): executes logic on tag image |
| **HA Core** | Source of truth for entity state; executor of services |

## Scan cycle contract

```text
every scan_period (best-effort):
  1. INPUT PHASE
       for each input binding:
         read entity (and optional attribute) from HA
         coerce → PLC tag type
         apply freshness / unavailable policy → effective input value
         write into runtime input image
  2. LOGIC PHASE
       run one PLC program cycle (OpenPLC)
  3. OUTPUT PHASE
       for each output binding:
         read PLC output tag
         if changed (or force policy): call HA service / write entity
       apply output fail-safe if bridge unhealthy
  4. DIAGNOSTICS
       update metrics (cycle time, overruns, lag, errors)
  5. WAIT until next period (may overrun; record overrun)
```

**Default `scan_period` (proposal):** `100 ms` (10 Hz). Tunable; final default confirmed in SWD-69. Soft real-time only — overruns are recorded, not treated as hard faults unless configured.

## Binding model

A **binding** links one PLC tag to one HA address.

### Common fields

| Field | Required | Description |
|-------|----------|-------------|
| `tag` | yes | PLC symbol / address (runtime-native string, e.g. OpenPLC variable name) |
| `direction` | yes | `input` \| `output` \| `memory_mirror` |
| `entity_id` | yes | HA entity id |
| `attribute` | no | If set, use `state.attributes[attribute]`; else entity `state` |
| `enabled` | no | Default true |

### Input bindings (`direction: input`)

| Field | Required | Description |
|-------|----------|-------------|
| `value_type` | yes | `bool` \| `number` \| `string` |
| `coerce` | no | Rules for mapping HA strings (`"on"`/`"off"`, numeric parse, scale/offset) |
| `unavailable_policy` | no | See [Fail-safe](#fail-safe-and-freshness) |
| `stale_after_s` | no | Seconds after which value is stale if no update; null = only availability |
| `stale_policy` | no | Policy when stale (defaults to `unavailable_policy`) |

### Output bindings (`direction: output`)

| Field | Required | Description |
|-------|----------|-------------|
| `value_type` | yes | `bool` \| `number` \| `string` |
| `write_mode` | yes | `service` \| `entity` |
| `service` | if service | `{ "domain", "service", "data_template" }` mapping tag→service data |
| `idempotent` | no | Default true: skip write if last commanded value equals new value |
| `min_write_interval_ms` | no | Rate limit; default e.g. 0 or 50 |
| `on_bridge_fault` | no | Output fail-safe when HAL cannot talk to HA |

### Memory mirror (`direction: memory_mirror`)

Optional bidirectional or HA→PLC mirror for operator setpoints using `input_number` / `input_boolean` / `input_select` helpers. Exact conflict rules (PLC vs UI wins) are decided in SWD-71; default proposal: **UI write updates PLC memory on next scan; PLC writes back only if `mirror_to_ha: true`.**

## Coercion

| HA state / attribute | `bool` | `number` | `string` |
|----------------------|--------|----------|----------|
| `on` / `off` / `true` / `false` | true/false | 1.0 / 0.0 | as-is |
| numeric string | ≠0 → true | parse float | as-is |
| `unavailable` / `unknown` | policy | policy | policy |
| missing attribute | policy | policy | policy |

Scaling: optional `scale` and `offset` on number paths: `plc = ha * scale + offset` (inputs); inverse on outputs when applicable.

## Fail-safe and freshness

### Input policies

| Policy | Behaviour |
|--------|-----------|
| `hold_last` | Keep last good coerced value (**default** for inputs) |
| `force_zero` | Use `false` / `0` / `""` |
| `force_value` | Use binding’s `safe_value` |
| `fault` | Mark channel faulted; may trigger global output safe mode if configured |

### Output policies (bridge / channel fault)

| Policy | Behaviour |
|--------|-----------|
| `hold_last_command` | Do not send new writes |
| `safe_off` | Force bool outputs off / numbers to `safe_value` (**recommended** for critical actuators when configured) |
| `noop` | Stop writing; leave HA entity as-is |

**Global bridge fault** (WebSocket down, auth failure): apply each output’s `on_bridge_fault` (default proposal: `hold_last_command` unless binding marked `critical: true` → `safe_off`).

## Diagnostics (integration entities)

Expose at least:

| Diagnostic | Type | Meaning |
|------------|------|---------|
| `scan_period_ms` | number | Configured period |
| `last_cycle_ms` | number | Last measured cycle duration |
| `overrun_count` | number | Cycles that exceeded period |
| `bridge_connected` | binary | HA API connectivity |
| `bridge_lag_ms` | number | Approximate sample/command lag |
| `binding_error_count` | number | Coercion / write failures |
| `runtime_state` | sensor | e.g. `running` / `stopped` / `fault` |

These are first-class HA entities so Lovelace can show health without a custom panel.

## Transport

| Path | MVP | Notes |
|------|-----|-------|
| HA WebSocket/REST via Supervisor Core proxy | **Required** | Primary entity I/O |
| Modbus TCP server exposing tags | Optional (post-MVP default) | For FUXA / external tools |

## Out of scope here

- Config UI / YAML schema presentation (SWD-71)  
- OpenPLC-specific address encoding details beyond opaque `tag` strings (SWD-69 may add a mapping appendix)  
- Historian retention and Grafana dashboards (SWD-68)

## Testability notes (for SWD-71/69)

- HAL should accept injectable “HA client” and “clock” seams so unit tests can simulate stale entities and overruns without a live Core.  
- Binding coercion and fail-safe matrices should be pure functions with table-driven tests.
