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
- SWD-181 define extended the route with a small **scheduling editor** Task (SWD-191); keep Tasks small and well-defined.

## Route
| Order | Task | Type | Blocked by | Status | Issue |
|-------|------|------|------------|--------|-------|
| 1 | Research: industrial PLC program organization & engineering UI capabilities | research | — | Done | [SWD-179](https://marcusknielsen.atlassian.net/browse/SWD-179) |
| 2 | Soft-PLC program organization model (tasks → programs → instances) | define→ship | SWD-179 | Done (App 0.1.32, PR #76) | [SWD-182](https://marcusknielsen.atlassian.net/browse/SWD-182) |
| 3 | App engineering surface (Program cards + Diagram/Log/Settings) | define→ship | SWD-182 | Done (App 0.1.33, PR #77) | [SWD-181](https://marcusknielsen.atlassian.net/browse/SWD-181) |
| 4 | Task/Program scheduling editor | define→ship | SWD-181 | Done (App 0.1.34, PR #78) | [SWD-191](https://marcusknielsen.atlassian.net/browse/SWD-191) |
| 5 | Library inspectability + generic PID | define→ship | SWD-182 | In Review (App 0.1.35) | [SWD-180](https://marcusknielsen.atlassian.net/browse/SWD-180) |
| 6 | Define integration multi-datablock tag mapping UI (mirrors Soft-PLC multi-model) | define | SWD-182 | To Do | [SWD-184](https://marcusknielsen.atlassian.net/browse/SWD-184) |
| 7 | Define online / runtime visibility (loaded vs running, live values) | define | SWD-181 | To Do | [SWD-183](https://marcusknielsen.atlassian.net/browse/SWD-183) |

## Cleared so far
- [Research: industrial PLC program/UI capabilities](https://marcusknielsen.atlassian.net/browse/SWD-179) — multi-axis brief in `docs/RESEARCH.md`
- [Soft-PLC program organization model](https://marcusknielsen.atlassian.net/browse/SWD-182) — SoftPlcProject/Task/ProjectLoader; App 0.1.32; PR #76
- [App engineering surface](https://marcusknielsen.atlassian.net/browse/SWD-181) — Program cards + Diagram/Log/Settings; App 0.1.33; PR #77
- [Task/Program scheduling editor](https://marcusknielsen.atlassian.net/browse/SWD-191) — Save/Apply schedule; App 0.1.34; PR #78
- [Library inspectability + generic PID](https://marcusknielsen.atlassian.net/browse/SWD-180) — shipped PID, library editor, equation-driven instances; App 0.1.35; branch `cursor/swd-180-library-pid-a52c`

## Not yet specified
- How integration “datablocks” bind to Soft-PLC programs (1:1 vs many tags per program) — SWD-184
- Depth of online force/write vs monitor-only for v1 — SWD-183
- Whether Python FBD remains the only authoring language (LD/ST deferred?)

## Out of scope
- Full clone of TIA Portal / Studio 5000 / TwinCAT product surfaces
- SIL / safety-engineering toolchain and certified force workflows
- Physical plant / field I/O commissioning
- Replacing Lovelace HMI with Soft-PLC-native SCADA
- Re-opening Soft-PLC plant ODEs (mock stays integration-owned)

## Tracker
- Provider: jira
- Story (map): [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)
- Tasks: [SWD-179](https://marcusknielsen.atlassian.net/browse/SWD-179) (Done), [SWD-182](https://marcusknielsen.atlassian.net/browse/SWD-182) (Done), [SWD-181](https://marcusknielsen.atlassian.net/browse/SWD-181) (Done), [SWD-191](https://marcusknielsen.atlassian.net/browse/SWD-191) (Done), [SWD-180](https://marcusknielsen.atlassian.net/browse/SWD-180), [SWD-184](https://marcusknielsen.atlassian.net/browse/SWD-184), [SWD-183](https://marcusknielsen.atlassian.net/browse/SWD-183)

## Next
`/review-fix SWD-180` — Review and auto-fix until clean
(also open: SWD-184, SWD-183)
