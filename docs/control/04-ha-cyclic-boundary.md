# 04 — HA ↔ cyclic boundary

**Tracker:** [SWD-101](https://marcusknielsen.atlassian.net/browse/SWD-101)  
**Parent:** [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Clarify how Home Assistant’s **event-driven** world meets the Soft-PLC
**cyclic scan** without making HA automations the control engine.

## Layering

| Layer | Role |
|-------|------|
| Home Assistant | Entity state changes, services, dashboards — **asynchronous** |
| Thin integration ([`docs/io/`](../io/01-image-quality.md)) | Bindings, unit conversion, mock/field sample buffer |
| Soft-PLC scan ([`01-scan-scheduler.md`](01-scan-scheduler.md)) | Owns the **scan clock**; IN → safety → control → OUT |

## Contract

1. HA events **update a sample buffer** (entity store / binding inputs).
2. They **do not** execute cascade or safety logic mid-scan.
3. Each scan **samples** the buffer into the frozen I/O image at IN.
4. OUT flushes PLC-paced commands every scan (SWD-86 — no change-detect yet).
5. Stale / missing samples become `UNCERTAIN` / `BAD` via the quality model —
   not ad-hoc event handlers inside FB code.

```text
  HA entity events ──► sample buffer ──► IN (image) ──► SAFETY/CONTROL ──► OUT ──► HA
                         (async)           (scan)           (scan)         (scan)
```

## Mental model

Prefer **IEC 61131-shaped cyclic** core. IEC 61499 event FBs are not the primary
product metaphor. Behavior trees / high-level authoring (SWD-82) may sit **atop**
the same scan contract later.

## Related

- Image + quality: [`docs/io/01-image-quality.md`](../io/01-image-quality.md)
- Thin integration scan API: [`docs/io/03-thin-integration-stub.md`](../io/03-thin-integration-stub.md)
- Packaging (Add-on owns live image): [`docs/wedge/08-packaging-sketch.md`](../wedge/08-packaging-sketch.md)
