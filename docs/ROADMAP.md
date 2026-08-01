# Roadmap: Industrial-parity Soft-PLC programming surface

## Destination
Soft-PLC App and thin HA integration expose an industrial-style engineering surface: multi-program/task organization with matching multi-datablock tag mappings, inspectable block instances (including equations), a single generic PID library mapped into loops by instance, online visibility of what is defined vs loaded/running, and acceptance proven at unit, integration, and system levels.

## Notes
- Trigger: after SWD-173 control recovered, App still showed empty canvas / empty builtin equations; integration still lacks a proper tag/datablock mapping UI.
- Evidence: [docs/RESEARCH.md](RESEARCH.md) ([SWD-179](https://marcusknielsen.atlassian.net/browse/SWD-179)) — IEC hierarchy, vendor UIs, generic PID practice. Supportive only; does not lock product choices.
- Route order: **full Soft-PLC program organization model first**, then App surface and library, then **integration multi-datablock / tag mapping UI** (sequential — mirrors Soft-PLC multi-model), then online visibility.
- Prefer industrial metaphors from the brief — exact metaphor is a define probe on SWD-182.
- Keep Soft-PLC mock-unaware; plant dynamics stay integration-owned (SWD-145 lineage).
- **Testing bar (this initiative):** every define → implement slice must ship **unit**, **integration**, and **system**-level tests that exercise the setup path.

## Route
| Order | Task | Type | Blocked by | Status | Issue |
|-------|------|------|------------|--------|-------|
| 1 | Research: industrial PLC program organization & engineering UI capabilities | research | — | Done | [SWD-179](https://marcusknielsen.atlassian.net/browse/SWD-179) |
| 2 | Define Soft-PLC program organization model (tasks → programs → instances) | define | SWD-179 | Defined — `/implement` | [SWD-182](https://marcusknielsen.atlassian.net/browse/SWD-182) |
| 3 | Define App engineering surface (navigator + defined/active programs on canvas) | define | SWD-182 | To Do | [SWD-181](https://marcusknielsen.atlassian.net/browse/SWD-181) |
| 4 | Define library inspectability + generic PID (replace opaque level_pi/flow_pi) | define | SWD-182 | To Do | [SWD-180](https://marcusknielsen.atlassian.net/browse/SWD-180) |
| 5 | Define integration multi-datablock tag mapping UI (mirrors Soft-PLC multi-model) | define | SWD-182 | To Do | [SWD-184](https://marcusknielsen.atlassian.net/browse/SWD-184) |
| 6 | Define online / runtime visibility (loaded vs running, live values) | define | SWD-181 | To Do | [SWD-183](https://marcusknielsen.atlassian.net/browse/SWD-183) |

## Cleared so far
- [Research: industrial PLC program/UI capabilities](https://marcusknielsen.atlassian.net/browse/SWD-179) — multi-axis brief in `docs/RESEARCH.md`

## Not yet specified
- How integration “datablocks” bind to Soft-PLC programs (1:1 vs many tags per program) — SWD-184
- Depth of online force/write vs monitor-only for v1 — SWD-183
- Whether Python FBD remains the only authoring language (LD/ST deferred?)
- Migration path for existing wedge cascade instances onto generic PID — SWD-180
- Exact JSON/YAML field names for Soft-PLC project (implementer default OK if documented) — SWD-182

## Out of scope
- Full clone of TIA Portal / Studio 5000 / TwinCAT product surfaces
- SIL / safety-engineering toolchain and certified force workflows
- Physical plant / field I/O commissioning
- Replacing Lovelace HMI with Soft-PLC-native SCADA
- Re-opening Soft-PLC plant ODEs (mock stays integration-owned)

## Tracker
- Provider: jira
- Story (map): [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)
- Tasks: [SWD-179](https://marcusknielsen.atlassian.net/browse/SWD-179) (Done), [SWD-182](https://marcusknielsen.atlassian.net/browse/SWD-182), [SWD-181](https://marcusknielsen.atlassian.net/browse/SWD-181), [SWD-180](https://marcusknielsen.atlassian.net/browse/SWD-180), [SWD-184](https://marcusknielsen.atlassian.net/browse/SWD-184), [SWD-183](https://marcusknielsen.atlassian.net/browse/SWD-183)

## Next
`/implement SWD-182` — Build Soft-PLC program organization model per `docs/PLAN.md`
