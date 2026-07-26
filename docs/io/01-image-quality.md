# 01 — I/O image & quality contract

**Tracker:** [SWD-95](https://marcusknielsen.atlassian.net/browse/SWD-95)  
**Parent:** [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Define the Soft-PLC **scan-cycle I/O image** and per-tag **quality** model used by the Add-on at runtime. HA entity bindings (direction, units, mock) feed and sink this image in later packages; this document owns **image semantics, quality, last-good / defaults, and IN/OUT scan timing**.

Code: `plcassistant.io` (`QualityStatus`, `ReasonCode`, `TagQuality`, `IoImage`).

## Image role

| Role | Owner |
|------|--------|
| Live scan-cycle image | Add-on (Soft-PLC runtime) |
| Tag declarations, bindings, unit conversion, mock entities | Thin HA integration (later packages) |

The Soft-PLC keeps one **I/O image** for the scan. Bindings apply field samples into the image and flush outputs from it. Logic and safety read/write **tags** on the image — never HA entities directly.

There are **no** separate `*_BAD` tags. Quality lives on each tag.

## Scan-synchronous refresh

Refresh is **scan-synchronous** and happens **every scan**:

| Boundary | Action |
|----------|--------|
| **Scan start (IN)** | Bindings (or tests) call `apply_input` for each input tag: value + quality + reason |
| **Scan body** | Logic / safety read tag values and quality; write outputs via `set_output` |
| **Scan end (OUT)** | Runtime takes a **snapshot** of output values and flushes them to the field (every scan; change-detect deferred) |

Until bindings exist, callers exercise the same API with in-memory samples. The Add-on scan path stays binding-agnostic: mock and field use the same image API.

```text
  ┌─────────────────────────────────────────────┐
  │  scan N                                     │
  │  1. IN:  apply_input(...) for each IN tag   │
  │  2.     logic / safety on image values      │
  │  3. OUT: snapshot() → flush writers         │
  └─────────────────────────────────────────────┘
```

## Quality model

Each tag carries a status and an optional reason:

| Status | Meaning |
|--------|---------|
| `GOOD` | Sample is trustworthy for control and safety |
| `UNCERTAIN` | Sample may be usable for display / soft decisions; **not** good for safety |
| `BAD` | Sample must not drive control or safety as a live PV |

### Reason codes

Minimal closed set (resolves PLAN open item):

| Code | When |
|------|------|
| `unavailable` | No successful sample yet, or source not present |
| `unknown` | Failure without a more specific classification |
| `stale` | Sample older than allowed / not refreshed this scan |
| `fault` | Explicit sensor / channel / conversion fault |

- When status is `GOOD`, reason is omitted (`None`).
- When status is `UNCERTAIN` or `BAD`, a reason **must** be set.

### Safety collapse

Safety treats **only `GOOD` as good**. Helpers:

- `is_good(quality)` → `True` iff status is `GOOD`
- `collapse_quality(quality)` → same boolean collapse for trip / LOS checks

Binding-level opt-out (treat `UNCERTAIN` as usable) is **out of scope** here and comes with the binding model.

## Value retention rules

| Condition | Tag value used by logic | Quality on tag |
|-----------|-------------------------|----------------|
| Before first successful `GOOD` sample | Configured **default** | `BAD` + `unavailable` |
| Latest apply is `GOOD` | New sample value; becomes **last good** | `GOOD` |
| Latest apply is `UNCERTAIN` or `BAD` | **Last good** value (unchanged); if none yet, **default** | New status + reason |

Non-`GOOD` updates **never** overwrite the retained last-good (or default) value with the bad sample. The bad / uncertain payload may be discarded for logic; only quality/reason advance.

## Tag declaration

Tags are declared on the image with a name and default before use:

```text
declare(name, default=…)
→ value = default, quality = BAD / unavailable, last_good = none
```

Direction (`IN` / `OUT` / `INOUT`), uniqueness, and HA entity mapping belong to the **binding** package (SWD-98), not this contract.

## API sketch (`plcassistant.io`)

| Operation | Scan phase | Behaviour |
|-----------|------------|-----------|
| `declare(name, default=…)` | setup | Create slot; initial BAD + default |
| `apply_input(name, value, status, reason=…)` | start (IN) | Apply sample per retention rules |
| `get_value` / `get_quality` / `get` | body | Read for logic / safety |
| `set_output(name, value)` | body | Logic writes CV / command |
| `snapshot()` / `snapshot_outputs()` | end (OUT) | Capture values for flush |

Outputs written by logic are trusted (`GOOD`) unless a later package defines otherwise.

## Non-goals (this package)

- HA entity bindings, YAML schema, unit conversion (SWD-98 / SWD-99)
- Wedge `*_BAD` retirement in skid specs (SWD-96)
- Change-detect OUT writes
- Real Home Assistant

## References

- Parent plan: [`docs/PLAN.md`](../PLAN.md) (SWD-86 work package 1)
- Prior wedge I/O names (still authoritative for skid roles until SWD-96): [`docs/wedge/02-io-hmi-contract.md`](../wedge/02-io-hmi-contract.md)
- Tracker Task: [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86)
