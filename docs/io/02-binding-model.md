# 02 — Binding model & schema

**Tracker:** [SWD-98](https://marcusknielsen.atlassian.net/browse/SWD-98)  
**Parent:** [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86) · [`docs/PLAN.md`](../PLAN.md)  
**Depends on:** [`docs/io/01-image-quality.md`](01-image-quality.md)

## Purpose

Define how Home Assistant entities **bind** to Soft-PLC image tags: direction, setpoint pattern, unit conversion, uniqueness, and the thin-integration **config shape**. Code: `plcassistant.io.binding` (`Direction`, `Binding`, `BindingTable`).

Bindings sit between field samples and the I/O image. The Add-on still owns the live image; the thin integration owns tag declarations + this binding table (stub in SWD-99).

## Directions (declared, never inferred)

Every binding declares exactly one direction:

| Direction | Scan role |
|-----------|-----------|
| `IN` | Entity → tag at scan start (`apply_in`) |
| `OUT` | Tag → entity at scan end (`apply_out`) |
| `INOUT` | Both: read at start, write at end |

There is **no** silent bidirectional inference from entity type or naming. `INOUT` is an explicit opt-in.

## Setpoint default: split IN + OUT

Setpoints default to **two tags / two bindings**, not one `INOUT`:

| Tag role | Direction | Meaning |
|----------|-----------|---------|
| Request (e.g. `SP_SPEED_REQ`) | `IN` | Operator / HA requested setpoint |
| Active (e.g. `SP_SPEED`) | `OUT` | Value the Soft-PLC is applying / reporting |

Use `INOUT` on a single tag only when a binding **opts in** (rare; e.g. a deliberately bidirectional test entity).

Example config sketch:

```yaml
tags:
  SP_SPEED_REQ: { default: 0.0, unit: pct }
  SP_SPEED: { default: 0.0, unit: pct }
bindings:
  - tag: SP_SPEED_REQ
    entity: input_number.speed_setpoint
    direction: IN
  - tag: SP_SPEED
    entity: sensor.speed_setpoint_active
    direction: OUT
```

## Unit conversion

Conversion happens in the **binding layer** (HA raw ↔ engineering units on the tag).

Simple linear transform (stub / v1):

| Path | Formula |
|------|---------|
| IN (raw → engineering) | `engineering = raw * scale + offset` |
| OUT (engineering → raw) | `raw = (engineering - offset) / scale` |

- `scale` defaults to `1.0`; `offset` defaults to `0.0`.
- Optional `entity_unit` / tag `unit` are documentation hints for humans; they do not drive conversion by themselves in this package.
- Non-numeric conversion and richer unit registries are out of scope here.

## Uniqueness

| Rule | Behaviour |
|------|-----------|
| Multi-IN | One HA entity **may** bind to **many** tags as `IN` |
| Single OUT writer | At most **one** binding that **writes** an entity per entity id |
| Writers | `OUT` and `INOUT` both count as writers |

`BindingTable` construction / `from_config` **rejects** a second writer for the same entity (`ValueError`). Two `IN` bindings to the same entity are allowed.

## Safety opt-in

Safety collapses quality to good **only** for `GOOD` unless the binding sets:

```text
treat_uncertain_as_good: true   # default false
```

When `true`, `UNCERTAIN` may be treated as usable for that binding’s safety consumers (`Binding.usable_for_safety`). Image retention rules from [`01-image-quality.md`](01-image-quality.md) are unchanged: non-`GOOD` samples still do not overwrite last-good on the image.

## Config schema (YAML-oriented dict)

Resolved field names for thin-integration config (and `BindingTable.from_config`):

```yaml
tags:
  LT_TANK:
    default: 0.0
    unit: m          # optional documentation
bindings:
  - tag: LT_TANK
    entity: sensor.tank_level
    direction: IN    # IN | OUT | INOUT
    entity_unit: m   # optional documentation
    scale: 1.0       # optional, default 1.0
    offset: 0.0      # optional, default 0.0
    treat_uncertain_as_good: false  # optional, default false
```

| Key | Required | Notes |
|-----|----------|-------|
| `tags` | yes (may be empty only if unused) | Map tag name → `{ default, unit? }` |
| `tags.<name>.default` | yes | Initial image value (BAD / unavailable until first GOOD) |
| `tags.<name>.unit` | no | Engineering unit hint |
| `bindings` | yes | List of binding objects |
| `bindings[].tag` | yes | Must exist under `tags` |
| `bindings[].entity` | yes | HA entity id string |
| `bindings[].direction` | yes | `IN` / `OUT` / `INOUT` |
| `bindings[].entity_unit` | no | Raw-side unit hint |
| `bindings[].scale` | no | Default `1.0` |
| `bindings[].offset` | no | Default `0.0` |
| `bindings[].treat_uncertain_as_good` | no | Default `false` |

At most one binding per tag. Tag declarations are applied to an `IoImage` via `BindingTable.declare_on(image)`.

## API sketch (`plcassistant.io.binding`)

| Type / op | Role |
|-----------|------|
| `Direction` | `IN` / `OUT` / `INOUT` |
| `Binding` | One tag↔entity link + scale/offset + safety flag |
| `TagDecl` | Declared tag default (+ optional unit) |
| `BindingTable` | Validated collection; uniqueness enforced |
| `from_config(dict)` | Load tags + bindings from the schema above |
| `declare_on(image)` | Declare all tags on an `IoImage` |
| `apply_in(image, samples)` | IN/INOUT only: convert raw→eng, `apply_input` |
| `apply_out(image)` | OUT/INOUT only: eng→raw map `entity → raw` |

`samples` maps entity id → numeric raw value or `(value, QualityStatus, reason?)`. Pure Python; no Home Assistant.

## Non-goals (this package)

- Thin-integration stub / mock entities / scan orchestration — see [`03-thin-integration-stub.md`](03-thin-integration-stub.md) ([SWD-99](https://marcusknielsen.atlassian.net/browse/SWD-99))
- Wedge `*_BAD` retirement — done in SWD-96
- Packaging mock ownership note (SWD-97)
- Real Home Assistant
- Change-detect OUT writes

## References

- Image & quality: [`docs/io/01-image-quality.md`](01-image-quality.md)
- Parent plan: [`docs/PLAN.md`](../PLAN.md) (SWD-86 work package 2)
- Tracker: [SWD-98](https://marcusknielsen.atlassian.net/browse/SWD-98) · [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86)
