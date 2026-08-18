# Research brief: ISA-101 / ISA-112 and DCS PID faceplates

**Tracker:** [SWD-369](https://marcusknielsen.atlassian.net/browse/SWD-369)  
**Story:** [SWD-368](https://marcusknielsen.atlassian.net/browse/SWD-368)  
**Date:** 2026-08-17  
**Tooling:** WebSearch / WebFetch + `scripts/arxiv_research.py`

## Question

What do current **ISA** documents and industrial HMI practice say about:

1. **Operator PID faceplates** — layout (bars, labels), modes, and what the operator may write
2. **SCADA / HMI colour and chrome** — how to highlight the writable parameter without violating high-performance HMI rules
3. **Which standard actually governs** the two-vertical-bar + horizontal-output layout

Scope: supportive evidence for `/define` on Lovelace PID faceplates. This brief does **not** decide product scope, UX, or acceptance.

## Axes covered

| Axis | Status | Notes |
|------|--------|-------|
| Preprints (arXiv) | covered (empty) | Queries `high performance HMI`, `ISA-101`, `PID faceplate` returned 0 papers. HMI style is not an arXiv topic here. |
| Formal written | covered | ISA-101.01-2015 hub; ISA-TR101.01 / TR101.02; ANSI/ISA-112.00.01-2025 announcement; existing ISA-5.1 / ISA-TR5.9 brief in prior `docs/RESEARCH.md` (SWD-360) |
| Web discovery | covered | ISA press release 2026-02-24; Industrial Cyber on ISA-112; ISA-101 series page; ISA112 lifecycle diagram (points HMI style guides at ISA-101) |
| Informal / practitioner | covered | AVEVA Plant SCADA Analog Controller; Citect Situational Awareness library; FrameworX ISA-101 how-to; plcprogramming.io HPHMI; Casual Process Engineer DCS modes; control.com cascade textbook. Labeled informal. |

## Search strategy

| Axis | Queries / targets |
|------|-------------------|
| Preprints | `all:"high performance HMI"`; `all:ISA-101`; `all:"PID" AND "faceplate"` |
| Formal | [ISA-101 series](https://www.isa.org/standards-and-publications/isa-standards/isa-101-standards); [ISA 2026-02-24 ISA-112 announcement](https://www.isa.org/news-press-releases/2026/february/isa-announces-publication-of-new-standard-for-scad); prior SWD-360 brief (ISA-5.1, ISA-TR5.9, IFAC 2024) |
| Web | Industrial Cyber ISA-112; ISA112 lifecycle PDF |
| Informal | AVEVA Analog Controller; Tatsoft FrameworX ISA-101 how-to; DCS MAN/AUTO/CAS explainers |

## Executive summary (what the sources say)

Four different standards answer four different questions. None of them is “the PDF that draws the two-bar PID faceplate”:

- **ANSI/ISA-101.01-2015** (and TR101.01 philosophy / TR101.02 usability) standardises **HMI practice**: grayscale / low-chroma normal operation, colour reserved for abnormal or required action, analog indicators with context (range, setpoint, limits), consistent widget libraries, display hierarchy. It does **not** prescribe a particular PID bar geometry.
- **ANSI/ISA-112.00.01-2025** (the February 2026 ISA announcement) standardises **SCADA lifecycle, diagrams, and terminology**. It tells organisations to keep an HMI philosophy / style guide and points that work at **ISA-101**. It is not a faceplate drawing spec.
- **ISA-TR5.9-2023** standardises **signal names** on the PID: PV, SP, **CO** (controller output). Informal process language often says MV (manipulated variable) for the same signal. Formal ISA PID nomenclature is CO, not MV.
- **ANSI/ISA-5.1-2024** standardises the **function-block glyph** (ε / P / I / D), already shipped on this product (SWD-360 / SWD-366). It is not the operator faceplate.
- The **two vertical bars (PV, SP) + horizontal output bar** plus **MAN / AUTO / CAS(REM)** is **DCS analog-controller convention** (AVEVA/Citect Situational Awareness Analog Controller; Honeywell / Emerson / Yokogawa family faceplates). SP is editable in Auto; output is editable in Manual; cascade/remote SP is not operator-local.

**Highlighting** in ISA-101 is not a mode colour. Mode identity stays grayscale (selected chrome / outline / invert). Colour is for caution and abnormal (already SWD-366). AVEVA’s green active-mode button is a vendor library choice and **conflicts** with ISA-101 colour-for-abnormal.

**Manual** in DCS and in Bauer / IFAC 2024 is **output Manual** (`auto=false`, operator supplies CO / `uman`). It is not “a third setpoint source while the PID still computes CO”. PLCAssistant’s current Man / Auto / Rem mux is the latter — that is the contradiction to correct.

## Key sources

| Title | Axis | ID/URL | Relevance |
|-------|------|--------|-----------|
| ISA-101 series hub | Formal | [isa.org ISA-101](https://www.isa.org/standards-and-publications/isa-standards/isa-101-standards) | ISA-101.01-2015 + TR101.01 / TR101.02: HMI lifecycle, philosophy, usability — not bar geometry |
| ISA announces ISA-112 Part 1 | Formal | [ISA 2026-02-24](https://www.isa.org/news-press-releases/2026/february/isa-announces-publication-of-new-standard-for-scad) | ANSI/ISA-112.00.01-2025: SCADA lifecycle, diagrams, terminology |
| Industrial Cyber on ISA-112 | Web | [industrialcyber.co](https://industrialcyber.co/isa-iec-62443/isa-issues-ansi-isa-112-standard-to-guide-functional-architecture-models-standardize-scada-lifecycle-architecture/) | ISA-112 includes HMI/alarm *considerations* and control-mode terminology; defers HMI style |
| ISA112 lifecycle diagram | Formal | [ISA PDF 2022-07-08](https://www.isa.org/getmedia/ac809e6d-27ed-4305-b207-9813b04f43b4/ISA112_SCADA-Systems_SCADA-lifecycle-diagram_rev2022-07-08.pdf) | Explicit: “HMI Philosophy and HMI Style Guides (ISA101)” |
| AVEVA Analog Controller | Informal | [docs.aveva.com](https://docs.aveva.com/bundle/plant-scada/page/1206371.html) | SP editable only in Auto; OP editable only in Manual; Auto / Manual / Cascade buttons; output bar below |
| FrameworX ISA-101 how-to | Informal | [docs.tatsoft.com](https://docs.tatsoft.com/display/FX/ISA-101+HMI-Compliance-How-to) | Analog bars: gray fill, dark current, triangle SP; faceplate fields PV / SP / OP; modes AUTO/MAN/CAS |
| High Performance HMI (ISA-101) | Informal | [plcprogramming.io](https://plcprogramming.io/blog/high-performance-hmi-isa-101) | Faceplates with analog bars as the loop-controller widget; colour only when action required |
| DCS controller modes | Informal | [casualprocessengineer.com](https://www.casualprocessengineer.com/Process-control/DCS-Controller-Modes) | MAN = operator sets MV/OP; AUTO = operator sets SP; CAS = SP from another block |
| Cascade control textbook | Informal | [control.com](https://control.com/textbook/basic-process-control-strategies/cascade-control/) | Slave in cascade must stay in CAS; AUTO on the slave breaks the cascade |
| Prior PID brief | Formal (prior) | `docs/RESEARCH.md` history / SWD-360 | ISA-TR5.9 CO; Bauer `auto`/`uman`; ISA-5.1 glyph |

## Themes and trends

### 1. ISA-112 is not ISA-101

The linked February 2026 announcement is **ISA-112 Part 1**. It organises SCADA projects (lifecycle, architecture, terminology, which end-user standards to keep). HMI drawing rules stay in the ISA-101 series. An ISA-112-aligned product still uses an ISA-101 style guide for operator graphics.

### 2. Analog bars are the ISA-101 indicator; dual PV/SP bars are DCS convention

ISA-101-aligned practice prefers analog bars over naked digits so the operator sees value versus range and setpoint at a glance. Typical encodings: gray track, dark fill or pointer for PV, marker for SP, colour only in alarm bands.

The **two adjacent vertical bars (PV and SP) with a horizontal output** is the analog-controller faceplate used by DCS/SCADA libraries. A single PV bar with an SP triangle is also valid HPHMI. The user’s two-bar + horizontal CO request matches the analog-controller family, not a clause in ISA-101.

### 3. Labels are PV / SP / MV on the faceplate; Soft-PLC key stays CO

ISA-TR5.9 and this product’s tags/helpers use **CO**. AVEVA/Citect use **OP**. Process engineers often say **MV**. Operator chrome (SWD-378) labels the horizontal analog **MV**; internal `cv` / `data-bar="co"` / write_target `co` stay CO.

### 4. MAN / AUTO / REM(CAS) are controller modes, not SP-source muxes

| Mode | Who sets SP | Who sets CO | PID algorithm |
|------|-------------|-------------|---------------|
| MAN | frozen / tracking | operator | off (`auto=false`, CO = `uman`) |
| AUTO | operator (local) | PID | on |
| CAS / REM | other loop or remote | PID | on |

Writing SP in Manual, or colouring the three modes, is contrary to both DCS faceplates and ISA-101.

On a cascade slave, the “normal” closed-loop mode is **CAS/REM** (SP from the primary CO), not local AUTO. Local AUTO on the slave breaks the cascade.

### 5. Writable-parameter emphasis is grayscale, not hue

Selected / writable analog (SP in AUTO, CO in MAN) uses outline, invert, or stronger gray fill. Colour remains caution (`warning`) and abnormal (`error`), as already implemented in SWD-366.

Click-to-set on the writable analog (and typed numeric) is standard analog-controller interaction (AVEVA: SP in Auto, OP in Manual).

## Gaps and limitations

- Full ISA-101.01 and ISA-112 PDFs are paywalled. This brief uses the public ISA hubs, the 2026 press release, the ISA112 lifecycle diagram, and practitioner libraries that claim ISA-101 alignment. Fine print (normative notes on faceplate contents) may be incomplete.
- AVEVA’s green mode buttons are **not** ISA-101; treat the *editability* rules as the signal, not the green.
- No arXiv corpus for this HMI question.
- IEC 62682 / ISA-18.2 (alarms) and IEC 61514-2 (PID performance) were not retrieved; they do not define faceplate geometry.

## Recommended reading order

1. ISA-101 series hub — what HMI standards actually cover
2. ISA 2026-02-24 ISA-112 announcement + lifecycle diagram — SCADA vs HMI split
3. AVEVA Analog Controller table — SP vs OP editability
4. DCS MAN / AUTO / CAS explainers — mode semantics
5. Prior SWD-360 brief — CO name, Bauer `auto`/`uman`, ISA-5.1 glyph

## Role in pipeline

Finding docs for `/define` and `/implement` on SWD-369. Supportive context only — not a product plan.

## Sources

- ISA, *ISA-101 Series of Standards*, https://www.isa.org/standards-and-publications/isa-standards/isa-101-standards (Formal)
- ISA, *ISA Announces Publication of New Standard for SCADA Systems*, 2026-02-24, https://www.isa.org/news-press-releases/2026/february/isa-announces-publication-of-new-standard-for-scad (Formal)
- Industrial Cyber, *ISA issues ANSI/ISA-112…*, https://industrialcyber.co/isa-iec-62443/isa-issues-ansi-isa-112-standard-to-guide-functional-architecture-models-standardize-scada-lifecycle-architecture/ (Web)
- ISA112 committee, *SCADA System Lifecycle* diagram, 2022-07-08, https://www.isa.org/getmedia/ac809e6d-27ed-4305-b207-9813b04f43b4/ISA112_SCADA-Systems_SCADA-lifecycle-diagram_rev2022-07-08.pdf (Formal)
- AVEVA, *Analog Controller* (Plant SCADA), https://docs.aveva.com/bundle/plant-scada/page/1206371.html (Informal)
- Tatsoft, *ISA-101 HMI Compliance How-to*, https://docs.tatsoft.com/display/FX/ISA-101+HMI-Compliance-How-to (Informal)
- plcprogramming.io, *High Performance HMI (ISA-101)*, https://plcprogramming.io/blog/high-performance-hmi-isa-101 (Informal)
- Casual Process Engineer, *DCS Controller Modes*, https://www.casualprocessengineer.com/Process-control/DCS-Controller-Modes (Informal)
- control.com, *Cascade Control*, https://control.com/textbook/basic-process-control-strategies/cascade-control/ (Informal)

## Tracker

- Task: SWD-369
- Artifact: docs/RESEARCH.md
- Branch: `cursor/swd-369-isa101-pid-faceplate-5304`
- PR: — (research never opens a PR)

## Next

`/define SWD-369` — lock faceplate geometry, DCS modes, and CO vs MV using this brief
