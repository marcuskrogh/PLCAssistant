# Roadmap: Standardised PID blocks (ISA visualisation and structure)

## Destination
PID function blocks on the Soft-PLC Diagram and operator faceplates use one
ISA-aligned glyph and one named algorithm structure, so every loop looks and
behaves like the same industrial PID rather than a generic rectangle with
ad-hoc pins.

## Notes
- Visualisation follows ANSI/ISA-5.1-2024 functional diagrams (Table 15
  three-mode controller + Table 16 P / I / D symbols).
- Algorithm names follow ISA-TR5.9-2023 (Parallel / Standard / Series;
  two-degree-of-freedom β / γ; signals PV, SP, CO).
- Practical code follows Bauer, Sundström, Guzmán, Hägglund, Soltesz
  (IFAC 2024; arXiv:2604.15918, 2026): hybrid incremental / positional PID.
- Existing wedge cascade instances `level_pi` / `flow_pi` must keep working.
- Research findings: [`docs/RESEARCH.md`](RESEARCH.md). Plan: [`docs/PLAN.md`](PLAN.md).

## Route
| Order | Task | Type | Blocked by | Status | Issue |
|-------|------|------|------------|--------|-------|
| 1 | Define & ship standardised PID visualisation and structure | define | — | To Do | [SWD-360](https://marcusknielsen.atlassian.net/browse/SWD-360) |

## Cleared so far
- Research pass on ISA-5.1 / ISA-TR5.9 and Bauer et al. 2024–2026 — `docs/RESEARCH.md`

## Not yet specified
- Whether later slices add ISA-TR5.9 Series form, external-reset feedback, or
  classic output Manual on the Lovelace card
- Whether internal calculation should move from engineering units to percent of
  range (ISA-TR5.9 preference)

## Out of scope
- Autotune / gain scheduling
- ISA-5.5 process-equipment glyphs (pumps, vessels) on the Diagram
- Replacing Lovelace with a full ISA-101 HMI
- Vendor-copying the copybit/pid GitHub listing into the App
- Fractional-order or PIDD2 extensions

## Tracker
- Provider: jira
- Story (map): [SWD-359](https://marcusknielsen.atlassian.net/browse/SWD-359)
- Tasks: [SWD-360](https://marcusknielsen.atlassian.net/browse/SWD-360)
- Sub-tasks: SWD-361, SWD-362, SWD-363, SWD-364, SWD-365

## Next
`/implement SWD-360` — Build per PLAN.md (ISA-5.1 glyph, TR5.9 contract, Bauer hybrid algorithm)
