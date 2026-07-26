# 07 — Follow-on note

**Tracker:** [SWD-91](https://marcusknielsen.atlassian.net/browse/SWD-91)  
**Parent:** [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) · [`docs/PLAN.md`](../PLAN.md)

## Purpose

Point to work that is **out of SWD-83’s done bar** but required or expected next — so physical validation and later examples are not silently dropped.

## Physical rig (required for overall success)

Mock acceptance satisfies **this Task**. A **physical** recycled tank + reservoir skid is still required for **overall** PLCAssistant wedge success.

| Follow-on item | Intent |
|----------------|--------|
| BOM | Tank, reservoir, VFD+pump, level sensors, flow sensor, plumbing, spill containment |
| Wiring / HA devices | Map real entities to the same tags (`LT_TANK`, `LT_RES`, `FT_INLET`, `CMD_SPEED`, …) via the thin-integration binding table — same path as mock entities ([`08-packaging-sketch.md`](08-packaging-sketch.md), SWD-86) |
| Commissioning | Repeat [`06-mock-acceptance.md`](06-mock-acceptance.md) scenarios on hardware (with safe water procedures) |
| Tuning | Real PID/timing under SWD-85 / model guidance |

Do **not** treat physical as optional product scope — only optional relative to SWD-83 closure. Switching mock entities → field entities must not require an Add-on I/O mode change.

## Later process examples (out of this Task)

| Example | Why later |
|---------|-----------|
| Two-tank | Interacting levels / different cascade story |
| Four-tank with split valve | Adds control-valve actuation beyond pump-only |

Keep v1 packaging and tag patterns from painting into a corner that blocks these (PLAN constraint).

## Sibling Tasks (pointers only)

| Topic | Tracker |
|-------|---------|
| Control semantics / timing | [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85) |
| HA entity binding | [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86) |
| Programming surface | [SWD-82](https://marcusknielsen.atlassian.net/browse/SWD-82) |
| Packaging alternatives | [SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84) |
| Story umbrella | [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81) |

## Explicitly still out

- Home-as-process as a phase goal
- Full SIL / certified safety stack
- Final packaging freeze before SWD-84 (mock ownership in the thin integration is locked for SWD-86; overall packaging shape remains SWD-84)

## Related specs

- Reference process: [`01-reference-process.md`](01-reference-process.md)
- Packaging sketch: [`08-packaging-sketch.md`](08-packaging-sketch.md)
- I/O contracts: [`docs/io/01-image-quality.md`](../io/01-image-quality.md), [`docs/io/02-binding-model.md`](../io/02-binding-model.md)
