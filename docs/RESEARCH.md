# Research: Programming surface (SWD-82)

**Tracker:** [SWD-82](https://marcusknielsen.atlassian.net/browse/SWD-82)  
**Parent:** [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81) · Roadmap theme 4  
**Date:** 2026-07-27  
**Tooling:** `scripts/arxiv_research.py` (stdlib arXiv Atom client)

## Question

What should PLCAssistant’s **programming surface** mean for lab / hobby users — especially:

1. What “easy high-level” entry looks like without feeling like Home Assistant automations alone
2. What **escape hatches** preserve a path toward a credible soft-PLC (IEC-shaped depth)
3. How progressive disclosure (easy → customizable) should layer atop the locked **cyclic scan + FB** semantics ([SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85))

Scope: inform `/define SWD-82`. Do **not** lock packaging (SWD-84) or reopen scan/safety contracts.

## Strategy

| Step | What |
|------|------|
| Seed queries | IEC 61131 languages; behavior trees in industrial controllers; low-code / visual PLC programming; OpenPLC / soft-PLC editors |
| Lookup cores | Prior SWD-85 anchors: BT industrial ([2404.14030](https://arxiv.org/abs/2404.14030)), low-code factory ([2504.04224](https://arxiv.org/abs/2504.04224)), 61131 vs 61499, OpenPLC |
| Recency | 2023–2026 LD/ST/SFC tooling, LLM codegen for PLC graphics/text |
| EUD slice | End-user programming / Blockly–Scratch–Node-RED adjacent to automation |
| Snowball | From BT industrial, visual program generation, FBD no-code, IEC complexity |
| Triage | Keep PLC authoring / progressive depth / BT / IEC language UX; drop PLC=power-line, clinical, pure LLM surveys without industrial control |

Raw JSON under `/tmp/swd82-research/` (not committed).

## Summary (answers for define)

### Easy high-level for lab users

Literature does **not** converge on one “easy” PLC language. It does converge on **composition of modular control units** above raw LD/ST:

1. **Behavior Trees** as a lean, modular, graphical high-level for industrial automation controllers ([2404.14030](https://arxiv.org/abs/2404.14030)); assisted BT UIs studied in robotics ([2602.09772](https://arxiv.org/abs/2602.09772)). Fits “approachable industrial patterns” without forcing day-1 Ladder literacy.
2. **IEC 61131-3 graphical languages** (LD, FBD, SFC) remain the industrial vocabulary; complexity differs sharply between graphical and textual forms ([2212.05918](https://arxiv.org/abs/2212.05918)). FBD/no-code generation from documentation is an active “easy entry” research line ([2304.04117](https://arxiv.org/abs/2304.04117)).
3. **End-user programming** patterns (goal-oriented / block-based / assisted composition) are mature in **robotics** ([2403.13988](https://arxiv.org/abs/2403.13988), [2402.17878](https://arxiv.org/abs/2402.17878)) more than in soft-PLC-on-HA — PLCAssistant must adapt, not copy HA YAML automations as the product metaphor.

**Implication:** v1 “easy” should feel like **composing named FBs / modes / recipes on the scan** (wedge cascade already is one FB story), not writing LD or HA scripts. BTs or a small block/graph layer are the strongest prior-art metaphors.

### Escape hatches toward credible soft-PLC

Credibility in the literature still means **IEC 61131-shaped programs** (LD/ST/SFC/FBD) with scan semantics — already locked in SWD-85. Formal and tooling work treats those languages as the artifact of record ([2202.04076](https://arxiv.org/abs/2202.04076), [1301.3047](https://arxiv.org/abs/1301.3047), OpenPLC-oriented ESBMC line).

Practical progressive depth for define:

| Layer | Surface | Credibility role |
|-------|---------|------------------|
| L0 | Wedge / skid config + HMI modes (exists) | Demo today |
| L1 | High-level composition (BT / block graph of FBs + modes) | “Easy industrial” entry |
| L2 | Continuous FB parameters (PID, clamps — SWD-85) | Tuning without rewriting structure |
| L3 | Textual/graphical IEC-like or scripted-on-scan escape | Soft-PLC depth path |

Do **not** make L3 the day-1 UX. Do **not** replace the scan with IEC 61499 event FBs as the authoring model (SWD-85).

### LLM / generative PLC coding (adjacent, not core)

2023–2026 arXiv is heavy on LLM generation of ST, LD, SFC ([2305.15809](https://arxiv.org/abs/2305.15809), [2410.15200](https://arxiv.org/abs/2410.15200), [2410.22159](https://arxiv.org/abs/2410.22159), [2512.06787](https://arxiv.org/abs/2512.06787)). Useful as a **future assist** on L3, weak as the primary lab programming metaphor (verification, trust, and OpenPLC security concerns remain). Define should treat LLM codegen as **optional assist**, not the product surface.

### Relation to HA

HA dashboards / Node-RED-like flows are great HMI and integration glue — already outsourced per roadmap. The Soft-PLC programming surface must stay **scan-native** (compose what runs *inside* IN→safety→control→OUT), distinct from HA automation triggers.

## Key papers

| arXiv | Title | Why it matters |
|-------|-------|----------------|
| [2404.14030](https://arxiv.org/abs/2404.14030) | Towards Using Behavior Trees in Industrial Automation Controllers | BT as modular high-level on industrial controllers — primary L1 metaphor candidate |
| [2602.09772](https://arxiv.org/abs/2602.09772) | Assisted Programming Interface for Behavior Trees in Robotics | UX evidence for assisted BT authoring |
| [2212.05918](https://arxiv.org/abs/2212.05918) | Measuring Overall Complexity of Graphical and Textual IEC 61131-3 | Graphical vs textual complexity — informs progressive depth |
| [2304.04117](https://arxiv.org/abs/2304.04117) | No Code AI: FBD generation from documentation | “Easy” as FBD/no-code, not HA YAML |
| [2502.16529](https://arxiv.org/abs/2502.16529) | Visual Program Generation (RAFT + preference opt.) | Visual languages as accessible industrial-adjacent entry |
| [2401.09185](https://arxiv.org/abs/2401.09185) | Behavior Trees with Dataflow (Lingua Franca) | BT + reactive dataflow — composition patterns |
| [2403.13988](https://arxiv.org/abs/2403.13988) | Goal-Oriented End-User Programming of Robots | EUD patterns transferable to lab users |
| [2202.04076](https://arxiv.org/abs/2202.04076) | K-ST formal ST semantics | Escape hatch credibility = real IEC-shaped semantics |
| [1301.3047](https://arxiv.org/abs/1301.3047) | Coq semantics for PLC (SFC/IL/LD/FBD) | Multi-language top-level control-flow thinking |
| [2410.15200](https://arxiv.org/abs/2410.15200) | LLM support for IEC 61131-3 graphic languages | LLM assist for graphics — secondary |
| [2512.06787](https://arxiv.org/abs/2512.06787) | LLM4SFC | SFC generation — secondary |
| [2504.04224](https://arxiv.org/abs/2504.04224) | Robustness & safety in low-code factory automation | Approachable industrial without overclaiming SIL |
| [2509.22664](https://arxiv.org/abs/2509.22664) | OpenPLC security issues | Soft-PLC trust boundary — packaging (SWD-84), not authoring UX |

## Themes

1. **Composition first, languages second** — easy entry = wiring FBs/modes/BTs on the scan; LD/ST are depth, not onboarding.
2. **BTs are the strongest “industrial but approachable” L1 prior art** for controllers; robotics EUD is a secondary pattern source.
3. **IEC 61131 remains the credibility escape hatch** — measure complexity and keep a path to ST/LD/SFC-shaped artifacts later.
4. **LLM codegen is assistive noise for v1** — popular on arXiv; not the programming *product*.
5. **Keep Soft-PLC authoring distinct from HA automations** — HA owns HMI/integration; Soft-PLC owns scan logic composition.
6. **Progressive disclosure is the product** — L0 config → L1 graph/BT → L2 params → L3 IEC/script; each layer reuses the same scan + FB runtime (SWD-85).

## Gaps

- Almost no peer-reviewed work on **Home Assistant + soft-PLC programming UX**; design must be original, guided by BT/EUD/IEC priors.
- “Lab hobby” users are under-studied vs factory PLC programmers and robot EUD subjects.
- Visual/low-code papers often assume FBD/LD literacy or factory toolchain; PLCAssistant still needs a thinner L1 vocabulary tied to the wedge (modes, cascade, trips).
- Node-RED / Blockly appear more in adjacent automation than in IEC soft-PLC cores — treat as inspiration, not a required dependency.

## Suggested reading order

1. [2404.14030](https://arxiv.org/abs/2404.14030) — BT on industrial controllers  
2. [2212.05918](https://arxiv.org/abs/2212.05918) — graphical vs textual IEC complexity  
3. Wedge + control docs (`docs/wedge/03`, `docs/control/`) — what already runs on the scan  
4. [2304.04117](https://arxiv.org/abs/2304.04117) / [2502.16529](https://arxiv.org/abs/2502.16529) — easy visual/no-code metaphors  
5. [2602.09772](https://arxiv.org/abs/2602.09772) — assisted BT UX  
6. [2202.04076](https://arxiv.org/abs/2202.04076) — only when specifying L3 escape hatch  
7. LLM PLC papers — skim only if defining optional assist  

## Implications for `/define SWD-82`

Draft define should lock (conceptually):

- **Progressive layers L0–L3** (config → high-level composition → FB params → IEC/script escape)
- **L1 metaphor preference** (BT vs FBD-like blocks vs recipe-only) — pick one primary for v1
- **What is not HA automation** — authoring produces Soft-PLC scan logic, not HA triggers
- **Non-goals:** full LD/ST IDE day-1; LLM-as-primary editor; replacing scan with 61499
- Acceptance: a lab user can express wedge cascade/modes at L0/L1 without writing LD; an advanced path to L2/L3 is documented even if L3 is stubbed

## Sources

- arXiv Atom API via `scripts/arxiv_research.py` (`search` ×3 batches, `lookup`, `snowball`)
- Repo: `docs/ROADMAP.md`, `docs/PLAN.md` (SWD-85), `docs/control/`, `docs/wedge/03-control-story.md`

## Tracker

- Task [SWD-82](https://marcusknielsen.atlassian.net/browse/SWD-82) remains **To Do** until define/implement; research artifact is this doc.
- Story [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81) Next → `/define SWD-82`.

## Next

`/define SWD-82` — turn this brief into `docs/PLAN.md` + Sub-tasks for the programming surface (progressive layers, L1 metaphor, escape hatch).
