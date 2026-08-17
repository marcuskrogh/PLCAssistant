# Research brief: ISA PID standardisation and Bauer reference implementation

**Tracker:** [SWD-360](https://marcusknielsen.atlassian.net/browse/SWD-360)  
**Story:** [SWD-359](https://marcusknielsen.atlassian.net/browse/SWD-359)  
**Date:** 2026-08-17  
**Tooling:** `scripts/arxiv_research.py` + WebSearch / WebFetch

## Question

What do current **ISA** documents and **Margret Bauer**’s recent publications
say about:

1. **Visualisation** — how a PID should be drawn as a function block / functional
   diagram / operator display
2. **Structure** — named algorithm forms, pins, modes, anti-windup, and
   practical digital implementation

Scope: supportive evidence for `/define` on standardised Soft-PLC PID blocks.
This brief does **not** decide product scope, UX, or acceptance.

## Axes covered

| Axis | Status | Notes |
|------|--------|-------|
| Preprints (arXiv) | covered | Multi-query search; core hit is arXiv:2604.15918 (Bauer et al., 2026). Broader “PID + standard” queries are noisy (unrelated PID acronyms). |
| Formal written | covered | ISA-TR5.9-2023 (via ISA InTech excerpt); ANSI/ISA-5.1-2024 (functional diagram + Table 16); IFAC-PapersOnLine 2024 reference implementation (DOI 10.1016/j.ifacol.2024.08.090) |
| Web discovery | covered | ISA-5 series hub; ANSI blog on ISA-5.1-2024; ISA committee pages |
| Informal / practitioner | covered | Bauer LinkedIn 2026-04-29; Control Global ISA 5.9 columns; GitHub copybit/pid listings. Labeled informal. |

## Search strategy

| Axis | Queries / targets |
|------|-------------------|
| Preprints | `au:Bauer AND all:PID`; `all:"reference implementation" AND PID`; `all:PID AND (standard OR standardisation OR ISA)`. Unique papers: 18. Core: [arXiv:2604.15918](https://arxiv.org/abs/2604.15918). |
| Formal | [ISA-5 series](https://www.isa.org/standards-and-publications/isa-standards/isa-5-standard); [ISA-TR5.9 InTech](https://www.isa.org/intech-home/2023/june-2023/features/isa-tr5-9-2023-realizing-and-achieving-best-pid); ANSI/ISA-5.1-2024 Table 15–16; [IFAC 2024 DOI](https://doi.org/10.1016/j.ifacol.2024.08.090); [Lund post-print](https://lucris.lub.lu.se/ws/files/177637056/sundstrom24a.pdf) |
| Web | ISA-5.1 / ISA-5.5 committee pages; ANSI blog 2024 revision notes |
| Informal | [Bauer LinkedIn](https://www.linkedin.com/posts/margret-bauer-a885618_after-two-years-of-developing-a-standard-activity-7455172250363854848--8qU); [Control Global part 1](https://www.controlglobal.com/control/loop-control/article/11290464/the-concealed-pid-revealed-part-1) / [part 3](https://www.controlglobal.com/control/loop-control/article/11289104/the-concealed-pid-revealed-part-3); [github.com/copybit/pid](https://github.com/copybit/pid) |

## Executive summary (what the sources say)

ISA and Bauer answer **different halves** of “standard PID”:

- **ISA-TR5.9-2023** standardises **names**: Parallel, Standard, and Series
  algorithm forms; two-degree-of-freedom (2DoF) structures with setpoint weights
  β and γ; signals treated as percent of engineering-unit range; direct vs
  reverse action. It is a technical report laying a foundation for a future
  standard, not a code listing.
- **ANSI/ISA-5.1-2024** standardises **drawings**: functional diagrams use
  Table 15 controller glyphs composed from Table 16 signal-processing blocks
  (difference, proportional K/P, integral ∫/I, derivative d/dt/D). A three-mode
  PID is an error summer plus P, I, and D compartments — not a blank rectangle.
- **Bauer et al.** (IFAC PID 2024, then the 2026 practical guide) standardise
  **implementation**: a hybrid incremental (velocity) / positional controller
  with anti-windup, bumpless transfer, setpoint weighting, feed-forward inside
  the block, tracking, filtering, and jitter compensation. They cite ISA 2023
  as nomenclature, not as an implementation spec. There is still **no ISA
  standard for PID source code**.

Industrial 2DoF practice (ISA-TR5.9 commentary / Control Global) most often
uses **PI on error, derivative on PV** (γ = 0) to avoid derivative kick.

## Key sources

| Title | Axis | ID/URL | Relevance |
|-------|------|--------|-----------|
| A Practical Guide to PID Controller Implementation | Preprint | [arXiv:2604.15918](https://arxiv.org/abs/2604.15918) | Bauer, Sundström, Guzmán, Hägglund, Soltesz (compiled 2026-05-07; v3 2026-07-14). Hybrid incremental/positional reference; pins r/y; auto/uman; track; uff. |
| Reference Implementation of the PID Controller | Formal | [doi:10.1016/j.ifacol.2024.08.090](https://doi.org/10.1016/j.ifacol.2024.08.090) | Peer-reviewed 2024 conference version; incremental form; GitHub copybit/pid. |
| ISA-TR5.9-2023 (InTech excerpt) | Formal | [ISA InTech June 2023](https://www.isa.org/intech-home/2023/june-2023/features/isa-tr5-9-2023-realizing-and-achieving-best-pid) | Naming: Parallel / Standard / Series; % of range; 2DoF; external-reset feedback. |
| ANSI/ISA-5.1-2024 | Formal | ISA-5.1-2024 Table 15–16 | Three-mode controller glyph; Table 16 symbols 8 (P), 10 (I), 11 (D). |
| ISA-5 series hub | Web | [isa.org ISA-5](https://www.isa.org/standards-and-publications/isa-standards/isa-5-standard) | Places TR5.9 and 5.1 in the same documentation family. |
| copybit/pid `pid.txt` | Informal | [github.com/copybit/pid](https://github.com/copybit/pid) | Living pseudo-code listing (no license on the repo). |
| Bauer LinkedIn, 2026-04-29 | Informal | [LinkedIn post](https://www.linkedin.com/posts/margret-bauer-a885618_after-two-years-of-developing-a-standard-activity-7455172250363854848--8qU) | Announces finalised “standard PID” code after two years. |

## Themes and trends

### 1. Nomenclature is standardised; source code is not

ISA-TR5.9 exists because vendors used incompatible names for the same
equations. Bauer et al. (2024, 2026) repeat that ISA 2023 covers nomenclature
and use, **not** implementation, and that commercial PIDs often omit
anti-windup.

### 2. Three algorithm forms, one 2DoF structure family

ISA-TR5.9 names:

| Form | Idea |
|------|------|
| Parallel | Independent Kc, Ki, Kd summed to CO |
| Standard | Kc applied to P, I (Ti), and D (Td) together |
| Series | Derivative as phase-lead before PI; identical to Standard when Td = 0 |

2DoF setpoint weights: β on proportional, γ on derivative (Bauer uses b and c
for the same idea). Structure “PI on error, D on PV” (γ = 0) is the common
industrial default.

### 3. Functional-diagram PID is a composed glyph

ISA-5.1 Table 15 “automatic three-mode controller”: top box is Table 16
symbol 3 (difference); left / centre / right boxes are symbols 8, 10, 11
(P, I, D). Identification bubbles (LIC, FIC) belong on P&IDs, not as a
substitute for that software glyph.

ISA-5.5-1985 is for process-equipment display symbols (pumps, vessels). ISA
marks it inactive and points HMI work to ISA-101. It is not a PID faceplate
standard.

### 4. Practical digital PID is incremental when integral is present

Bauer 2026: incremental form gives bumpless transfer and clamping anti-windup
without a tracking-time parameter; positional form is required when ki = 0
(P / PD), with bias u0. Feed-forward must enter **inside** the block before
anti-windup. Measurement filter on y; derivative on filtered PV. Optional
tracking (output follows utrack) and auto/manual (CO = uman when not auto).

The 2024 IFAC listing and 2026 guide agree on this pin set:

```text
PID(r, y; uff, uman, utrack, Tx=1.0, track, auto, windup) → u
```

ISA-TR5.9 aliases: r ≈ SP, y ≈ PV, u ≈ CO.

### 5. Manual mode is output Manual, not SP-source

Bauer `auto=false` means the operator (or a higher layer) supplies **CO**
(`uman`). ISA-5.1 Table 15 also shows auto-manual stations as separate
manual signal processors. That is a different concept from PLCAssistant’s
current Manual / Automatic / Remote **setpoint-source** mux.

## Gaps and limitations

- Full ISA-TR5.9 and ISA-5.1 PDFs are paywalled; this brief uses the ISA
  InTech excerpt, the public ISA-5 hub, and retrieved Table 15–16 text.
  Fine print (normative notes, ERF annexes) may be incomplete.
- copybit/pid has **no declared license** and is a tiny pseudo-code dump
  (last push 2024-03-19). Treat it as illustration, not a vendored dependency.
- IEC 61514-2 (PID performance evaluation) is cited by Bauer 2026 but was not
  retrieved here.
- ArXiv “PID + standard” search is polluted by other expansions of “PID”
  (process ID, partial information decomposition).

## Recommended reading order

1. ISA InTech excerpt of TR5.9 — Parallel / Standard / Series names
2. ISA-5.1 Table 15–16 — how to draw the three-mode block
3. arXiv:2604.15918 §§2–4 — hybrid algorithm and pin set
4. IFAC 2024 paper + copybit/pid `pid.txt` — compact listing
5. Control Global “Concealed PID” parts 1 and 3 — 2DoF β / γ practice

## Role in pipeline

Finding docs for `/define` and `/implement` on SWD-360. Supportive context
only — not a product plan.

## Sources

- Sundström, E., Bauer, M., Guzmán, J. L., Hägglund, T., Soltesz, K. (2026). *A Practical Guide to PID Controller Implementation*. arXiv:2604.15918. Axis: Preprints.
- Sundström, E., Hägglund, T., Bauer, M., Eker, J., Soltesz, K. (2024). *Reference Implementation of the PID Controller*. IFAC-PapersOnLine 58(7), 370–375. doi:10.1016/j.ifacol.2024.08.090. Axis: Formal written.
- ISA (2023). *ISA-TR5.9-2023, Proportional-Integral-Derivative (PID) Algorithms and Performance*. Described in Morgan & McMillan, InTech, June 2023. Axis: Formal written.
- ISA (2024). *ANSI/ISA-5.1-2024, Instrumentation and Control – Symbols and Identification*, Tables 15–16. Axis: Formal written.
- ISA (n.d.). *ISA-5 Series of Standards*. https://www.isa.org/standards-and-publications/isa-standards/isa-5-standard. Axis: Web discovery.
- copybit (2024). *pid* reference listings. https://github.com/copybit/pid. Axis: Informal / practitioner.
- Bauer, M. (2026-04-29). LinkedIn post announcing finalised standard PID code. Axis: Informal / practitioner.
- Control Global (ISA 5.9 series). *The concealed PID revealed*, parts 1 and 3. Axis: Informal / practitioner.

## Tracker
- Task: [SWD-360](https://marcusknielsen.atlassian.net/browse/SWD-360)
- Story: [SWD-359](https://marcusknielsen.atlassian.net/browse/SWD-359)
- Artifact: docs/RESEARCH.md
- Branch: `cursor/swd-360-isa-pid-blocks-25fc`
- PR: — (research never opens a PR; define opens the delivery PR)

## Next
`/implement SWD-360` — PLAN.md binds the build; research is complete on this branch
