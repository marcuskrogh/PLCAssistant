# Lab / hobby wedge — gravity-drained tank skid

Specification package for **SWD-83** (Story [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81)).

Primary example: one process tank + reservoir, recycled water loop, pump-only cascade control, and an illustrative safety layer. **Mock first**; physical rig is the required follow-on for overall success.

**Mock layers:** skid **plant-model** physics live in wedge core (`MockProcess`, SWD-83) for control-dev and offline tests; **HA entity mock/sim** for the Soft-PLC image is owned by the thin integration (SWD-86) — see [`08-packaging-sketch.md`](08-packaging-sketch.md).

Parent plan: [`docs/PLAN.md`](../PLAN.md)

## Spec index

| # | Doc | Sub-task | Purpose |
|---|-----|----------|---------|
| 01 | [Reference process](01-reference-process.md) | [SWD-88](https://marcusknielsen.atlassian.net/browse/SWD-88) | P&ID-level narrative, boundaries, recycled loop |
| 02 | [I/O & HMI contract](02-io-hmi-contract.md) | [SWD-87](https://marcusknielsen.atlassian.net/browse/SWD-87) | Signals, setpoints, start/stop/reset, displays |
| 03 | [Control story](03-control-story.md) | [SWD-92](https://marcusknielsen.atlassian.net/browse/SWD-92) | Cascade level → flow → pump speed; modes |
| 04 | [Safety story](04-safety-story.md) | [SWD-93](https://marcusknielsen.atlassian.net/browse/SWD-93) | Trips, latch/reset, Start permissives |
| 05 | [Mock process](05-mock-process.md) | [SWD-90](https://marcusknielsen.atlassian.net/browse/SWD-90) | Plant-model physics + first-class mock capability (entity mock → thin integration) |
| 06 | [Mock acceptance](06-mock-acceptance.md) | [SWD-89](https://marcusknielsen.atlassian.net/browse/SWD-89) | Runnable checklist for cascade + safety |
| 07 | [Follow-on](07-follow-on.md) | [SWD-91](https://marcusknielsen.atlassian.net/browse/SWD-91) | Physical rig + later multi-tank pointers |
| 08 | [Packaging sketch](08-packaging-sketch.md) | [SWD-94](https://marcusknielsen.atlassian.net/browse/SWD-94) · [SWD-97](https://marcusknielsen.atlassian.net/browse/SWD-97) | HA Add-on (live image) + thin integration (bindings + mock entities) |

## Naming conventions (shared)

Logical tag names are stable across all wedge docs. HA entity IDs are binding-time; tags are the PLC-facing contract.

| Tag | Role | Typical unit |
|-----|------|--------------|
| `LT_TANK` | Process tank level | m (or % of span) |
| `LT_RES` | Reservoir level | m (or % of span) |
| `FT_INLET` | Inlet volumetric flow | L/min |
| `SC_PUMP` | Pump speed feedback (optional) | % |
| `CMD_SPEED` | Pump speed command | % |
| `SP_LEVEL` | Tank level setpoint | m (or %) |
| `SP_FLOW` | Flow setpoint (from level loop or operator override) | L/min |
| `HMI_START` | Operator start request | bool pulse / command |
| `HMI_STOP` | Operator stop request | bool pulse / command |
| `HMI_RESET` | Operator trip reset | bool pulse / command |
| `PERM_OK` | Aggregated start permissive | bool |
| `TRIP_ACTIVE` | Any latched safety trip | bool |
| `MODE` | Operating mode enum | see control story |

## Out of this package

- Home-as-process
- Two-tank and four-tank / split-valve examples
- Physical BOM/wiring (follow-on)
- Full SIL / certified safety PLC
- Final packaging freeze (see SWD-84)
