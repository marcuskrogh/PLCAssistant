# Implementation plan: Programming surface (SWD-82)

## Summary
- Progressive **Python block library**: place copies → edit that copy → or author new library blocks in-App.
- **JSON-shaped program dict is the v1 program-of-record** (YAML-ready: same structure for `yaml.safe_load` / `yaml.safe_dump`). App visual editor reads/writes that dict via JSON API. HA **integration stays connections-only** (entities ↔ tags).
- **Hybrid graph**: pin wiring + explicit deterministic execution order on the scan.
- **Fixed** mode/safety shell (non-bypassable). User graph runs in CONTROL only.
- **Hybrid wedge**: framework + enough blocks to run the mock skid on the new surface.
- Apply changes via **restart** by default; **super-user hot-apply** for development.

## Scope
**In**
- Block model + YAML-ready schema (instances as copies, pins/wires, params, execution order)
- Python block runtime API (scan tick; tag/pin I/O) inside Soft-PLC App
- Built-in library (read-only) with wedge-capable blocks (e.g. Level/Flow PI and supporting pieces)
- User library: create/edit custom Python blocks via **in-App editor**; place always **copies**; **reset-to-library** on a placed copy
- App visual canvas + JSON editing of the same program dict
- Loader: restart-apply default; super-user on-the-fly apply
- Migrate mock skid control path onto the block program (safety/mode shell unchanged)
- Contract/unit tests + a minimal App editor smoke path

**Out**
- SIL / certified safety authoring
- Full IEC 61131 IDE (LD/ST/SFC editors) — Python blocks first; IEC later optional
- Behavior trees / LLM codegen as primary surface
- HA automations / Node-RED as the Soft-PLC program
- Editing built-in library definitions
- Deep packaging freeze beyond “App hosts editor + runtime; integration = bindings” ([SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84))
- Physical rig

## Decisions
- Easy path = **block library + params** on a visual canvas (JSON/YAML-shaped dict)
- Depth = edit **placed copy** or add **custom user-library** Python block
- Python only for v1 block bodies
- JSON-shaped dict program-of-record (YAML-ready); visual updates the same dict
- Safety/mode **fixed shell**; user blocks cannot bypass
- Built-ins **stock** (read-only templates); user library for new templates
- Place always **copies** the template; editing a placed block never mutates the library; **reset-to-library** restores a placed copy from its template
- Hybrid wiring + execution order (topo-sort default; explicit override allowed)
- Editor + runtime in the **App** (formerly “Add-on”); integration = connections layer only
- Restart to apply program changes by default; **super-user hot-apply** for development

## Constraints
- Preserve SWD-85 scan order: IN → safety → control → OUT; user graph executes only in CONTROL
- Preserve SWD-86 I/O image, quality, and bindings; integration must not grow a program authoring surface
- Must not claim SIL or certified safety PLC
- Soft-PLC ≠ HA automations — program-of-record lives in the App (JSON-shaped / YAML-ready dict), not HA automation YAML
- Built-in library templates remain stock; no in-place mutation of shipped blocks
- Demo-grade wedge behavior must still pass existing mock acceptance intent after migration

## Inputs (supportive — not substitutes for decisions above)
- Research: [`docs/RESEARCH.md`](RESEARCH.md) (multi-axis programming-surface survey)
- Prior locks: `docs/control/*`, `docs/io/*`, `docs/wedge/*`

## Acceptance criteria
- Mock skid runnable as a JSON-shaped / visual program of built-in blocks under the fixed safety shell
- Placing a block creates an independent copy; editing it does not change the library; reset restores from template
- User can create a custom Python block in-App, place it, and see it run in CONTROL
- Program dict ↔ visual round-trip for the same program
- Restart applies program changes; super-user hot-apply documented and testable
- Safety still forces CV safe the same scan regardless of user graph
- Tests cover loader, copy-on-place, reset, execution order, and safety precedence without real HA

## Work packages
1. **Block model + YAML-ready schema** — instance copies, pins/wires, params, execution order → `docs/surface/`, schema module ([SWD-119](https://marcusknielsen.atlassian.net/browse/SWD-119))
2. **Python block runtime + scan integration** — tick API; CONTROL-phase execution ([SWD-116](https://marcusknielsen.atlassian.net/browse/SWD-116))
3. **Built-in wedge block library** — Level/Flow PI and supporting stock blocks ([SWD-115](https://marcusknielsen.atlassian.net/browse/SWD-115))
4. **User library + in-App Python editor** — create/edit user templates; copy-on-place; reset-to-library ([SWD-114](https://marcusknielsen.atlassian.net/browse/SWD-114))
5. **App visual canvas** — wires + order bound to the program dict ([SWD-120](https://marcusknielsen.atlassian.net/browse/SWD-120))
6. **Apply policy** — restart default + super-user hot-apply ([SWD-117](https://marcusknielsen.atlassian.net/browse/SWD-117))
7. **Wedge skid migration** — mock skid control path onto block program; shell unchanged ([SWD-121](https://marcusknielsen.atlassian.net/browse/SWD-121))
8. **Contract/unit tests + acceptance doc** ([SWD-118](https://marcusknielsen.atlassian.net/browse/SWD-118))

## Open items
- Exact YAML field names / pin typing details — lock during implement of package 1
- Super-user hot-apply auth mechanism (App setting vs env flag) — lock in package 6
- Whether “App” rename lands in all historical wedge/packaging docs in this Task or only new SWD-82 docs — prefer new docs + light cross-links; full rename can ride SWD-84

## Tracker
- Provider: jira
- Story: [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81)
- Task: [SWD-82](https://marcusknielsen.atlassian.net/browse/SWD-82)
- Research: [`docs/RESEARCH.md`](RESEARCH.md)
- Sub-tasks:
  - [SWD-119](https://marcusknielsen.atlassian.net/browse/SWD-119) — Block model + YAML schema
  - [SWD-116](https://marcusknielsen.atlassian.net/browse/SWD-116) — Python block runtime + scan integration
  - [SWD-115](https://marcusknielsen.atlassian.net/browse/SWD-115) — Built-in wedge block library
  - [SWD-114](https://marcusknielsen.atlassian.net/browse/SWD-114) — User library + in-App Python editor
  - [SWD-120](https://marcusknielsen.atlassian.net/browse/SWD-120) — App visual canvas bound to YAML
  - [SWD-117](https://marcusknielsen.atlassian.net/browse/SWD-117) — Apply policy (restart + hot-apply)
  - [SWD-121](https://marcusknielsen.atlassian.net/browse/SWD-121) — Wedge skid migration onto blocks
  - [SWD-118](https://marcusknielsen.atlassian.net/browse/SWD-118) — Contract/unit tests + acceptance

## Next
`/define SWD-84` — Packaging shape; research brief is supportive context only
