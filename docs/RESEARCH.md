# Research: Programming surface (SWD-82)

**Tracker:** [SWD-82](https://marcusknielsen.atlassian.net/browse/SWD-82)  
**Parent:** [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81) · Roadmap theme 4  
**Date:** 2026-07-27  
**Tooling:** `scripts/arxiv_research.py` (stdlib arXiv Atom client) + WebSearch / WebFetch

## Question

What do external sources say about a **programming surface** for a lab / hobby soft-PLC on Home Assistant — especially:

1. What “**easy high-level**” entry looks like for lab / non-PLC-expert users across industrial and hobby practice
2. What **escape hatches** preserve a path toward a **credible soft-PLC** (IEC-shaped depth without requiring a full IDE on day one)
3. How authoring layers relate to an already-locked **cyclic scan** runtime (SWD-85) and to **HA’s event-driven** world

Scope: inform `/define SWD-82` with evidence. This brief does **not** choose a language, layer model, or UX. A prior research/define pass for this Task was **reverted**; this pass does not reuse that brief.

## Axes covered

| Axis | Status | Notes |
|------|--------|-------|
| Preprints (arXiv) | covered | Multi-query search + ID lookup + snowball from BT / LLM-PLC / low-code seeds |
| Formal written | covered | IEC 61131-3 via PLCopen; PLCopen Software Construction Guidelines; ISA-88 / IEC 61512 as structure (not a language) |
| Web discovery | covered | Soft-PLC / OpenPLC / CODESYS / modern vPLC product surfaces; language-selection surveys |
| Informal / practitioner | covered | HA forum on ladder-on-HA; hobby soft-PLC repos; Node-RED vs PLC guidance; beginner learning paths |

## Search strategy

| Axis | Queries / targets |
|------|-------------------|
| Preprints | `behavior tree` + industrial/PLC; `IEC 61131` + language/ST/SFC/LD; OpenPLC; low-code + industrial; Node-RED + industrial; LLM + IEC 61131 graphic/ST. Lookup cores: `2404.14030`, `2403.19602`, `2401.05443`, `2410.15200`, `2410.22159`, `2512.06787`, `2509.12593`, `2504.04224`, `2212.05918`, `1303.4761`. Snowball from BT / LLM4PLC / low-code seeds. |
| Formal | [PLCopen IEC 61131-3](https://www.plcopen.org/standards/logic/iec-61131-3/); [Software Construction Guidelines](https://www.plcopen.org/guidelines/software-construction-guidelines/); ISA-88 / IEC 61512 recipe vs equipment separation |
| Web | IEC language comparison surveys; OpenPLC / Autonomy Edge; CODESYS SoftPLC; Chronax / OTee / Interkey (modern authoring pitches) |
| Informal | HA community thread on ladder/FBD-like programming; `honeytreelabs/homeautomation-plc`; `Auda29/ST_HA_Automation`; Node-RED industrial-control boundary posts; beginner LD→ST paths |

Raw JSON under `/tmp/swd82-research/` (not committed).

## Executive summary (what the sources say)

Sources do **not** converge on a single “easy high-level” authoring paradigm. They converge on a **tension**:

- Industrial practice and standards still center **IEC 61131-3 languages** (LD, FBD, ST, SFC; IL removed in edition 4.0 / 2025 per PLCopen) as the credible programming surface, usually **mixed in one project** by task type.
- “Easy” in training literature usually means **Ladder first**, then ST/FBD/SFC — not a non-IEC DSL.
- “Easy” in Industry 4.0 / robotics research often means **skill composition / behavior trees / low-code orchestration** *above* device-level FBs — still assuming a PLC-shaped runtime underneath.
- Hobby / HA-adjacent practice splits three ways: (a) **cyclic soft-PLC beside HA** with Lua/Python/config; (b) **transpile ST into HA automations** (event-driven, not scan); (c) **bridge to real PLCs**. HA community voices strongly reject treating HA itself as a PLC.

Escape hatches that preserve soft-PLC credibility, across axes, look like **access to IEC semantics or FB libraries under a scan**, not replacing the scan with flows. Flow tools (Node-RED and kin) are repeatedly positioned as **data / integration layers**, not deterministic control engines. LLM → IEC codegen is an active research assist path with validity/verification caveats — not a primary surface by itself.

Grounding already locked in-repo (SWD-85/86): authoring must sit **atop** cyclic IN → safety → control → OUT; HA remains async I/O/HMI. That constraint filters the design space but does not pick the surface.

## Key sources

| Source | Axis | ID/URL | Relevance |
|--------|------|--------|-----------|
| IEC 61131-3 via PLCopen | Formal | [plcopen.org/…/iec-61131-3](https://www.plcopen.org/standards/logic/iec-61131-3/) | Normative language suite + SFC as structuring; edition 4.0 (2025) |
| PLCopen Software Construction Guidelines | Formal | [guidelines…](https://www.plcopen.org/guidelines/software-construction-guidelines/) | Coding rules, FB libraries (Execute/Enable), SFC dos/don’ts, OOP guidance — progressive *craft*, not a different language |
| ISA-88 / IEC 61512 practice notes | Formal / web | [ISA-88 intro](https://www.symestic.com/en-us/what-is/isa-88); industrial implementer guides | Recipe/procedure vs equipment separation = config-level “easy” without inventing a PLC language |
| Sidorenko et al. — BTs in industrial controllers | Preprint | [2404.14030](https://arxiv.org/abs/2404.14030) | BTs as modular coordination *integrated into* 61131/61499; separates device FBs from frequently changing logic |
| BT industrial case study | Preprint | [2403.19602](https://arxiv.org/abs/2403.19602) | Few published industrial BT successes; modularity vs FSM claimed |
| LLM4PLC | Preprint (+ DOI) | [2401.05443](https://arxiv.org/abs/2401.05443) | LLMs need verification/feedback to produce valid PLC programs |
| LLM ST / graphic / SFC generation | Preprint | [2410.22159](https://arxiv.org/abs/2410.22159), [2410.15200](https://arxiv.org/abs/2410.15200), [2512.06787](https://arxiv.org/abs/2512.06787) | Assistive codegen across IEC surfaces; graphic/SFC harder than ST |
| Low-code open factory automation (Siemens/Berkeley) | Preprint | [2504.04224](https://arxiv.org/abs/2504.04224) | Low-code + coordination/safety; leans 61499 / Lingua Franca — adjacent ambition, different runtime story than our 61131-shaped scan |
| Complexity of graphical vs textual IEC | Preprint (+ DOI) | [2212.05918](https://arxiv.org/abs/2212.05918) | Measuring understandability cost of IEC units — relevant to “easy vs deep” |
| 61131 vs 61499 | Preprint (+ DOI) | [1303.4761](https://arxiv.org/abs/1303.4761) | Why cyclic 61131 remains industrial default (already used in SWD-85) |
| OpenPLC / Autonomy Edge | Web / informal | [autonomylogic.com docs](https://autonomylogic.com/docs); archived OpenPLC Editor notes | Soft-PLC peer: full IEC language editor as the product surface |
| CODESYS SoftPLC language suite | Web / informal | vendor SoftPLC summaries | Complete IEC editors + reusable FBs as commercial soft-PLC norm |
| Node-RED vs PLC control | Informal | Robustel industrial posts; hardloop PID README | Flows OK for data; not a substitute for cyclic deterministic control |
| HA forum: ladder on HA | Informal | [community thread](https://community.home-assistant.io/t/integration-of-ladder-programming-or-functional-plan-similar-step7/620120) | Event-driven HA ≠ PLC scan; users want organization, maintainers reject PLC emulation of core |
| homeautomation-plc | Informal | [honeytreelabs/…](https://github.com/honeytreelabs/homeautomation-plc) | Cyclic soft-PLC on Embedded Linux; YAML config + Lua/C++; IEC interpreter aspirational |
| ST → HA automations | Informal | [Auda29/ST_HA_Automation](https://github.com/Auda29/ST_HA_Automation) | ST *syntax* over HA event model — opposite of soft-PLC-beside-HA |
| Beginner LD → ST paths | Informal | industrial training blogs / exercise progressions | “Easy” = LD + scan mental model first; ST as power path |

## Themes and trends

### 1. “Easy high-level” is overloaded

Sources use the phrase for at least five different things:

| Sense of “easy” | Typical surface | Soft-PLC credibility |
|-----------------|-----------------|----------------------|
| Visual Boolean / electrician mental model | LD | High (is IEC) |
| Wire continuous loops from libraries | FBD + FB params | High |
| Step / mode sequences | SFC (plus ST/LD actions) | High |
| Parameterize / recipe without rewriting logic | ISA-88-style recipes, FB instances, YAML config | Medium–high if FBs are IEC-shaped under a scan |
| Compose skills / tasks without device code | Behavior trees, skill SOA | Research / niche; needs PLC integration story |
| Event flows / mashups | Node-RED, HA automations | Low as *control* engine (sources warn) |
| Natural language → program | LLM assist | Assist only; validity gated |

Define must pick which sense(s) PLCAssistant means — sources do not settle it.

### 2. Credible soft-PLC surfaces still look like IEC (or FB libraries on a scan)

OpenPLC/CODESYS/Autonomy-style peers treat **multi-language IEC editors** as the programming product. PLCopen’s progressive story is **better structure and reusable FBs** (libraries, SFC structuring, naming/coding rules, optional OOP), not abandoning 61131. Escape hatches cited in practice: **ST for algorithms**, **user FB libraries**, **SFC for sequences**, **OOP extensions** — still inside the standard.

### 3. High-level composition research assumes a PLC underneath

Behavior-tree work for industrial controllers ([2404.14030](https://arxiv.org/abs/2404.14030)) explicitly integrates BTs **with** IEC 61131 / 61499 and PLCopen Common Behavior Model FBs: device skills stay low-level; BTs coordinate. That is evidence for *optional* high-level orchestration — **not** evidence that BTs replace LD/ST/FBD as the only surface, and industrial case literature remains thin ([2403.19602](https://arxiv.org/abs/2403.19602)).

### 4. Config / recipe layer is a real “easy” path in process industries

ISA-88 separates **procedural / recipe** content from **equipment control**. Operators change formulas and phase parameters without rewriting PLC code; phases still run on IEC-shaped modules. For a lab wedge with fixed cascade + modes, a **parameterized default program** (tune gains, SPs, trip limits; optional sequence params) is a documented industrial pattern — orthogonal to inventing a new language.

### 5. Soft-PLC ≠ HA automations (practitioner consensus)

HA forum consensus: HA is **event-driven**; PLC is **cyclic evaluate**. Emulating ladder *inside* HA fights the platform. Hobby soft-PLCs that feel PLC-like keep a **scan loop** and treat MQTT/HA as I/O. Transpiling ST *into* HA automations reuses ST syntax but **drops** cyclic semantics. This aligns with SWD-85’s HA↔cyclic boundary — authoring should target the Soft-PLC artifact, not HA YAML as the program of record.

### 6. Flow / low-code tools are popular and category-confused

Node-RED (and Node-RED-based industrial shells) excel at integration and dashboards. Practitioner and vendor guidance: do **not** use them as the deterministic control path. Siemens/Berkeley low-code work ([2504.04224](https://arxiv.org/abs/2504.04224)) explores robust low-code with explicit coordination (Lingua Franca / 61499) — interesting for packaging later, but it pulls toward **event-driven** distribution that SWD-85 already deprioritized vs cyclic 61131.

### 7. LLM assist is rising, verification is the gate

Recent papers train or constrain LLMs for ST, LD→SFC, graphic languages, and SFC generation. Common finding: raw generation is brittle; **compiler / verifier feedback** matters ([2401.05443](https://arxiv.org/abs/2401.05443)). Treat as optional assist over a chosen artifact format — not as the definition of the surface.

### 8. Progressive depth in training ≠ a product layer cake

Industry pedagogy progresses **LD → timers/counters/state → ST/FBD/SFC**. That is a **learning path**, not a requirement that the product ship four locked abstraction layers on day one. Prior art products often expose **multiple editors on one project** rather than a strict L0/L1/L2 ladder.

## Gaps and limitations

- Almost no peer-reviewed work on **Home Assistant + soft-PLC authoring** as a combined product; HA evidence is forum + hobby repos.
- “Lab / hobby user” personas are under-studied in IEC literature (written for plant/machine engineers).
- Behavior-tree industrial adoption evidence is sparse beyond proposals and isolated case studies.
- Soft-PLC *feel* of authoring (online monitoring, force, cross-reference) is product UX, barely covered in papers.
- Snowball from author names on BT/LLM seeds was noisy (many off-topic math hits); triage was hand-filtered.
- Modern commercial pitches (Chronax text+AI, OTee vPLC browser ST, Interkey NL→IEC) are marketing-heavy; treat as signals of market interest, not validated designs.
- This brief intentionally **does not** prescribe progressive L0–L3 layers or a primary L1 paradigm — those are define questions (and were part of a reverted prior pass).

## Recommended reading order

1. PLCopen [IEC 61131-3 page](https://www.plcopen.org/standards/logic/iec-61131-3/) + [Software Construction Guidelines overview](https://www.plcopen.org/guidelines/software-construction-guidelines/) — normative surface + progressive craft  
2. Repo locks: `docs/control/04-ha-cyclic-boundary.md`, wedge `03`/`04` — what authoring must not break  
3. [2404.14030](https://arxiv.org/abs/2404.14030) — high-level composition *on* PLC (one option among many)  
4. HA community [ladder thread](https://community.home-assistant.io/t/integration-of-ladder-programming-or-functional-plan-similar-step7/620120) + [homeautomation-plc](https://github.com/honeytreelabs/homeautomation-plc) — Soft-PLC ≠ HA  
5. Node-RED industrial-control boundary posts — why flows ≠ scan  
6. [2401.05443](https://arxiv.org/abs/2401.05443) / [2410.15200](https://arxiv.org/abs/2410.15200) — only if considering LLM assist  
7. ISA-88 overview — only if considering recipe/config-first “easy”  

## Role in pipeline

Supportive context for `/define SWD-82`. Does **not** settle user alignment.

Particulars for define that remain open (non-exhaustive):

- Which sense of “easy high-level” is in-scope for the lab wedge v1?
- Is the first artifact **config of a fixed wedge program**, an **IEC subset**, a **custom DSL**, **BT/skill composition**, or something else?
- What escape hatch is required for “credible soft-PLC” in v1 vs later (ST? LD? FB library? full OpenPLC-class IDE)?
- Where does the program-of-record live (Add-on files, git, HA config) — packaging touchpoint with SWD-84?
- Non-goals: full commercial IDE parity; HA-automation-as-PLC; SIL authoring; requiring LLM?

## Sources

### Preprints (arXiv)

- [2404.14030](https://arxiv.org/abs/2404.14030) — Towards Using Behavior Trees in Industrial Automation Controllers  
- [2403.19602](https://arxiv.org/abs/2403.19602) — Behavior Trees in Industrial Applications: Case Study  
- [2401.05443](https://arxiv.org/abs/2401.05443) — LLM4PLC (DOI 10.1145/3639477.3639743)  
- [2410.15200](https://arxiv.org/abs/2410.15200) — LLM support for IEC 61131-3 graphic languages (DOI 10.1109/INDIN58382.2024.10774464)  
- [2410.22159](https://arxiv.org/abs/2410.22159) — Training LLMs for ST with online feedback  
- [2512.06787](https://arxiv.org/abs/2512.06787) — LLM4SFC  
- [2509.12593](https://arxiv.org/abs/2509.12593) — LD→SFC via LLM (DOI 10.1109/ETFA65518.2025.11205542)  
- [2504.04224](https://arxiv.org/abs/2504.04224) — Robustness & safety in low-code factory automation  
- [2212.05918](https://arxiv.org/abs/2212.05918) — Complexity of graphical and textual IEC 61131-3 (DOI 10.1109/LRA.2021.3084886)  
- [1303.4761](https://arxiv.org/abs/1303.4761) — IEC 61499 vs 61131 (DOI 10.4236/jsea.2013.68050)  
- Related runtime anchors (from prior SWD-85 pass, still relevant): [2607.10499](https://arxiv.org/abs/2607.10499), [2606.15461](https://arxiv.org/abs/2606.15461), [2202.04076](https://arxiv.org/abs/2202.04076)

### Formal / standards

- PLCopen — IEC 61131-3 overview (edition 4.0 – 2025): https://www.plcopen.org/standards/logic/iec-61131-3/  
- PLCopen Software Construction Guidelines: https://www.plcopen.org/guidelines/software-construction-guidelines/  
- ISA-88 / IEC 61512 models (recipe vs equipment) — secondary summaries cited above  

### Web / informal

- OpenPLC / Autonomy Edge docs: https://autonomylogic.com/docs  
- Archived OpenPLC Editor language list (historical): https://openplcproject.gitlab.io/openplc-editor/  
- HA community thread: https://community.home-assistant.io/t/integration-of-ladder-programming-or-functional-plan-similar-step7/620120  
- honeytreelabs/homeautomation-plc: https://github.com/honeytreelabs/homeautomation-plc  
- Auda29/ST_HA_Automation: https://github.com/Auda29/ST_HA_Automation  
- Node-RED vs industrial control (Robustel): https://robustel.com/can-node-red-support-industrial-control-edge-gateway-recommendation/  
- IEC language comparison surveys (instrumentationblog.in, feelautom.fr, industrialmonitordirect.com)  

### Repo grounding

- `docs/ROADMAP.md`, `docs/control/*`, `docs/wedge/03-control-story.md`, `docs/wedge/08-packaging-sketch.md` (deep authoring deferred to SWD-82)

## Tracker

- Task [SWD-82](https://marcusknielsen.atlassian.net/browse/SWD-82) remains **To Do** (research does not advance status).
- Artifact: this `docs/RESEARCH.md` (replaces SWD-85 research content on this path for the active theme).
- Prior incorrect research/define for SWD-82 was reverted (PRs #20/#21); this brief is a fresh multi-axis pass.

## Next

`/define SWD-82` — Probe user on which “easy” sense and which escape hatches belong in v1; research brief is supportive context only
