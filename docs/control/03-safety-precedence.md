# 03 — Safety precedence in the scan

**Tracker:** [SWD-104](https://marcusknielsen.atlassian.net/browse/SWD-104)  
**Parent:** [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

State how **safety** interacts with continuous control inside one scan cycle.
Product trip behaviors remain those in [`docs/wedge/04-safety-story.md`](../wedge/04-safety-story.md);
this document locks **ordering and CV force-zero**.

## Same-scan rule

```text
IN → SAFETY → CONTROL → OUT
```

1. **SAFETY** evaluates trips / Stop / Reset / Start and publishes `pump_permit`.
2. **CONTROL** runs only with that permit; integrators disabled when not permitted.
3. **OUT / actuator path** applies `CMD_SPEED = 0` whenever `pump_permit` is false,
   even if a controller object still holds internal state.

Consequence: a trip asserted on scan N forces safe CV on scan N (no one-scan lag
of “control wrote then safety noticed”).

## Mode vs FB enable

| Mode | `pump_permit` | Continuous FBs |
|------|---------------|----------------|
| `STOP` | false | Disabled; hold last SPs; CV = 0 |
| `RUNNING` | true | Enabled |
| `TRIPPED` | false | Disabled; CV = 0; latch until Reset |

## Integrators on trip / stop

- Entering non-permit: cascade `reset_integrators()` (via `step(..., running=False)`).
- Leaving non-permit via Start: bumpless re-init ([`02-fb-pid.md`](02-fb-pid.md)).

## Quality / LOS

Unchanged: only `GOOD` counts as good for trips and control PVs (`is_good`).
Non-GOOD on required PVs latches LOS and clears permit the same scan.

## Ambition ceiling

This is **illustrative middle-ground** safety — not SIL, dual-channel, or certified
safety PLC. Do not claim otherwise in docs or UX.
