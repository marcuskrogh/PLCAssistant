# Implementation plan: Programming surface (SWD-82)

## Summary
- Soft-PLC authoring is **progressive disclosure L0→L3**: config / default skid → **behavior-tree composition** → FB parameter tuning → documented escape hatch — not a day-1 IEC IDE and not HA automations.
- **L1 primary metaphor = behavior trees** (industrial-controller prior art) composed of named actions/conditions over existing FBs, modes, and tags; declarative program artifact (YAML) loads into the Soft-PLC.
- Authoring produces logic that runs **inside** the locked scan (**CONTROL** phase), atop SWD-85 FBs; **SAFETY remains non-bypassable** and is not a user BT playground.
- **LLM codegen and visual editors are out** of this Task; L3 is a **stubbed path** (documented hook), not a full ST/LD runtime.

## Scope
**In**
- Document progressive layers L0–L3 and the Soft-PLC ≠ HA automation boundary
- Declarative program artifact schema (YAML) for L1 BT + references to L0/L2 knobs
- Minimal BT subset runtime: Sequence, Selector, Condition, Action (leaf); tick once per scan in CONTROL when a program is loaded
- Default L0 path: today’s wedge skid (modes + cascade) remains valid with **no** BT required
- Express the wedge cascade/modes as an equivalent L1 example program (parity demo)
- L2: expose continuous FB / clamp params as tunable program or config fields without rewriting structure
- L3: document escape-hatch interface (scripted CONTROL hook / callable) and ship a stub or no-op adapter — not a full IEC language
- Contract/unit tests: load program, BT tick order, safety still precedes/overrides, L0 skid unchanged when no program, wedge L1 example can drive mode/cascade intents without LD
- Cross-link control/wedge docs; do not reopen scan phase order or safety semantics

**Out**
- Full IEC 61131-3 IDE (LD/ST/SFC/FBD editors) or OpenPLC editor embedding
- IEC 61499 as authoring model
- Visual / drag-drop BT or FBD editor UI (declarative file is v1 surface)
- LLM-as-primary programming product (optional assist later)
- User-authored safety trees that bypass trips/permissives/LOS
- Node-RED / Blockly / HA automation YAML as the Soft-PLC program format
- Packaging / Add-on install shape (SWD-84)
- Physical rig commissioning; SIL claims

## Decisions
- **Progressive layers locked:**

| Layer | Surface | v1 deliverable |
|-------|---------|----------------|
| **L0** | Wedge/skid config + HMI modes (existing) | Remains default; no BT required |
| **L1** | Behavior tree composition of FB/mode/tag leaves | YAML program + BT tick runtime |
| **L2** | Continuous FB parameters (PID/clamps — SWD-85) | Tunable via program/config fields |
| **L3** | Scripted-on-scan / future IEC-shaped escape | Documented stub interface only |

- **L1 metaphor = BT**, not FBD-first and not recipe-only. Recipes/modes appear as Action/Condition leaves or L0 config, not a separate primary language.
- **BT subset (v1):** `sequence`, `selector`, `condition`, `action`. Parallel / decorators deferred (open item).
- **Artifact format:** declarative **YAML** program file validated in-process (no HA regeneration of Soft-PLC logic).
- **Scan placement:** BT evaluates in **CONTROL** only; IN → SAFETY → CONTROL → OUT unchanged. Safety code owns trips; program may *request* Start/Stop/Reset-style intents that safety still gates.
- **Soft-PLC ≠ HA:** HA owns Lovelace HMI, entity bindings, and HA automations; Soft-PLC owns scan-native program + FBs. Authoring must not compile to HA automation triggers as the control engine.
- **Credibility path:** L3 documents how a future ST/script leaf would plug into CONTROL; shipping L3 depth is not required for Task Done.
- **Non-goals copy:** no “verified PLC”, no SIL, no “full Codesys replacement” claims in docs/UX.

## Constraints
- Preserve SWD-85 scan shell, FB cascade, safety precedence, and SWD-86 I/O image contracts
- Preserve wedge tag names, modes (`STOP`/`RUNNING`/`TRIPPED`), and five safety behaviors
- BT / program must not write CV in ways that skip safety force-zero on the same scan
- Default skid path (no program file) must keep existing mock acceptance green
- No new hard dependency on Node-RED, Blockly, or an external IEC IDE
- Demo-grade BT example only needs wedge parity — not a general factory library

## Acceptance criteria
- Documented L0–L3 model and Soft-PLC vs HA boundary with cross-links to `docs/control/` and `docs/wedge/`
- YAML program schema + loader rejects unknown node types / invalid leaf refs with clear errors
- BT runtime ticks once per CONTROL phase; Sequence/Selector/Condition/Action semantics documented and tested
- With no program loaded, wedge skid behavior matches pre-SWD-82 (regression)
- Example L1 program can express wedge start/run/cascade intent at the composition layer without LD/ST
- L2 params adjustable without editing BT structure; L3 escape interface documented (stub acceptable)
- Safety trip still forces `CMD_SPEED = 0` same scan; user program cannot override that precedence
- Tests green without real Home Assistant

## Work packages
1. **Layer model & Soft-PLC≠HA boundary** — L0–L3 narrative + authoring boundary → `docs/programming/01-layers.md`, `docs/programming/02-vs-ha.md` ([SWD-107](https://marcusknielsen.atlassian.net/browse/SWD-107))
2. **Program artifact schema & loader** — YAML BT/program schema, validation, load API → `docs/programming/03-program-schema.md`, `plcassistant/programming/` ([SWD-110](https://marcusknielsen.atlassian.net/browse/SWD-110))
3. **L1 BT runtime on CONTROL** — Sequence/Selector/Condition/Action tick; wire into scan CONTROL → `docs/programming/04-bt-runtime.md`, runtime module ([SWD-108](https://marcusknielsen.atlassian.net/browse/SWD-108))
4. **L0 default + wedge L1 example** — no-program skid path; example YAML expressing modes/cascade leaves → `docs/programming/05-l0-l1-wedge.md` ([SWD-112](https://marcusknielsen.atlassian.net/browse/SWD-112))
5. **L2 params + L3 escape stub** — param surface docs; escape-hatch interface stub → `docs/programming/06-l2-l3.md` ([SWD-111](https://marcusknielsen.atlassian.net/browse/SWD-111))
6. **Contract/unit tests** — load/validate, tick order, safety precedence, L0 regression, wedge L1 example → `docs/programming/07-acceptance.md`, `tests/test_swd82_acceptance.py` ([SWD-109](https://marcusknielsen.atlassian.net/browse/SWD-109))

## Open items
- Exact YAML top-level field names (`program` / `tree` / `params`) — lock during implement schema package
- Whether `parallel` / decorator nodes enter v1 subset or stay deferred
- L3 stub shape: Python callable registered on CONTROL vs placeholder protocol only
- Whether program live-reload mid-run is required for acceptance (default: load at start / explicit reload API; no hot-edit UI)
- Visual editor / assisted BT UI — explicitly later; not this Task

## Tracker
- Provider: jira
- Story: [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81)
- Task: [SWD-82](https://marcusknielsen.atlassian.net/browse/SWD-82)
- Research: [`docs/RESEARCH.md`](RESEARCH.md)
- Sub-tasks:
  - [SWD-107](https://marcusknielsen.atlassian.net/browse/SWD-107) — Layer model & Soft-PLC≠HA boundary
  - [SWD-110](https://marcusknielsen.atlassian.net/browse/SWD-110) — Program artifact schema & loader
  - [SWD-108](https://marcusknielsen.atlassian.net/browse/SWD-108) — L1 BT runtime on CONTROL
  - [SWD-112](https://marcusknielsen.atlassian.net/browse/SWD-112) — L0 default + wedge L1 example
  - [SWD-111](https://marcusknielsen.atlassian.net/browse/SWD-111) — L2 params + L3 escape stub
  - [SWD-109](https://marcusknielsen.atlassian.net/browse/SWD-109) — Contract/unit tests

## Next
`/implement SWD-82` — Build per this plan
