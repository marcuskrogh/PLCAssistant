# Implementation plan: HA entities as PLC I/O (SWD-86)

## Summary
- Soft-PLC keeps a **scan-cycle I/O image**; HA entities are the field that **feed/sink** that image.
- Refresh is **scan-synchronous**: IN at scan start, OUT at scan end (**every scan**).
- Each tag carries **quality** (`GOOD` / `UNCERTAIN` / `BAD` + reason); **no** separate `*_BAD` tags.
- **Thin HA integration** owns tag declarations, bindings, unit conversion, and **mock/sim entities**; **Add-on** owns the live image at runtime and always sees the same binding path.

## Scope
**In**
- I/O image + quality model and scan refresh rules
- Strictly directional bindings: `IN` / `OUT` / `INOUT` (declared, not inferred)
- Setpoint default: split **IN** (request) + **OUT** (active); `INOUT` only when a binding opts in
- Unit conversion in the binding layer
- Binding uniqueness: one HA entity may map to **many** tags; **at most one OUT** writer per entity
- Last-good retention when quality ≠ `GOOD`; before first sample: `BAD` / `unavailable` + **default value**
- Safety treats only `GOOD` as good unless a binding opts otherwise
- Mock/sim in the **thin integration** (entities mocked internally); Add-on has no special mock-process path
- Revise packaging notes that put mock inside the Add-on
- Working **thin-integration stub** + automated contract/unit tests (mocked HA; no real HA instance)
- Align wedge I/O contract: drop `*_BAD` tags in favor of per-tag quality

**Out**
- Real Home Assistant instance testing
- Final packaging freeze (SWD-84)
- Control / PID semantics (SWD-85)
- Programming authoring UX (SWD-82)
- Change-detect OUT writes (defer; write every scan for now)
- Physical rig commissioning

## Decisions
- Image + scan-synchronous refresh
- Quality trio + reasons; collapse to good/bad for safety
- Directional bindings; setpoint split by default; `INOUT` opt-in only
- Integration owns declarations / bindings / mock; Add-on owns live image
- Unit conversion at binding
- OUT every scan; multi-IN OK; single OUT writer per entity
- Initial: `BAD` + default value (no last-good yet)

## Constraints
- Must not break skid tag *names* / roles from SWD-83 except retiring `*_BAD`
- Add-on scan path must stay binding-agnostic (same for mock and field)
- No silent bidirectional bindings
- Prior SWD-83 wedge specs remain authoritative for process/control/safety behavior; this Task owns the entity↔tag I/O layer

## Acceptance criteria
- Documented contract covers image, quality, directions, units, uniqueness, initial/last-good, mock-in-integration
- Packaging sketch updated for mock ownership (integration, not Add-on process engine)
- Stub can declare tags, bind IN/OUT/INOUT, convert units, apply mock entity values into an image on a scan boundary
- Tests cover: sync refresh, quality transitions, last-good, defaults, direction enforcement, multi-IN / single-OUT, unit conversion, mock path ≡ field path into the Add-on image
- No real HA required for green tests

## Work packages
1. **I/O image & quality contract** — image semantics, quality enum/reasons, last-good, defaults, scan IN/OUT timing
2. **Binding model & schema** — IN/OUT/INOUT, setpoint split default, units, uniqueness rules, config shape in thin integration
3. **Wedge I/O contract update** — retire `*_BAD`; point safety/HMI at tag quality
4. **Packaging note revision** — mock/sim moves to thin integration; Add-on image SoT unchanged
5. **Thin-integration stub** — declarations, bindings, unit convert, mock entities, scan-boundary image refresh API toward Add-on
6. **Contract/unit tests** — mocked HA; acceptance checklist above

## Open items
- Exact reason-code list (minimal set: `unavailable`, `unknown`, `stale`, `fault`, …)
- Exact YAML/config schema field names
- How Add-on consumes the binding table from the integration (API/IPC) — sketch only if needed for stub
- Whether wedge runtime (`plcassistant/wedge`) gains a shared quality type now or only via adapter in this Task

## Tracker
- Provider: jira
- Story: [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81)
- Task: [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86)
- Sub-tasks:
  - [SWD-95](https://marcusknielsen.atlassian.net/browse/SWD-95) — I/O image & quality contract
  - [SWD-98](https://marcusknielsen.atlassian.net/browse/SWD-98) — Binding model & schema
  - [SWD-96](https://marcusknielsen.atlassian.net/browse/SWD-96) — Wedge I/O contract update
  - [SWD-97](https://marcusknielsen.atlassian.net/browse/SWD-97) — Packaging note revision
  - [SWD-99](https://marcusknielsen.atlassian.net/browse/SWD-99) — Thin-integration stub
  - [SWD-100](https://marcusknielsen.atlassian.net/browse/SWD-100) — Contract/unit tests

## Next
`/implement SWD-86` — Build per this plan
