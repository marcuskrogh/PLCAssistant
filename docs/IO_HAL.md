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
  0. BRIDGE CHECK
       if not bridge_connected: skip INPUT sampling writes to runtime;
         apply OUTPUT on_bridge_fault policies only; update diagnostics; WAIT
  1. INPUT PHASE
       for each input binding:
         read entity (and optional attribute) from HA
         coerce → PLC tag type
         apply freshness / unavailable / cold-start policy → effective input value
         write into runtime input image
       for each memory_mirror binding (HA → PLC direction this scan):
         sample HA helper → PLC memory tag (same coercion / freshness rules)
  2. LOGIC PHASE
       SoftPlcRuntime.execute_cycle()   # MVP adapter: OpenPLC; same port for fallback runtime
  3. OUTPUT PHASE
       for each output binding:
         read PLC output tag
         if changed (idempotent skip) and past min_write_interval_ms:
           call HA service / write entity
       for each memory_mirror binding with mirror_to_ha: true:
         write PLC memory → HA helper when changed
  4. DIAGNOSTICS
       update metrics (cycle time, overruns, lag, errors, stale counts)
  5. WAIT until next period (may overrun; record overrun)
```

**Scan ownership (MVP):** the **I/O HAL owns `scan_period`** and calls `SoftPlcRuntime.execute_cycle()` once per period. Do not run a second autonomous OpenPLC cyclic I/O loop against HA bindings. Embedding HA I/O inside an OpenPLC plugin is **not** MVP — only via explicit ADR amendment.

**Default `scan_period` (proposal):** `100 ms` (10 Hz). Tunable via integration options (pushed to addon); shipping default confirmed in SWD-69. Soft real-time only — overruns are recorded, not treated as hard faults unless configured.

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
| `scale` / `offset` | no | Number path: `plc = ha * scale + offset` (default 1 / 0) |
| `unavailable_policy` | no | See [Fail-safe](#fail-safe-and-freshness); default `hold_last` |
| `stale_after_s` | no | Seconds after which value is stale if no update; null = only availability |
| `stale_policy` | no | Policy when stale (defaults to `unavailable_policy`) |
| `safe_value` | if policy `force_value` | Typed value used by `force_value` / cold-start fallback |
| `cold_start_policy` | no | Before any good sample: `force_zero` \| `force_value` \| `fault` (default `force_zero`) |

### Output bindings (`direction: output`)

| Field | Required | Description |
|-------|----------|-------------|
| `value_type` | yes | `bool` \| `number` \| `string` |
| `write_mode` | yes | `service` \| `entity` |
| `service` | if service | `{ "domain", "service", "data_template" }` mapping tag→service data |
| `idempotent` | no | Default true: skip write if last commanded value equals new value |
| `min_write_interval_ms` | no | Rate limit; **default `0`** |
| `on_bridge_fault` | no | Output fail-safe when HAL cannot talk to HA; default `hold_last_command` |
| `safe_value` | if `safe_off` needs non-bool or custom | Value forced on `safe_off` (bool defaults to `false`) |
| `critical` | no | If true, global bridge fault defaults this binding to `safe_off` |

### Memory mirror (`direction: memory_mirror`)

Optional HA↔PLC mirror for operator setpoints using `input_number` / `input_boolean` / `input_select` helpers.

| Field | Required | Description |
|-------|----------|-------------|
| `value_type` | yes | `bool` \| `number` \| `string` |
| `mirror_to_ha` | no | Default **false**: HA→PLC each scan; if true, also PLC→HA when PLC memory changes |
| (plus input freshness fields) | no | Same unavailable/stale/cold-start rules as inputs for the HA→PLC leg |

Exact conflict rules (PLC vs UI wins under simultaneous edits) are decided in SWD-71; default proposal: **UI write updates PLC memory on next scan; PLC writes back only if `mirror_to_ha: true`.**

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
| `hold_last` | Keep last good coerced value (**default** for inputs **after** first good sample) |
| `force_zero` | Use `false` / `0` / `""` |
| `force_value` | Use binding’s `safe_value` (required when this policy is selected) |
| `fault` | Mark channel faulted; may trigger global output safe mode if configured |

**Cold start:** If `hold_last` is selected but no good sample has ever been stored (boot, new binding, never-available), apply `cold_start_policy` (default **`force_zero`**) until the first successful coerce. Do not leave the PLC input image undefined.

### Output policies (bridge / channel fault)

| Policy | Behaviour |
|--------|-----------|
| `hold_last_command` | Do not send new writes |
| `safe_off` | Force bool outputs off / numbers/strings to `safe_value` (**recommended** for critical actuators when configured) |
| `noop` | Stop writing; leave HA entity as-is |

**Global bridge fault** (WebSocket down, auth failure): **do not** attempt normal OUTPUT writes. Apply each output’s `on_bridge_fault` only (default `hold_last_command`; if `critical: true` → `safe_off`).

## Diagnostics (integration entities)

Expose at least:

| Diagnostic | Type | Meaning |
|------------|------|---------|
| `scan_period_ms` | number | Configured period |
| `last_cycle_ms` | number | Last measured cycle duration |
| `overrun_count` | number | Cycles that exceeded period |
| `bridge_connected` | binary | HA API connectivity |
| `bridge_lag_ms` | number | Approximate sample/command lag (latency) |
| `stale_binding_count` | number | Bindings currently in stale policy |
| `fail_safe_active` | binary | True while any output `on_bridge_fault` / safe mode is applied |
| `binding_error_count` | number | Coercion / write failures |
| `runtime_state` | sensor | e.g. `running` / `stopped` / `fault` |

These are first-class HA entities so Lovelace can show health without a custom panel.

**Phase ownership:** SWD-69 emits metrics via addon status API; SWD-71 (or SWD-67 if deferred) exposes the named diagnostic entities in the HACS integration. Not “later” without an owner.

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
