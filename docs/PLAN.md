# Implementation plan: Integration Datablock tag mapping UI (SWD-184)

## Summary
- Introduce named **Datablocks** that group Soft-PLC tags and HA entity bindings.
- Engineers define mappings in a real **HA integration configuration panel** (where signals live) — not in the Soft-PLC App.
- Soft-PLC **Programs declare Datablock id(s)** they can access; Soft-PLC only sees the union of those tags.
- Rebuild the **example system** to fit the new contract (beta — not constrained by the old flat wedge binding table).
- Acceptance: **unit**, **integration**, **system** on the mapping setup path end-to-end.

## Scope

### In
- Datablock model: id, description, tag declarations, bindings (direction, entity, scale, offset, … per existing binding rules)
- Hybrid use: a Program may reference **one or more** Datablock ids
- Soft-PLC tag visibility = tags from Datablocks the Program has access to
- Real HA integration **configuration panel** with necessary CRUD: Datablocks, tags/bindings, Program↔Datablock assignment
- Persist Datablocks in the integration (config entry / integration-owned store)
- Apply/reload into the MQTT / I/O image path used by Soft-PLC
- Rebuild demo: fully defined example Datablock(s) + matching Soft-PLC Program / entities as needed for the contract
- Retire or replace the flat-only `default_wedge_binding_config` demo path
- Tests: unit + integration + system for setup → Soft-PLC sees correct tags

### Out
- Soft-PLC App as the mapping editor (App remains Programs / Tasks / Library / Diagram)
- Online live values / force / deep runtime visibility → [SWD-183](https://marcusknielsen.atlassian.net/browse/SWD-183)
- Field commissioning, SIL tooling, certified force workflows
- Requiring Soft-PLC App to edit Program↔Datablock assignment (HA owns assignment; Soft-PLC consumes)

## Decisions
| Topic | Decision |
|-------|----------|
| Shape | Hybrid Datablocks; Program may use ≥1 DB |
| Ownership | HA integration defines mappings |
| Product term | **Datablock** (industrial) |
| Soft-PLC view | Tags only from Datablocks the Program has access to |
| Access rule | Each Program declares Datablock id(s) |
| HA UX | Real configuration panel in the integration (not Options-only forms) |
| Soft-PLC App | Does not own mapping edit; may later show read-only access if useful |
| Example | Redo example system to fit new contract (breaking changes OK if documented) |
| Panel tech | Implement may choose HA custom panel / sidebar panel within “real config panel” |

## Constraints
- Soft-PLC remains mock-unaware; plant dynamics stay integration-owned
- Dual trees synced when shipping App/package changes
- Prefer extending `docs/io/02-binding-model.md` + `BindingTable` rather than a parallel binding language
- Preserve MQTT image path semantics (IN/OUT/quality) unless the new contract explicitly replaces them
- Keep Tasks small; panel UX should be mobile-usable where practical

## Inputs (supportive — not substitutes for decisions above)
- `docs/ROADMAP.md` route order 6; Story [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)
- `docs/io/02-binding-model.md`, `docs/io/03-thin-integration-stub.md`
- Soft-PLC multi-program model (SWD-182) and App surface (SWD-181/191/180)
- Existing `default_wedge_binding_config` / integration mock bindings as material to **replace**, not freeze

## Acceptance criteria
- [x] Engineers can create/edit/delete a Datablock and its tag/binding rows in the HA configuration panel
- [x] Program declares Datablock access; Soft-PLC / image path only exposes tags from those Datablocks
- [x] Example system ships as a fully defined Datablock + matching Soft-PLC Program (and entities as needed)
- [x] Old flat-only demo binding path is replaced or clearly retired with a documented migration note
- [x] Changing mappings in HA applies into the live MQTT/image path without Soft-PLC needing to own the editor
- [x] **Unit** tests: Datablock schema, Program access → tag set, uniqueness/validation rules
- [x] **Integration** tests: HA panel/API persist + reload; Soft-PLC consumes accessible tags
- [x] **System** test: end-to-end setup path — define Datablock in integration → Soft-PLC Program with access runs with correct tags

## Work packages
1. **Datablock model + schema** — [SWD-209](https://marcusknielsen.atlassian.net/browse/SWD-209)
2. **Program ↔ Datablock access + tag visibility** — [SWD-208](https://marcusknielsen.atlassian.net/browse/SWD-208)
3. **HA configuration panel** — [SWD-210](https://marcusknielsen.atlassian.net/browse/SWD-210)
4. **Rebuild example** — [SWD-207](https://marcusknielsen.atlassian.net/browse/SWD-207)
5. **Persistence + apply/reload** — [SWD-212](https://marcusknielsen.atlassian.net/browse/SWD-212)
6. **Tests** — [SWD-211](https://marcusknielsen.atlassian.net/browse/SWD-211)

## Open items
- Exact HA panel host API (custom panel vs sidebar) — choose in implement within Decision “real config panel”
- Whether Soft-PLC App shows read-only Datablock access on Program Settings — optional, not required for Done

## Tracker
- Provider: jira
- Story: [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)
- Task: [SWD-184](https://marcusknielsen.atlassian.net/browse/SWD-184)
- Sub-tasks: SWD-209, SWD-208, SWD-210, SWD-207, SWD-212, SWD-211
- Branch: `cursor/swd-184-datablock-mapping-a52c`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/80
App: 0.1.36

## Next
`/review-fix SWD-184` — Review and auto-fix until clean
