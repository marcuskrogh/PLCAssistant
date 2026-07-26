# 03 — Thin-integration stub

**Tracker:** [SWD-99](https://marcusknielsen.atlassian.net/browse/SWD-99)  
**Parent:** [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86) · [`docs/PLAN.md`](../PLAN.md)  
**Depends on:** [`docs/io/01-image-quality.md`](01-image-quality.md) · [`docs/io/02-binding-model.md`](02-binding-model.md)

## Purpose

Working **thin-integration stub** (`plcassistant.io.integration`): owns tag declarations, bindings, unit conversion, and **mock entities**, and refreshes an Add-on-owned [`IoImage`](01-image-quality.md) on scan boundaries. No real Home Assistant.

## Responsibility split

| Concern | Stub (thin integration) | Add-on |
|---------|-------------------------|--------|
| Tag declarations + binding table | **Owns** | Consumes via scan API |
| Unit conversion | **Owns** (via `BindingTable`) | Sees engineering units on tags |
| Mock / sim entity store | **Owns** (`MockEntityStore`) | No special mock path |
| Live I/O image (SoT) | Feeds/sinks only | **Owns** |
| Scan / logic / safety | No | **Owns** |

**Invariant:** mock path ≡ field path. Both use `BindingTable.apply_in` / `apply_out` into the same `IoImage`. The Soft-PLC does not branch on “mock mode”.

Packaging context: [`docs/wedge/08-packaging-sketch.md`](../wedge/08-packaging-sketch.md).

## How the Add-on consumes bindings (resolved)

**This stub:** in-process API on a shared `IoImage`:

1. Integration builds `ThinIntegrationStub` from config (or a `BindingTable`).
2. Add-on (or test) creates `IoImage`; stub `attach(image)` declares tags.
3. Each scan: `scan_inputs(image)` → logic → `scan_outputs(image)`.

**Later / [SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84):** real HA packaging may replace the in-process calls with IPC (entity state / services) while keeping the same binding-fed image path. This package does not invent that IPC.

## Mock entities

`MockEntityStore` is an in-memory map `entity_id → (value, quality status, reason)`.

| Op | Behaviour |
|----|-----------|
| `set(id, value, status=GOOD, reason=None)` | Write / replace for tests or mock drivers |
| `get(id)` | Stored sample, or **`BAD` / `unavailable`** if missing |
| `has` / `remove` / `clear` | Test helpers |

Missing entities are treated like absent field samples: scan IN applies `BAD` + `unavailable` so the image keeps **last-good** or **default**.

## Scan API

| Method | When | Effect |
|--------|------|--------|
| `attach(image?)` | Setup | `BindingTable.declare_on`; creates `IoImage` if omitted |
| `scan_inputs(image)` | Scan start | For each IN/INOUT: read store → `apply_in` (units + quality) |
| `scan_outputs(image)` | Scan end | `apply_out` → write **logic-written** OUTs into store (skip never-written; quality from image tag) |
| `run_scan(image, logic)` | Tests | `scan_inputs` → `logic(image)` → `scan_outputs` |

Uniqueness (multi-IN / single OUT writer) is enforced by `BindingTable` at construction — the stub does not re-validate.

## Example

```python
from plcassistant.io import IoImage, ThinIntegrationStub

config = {
    "tags": {
        "LT_TANK": {"default": 0.0, "unit": "m"},
        "CMD_SPEED": {"default": 0.0, "unit": "pct"},
    },
    "bindings": [
        {
            "tag": "LT_TANK",
            "entity": "sensor.tank_level",
            "direction": "IN",
            "scale": 0.01,
            "offset": 0.0,
        },
        {
            "tag": "CMD_SPEED",
            "entity": "number.cmd_speed",
            "direction": "OUT",
        },
    ],
}

stub = ThinIntegrationStub(config)
image = stub.attach()  # or stub.attach(IoImage())

stub.entities.set("sensor.tank_level", 25.0)  # raw % → 0.25 m


def logic(img: IoImage) -> None:
    level = img.get_value("LT_TANK")
    img.set_output("CMD_SPEED", 40.0 if level > 0.2 else 0.0)


stub.run_scan(image, logic)
assert stub.entities.get("number.cmd_speed").value == 40.0
```

## Non-goals

- Real Home Assistant / `homeassistant` package
- HA IPC / Add-on packaging freeze ([SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84))
- Wedge plant model import (keep `plcassistant.wedge` separate)
- Change-detect OUT writes

## References

- Image & quality: [`docs/io/01-image-quality.md`](01-image-quality.md)
- Binding model: [`docs/io/02-binding-model.md`](02-binding-model.md)
- Packaging: [`docs/wedge/08-packaging-sketch.md`](../wedge/08-packaging-sketch.md)
- Parent plan: [`docs/PLAN.md`](../PLAN.md) (SWD-86 work package 5)
- Tracker: [SWD-99](https://marcusknielsen.atlassian.net/browse/SWD-99) · [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86)
