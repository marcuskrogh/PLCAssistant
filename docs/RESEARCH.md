# Research brief: Soft-PLC architectures for IEC 61131-style control over entity/IoT I/O

## Question

For **PLCAssistant** (Task [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70)), which architecture best matches “virtual PLC” behaviour when **Home Assistant entities** are the field I/O?

Candidate approaches from the roadmap:

1. **Soft-PLC sidecar** (OpenPLC-class runtime + HA entity I/O driver)
2. **In-HA soft runtime** (scan cycle inside Home Assistant / addon process)
3. **ST→automation transpile** (IEC language → event-driven HA automations)
4. **Hybrid** (scan-cycle runtime + HA as cyber/IoT fabric)

Secondary questions: how literature treats **cyclic scan vs event-driven** execution (IEC 61131 vs 61499), and what that implies for determinism and packaging.

## Search strategy

**Corpus:** arXiv Atom API via `scripts/arxiv_research.py` (primary host used: `https://arxiv.org/api/query`; `export.arxiv.org` returned persistent 503 during this run).

**Planned complementary queries:**

| # | Intent | Query |
|---|--------|-------|
| 1 | Broad IEC 61131 | `all:"IEC 61131"` |
| 2 | Soft/virtual PLC | `all:"soft PLC" OR all:"software PLC" OR all:"virtual PLC" OR all:softPLC` |
| 3 | OpenPLC / Modbus runtime | `all:OpenPLC OR (all:PLC AND all:Modbus AND all:runtime)` |
| 4 | PLC + IoT / CPS / SCADA (2018–2026) | `all:(PLC AND (IoT OR "home automation" OR "smart home" OR "cyber-physical" OR SCADA)) AND submittedDate:[201801010000 TO 202612312359]` |

**Executed successfully:** Query 1 — `total_results=42`, fetched 25 (`docs/research/arxiv_swd70_iec61131_search.json`).

**Blocked by arXiv rate limits (429/503) after the first successful page:** Queries 2–4 and follow-up `lookup`/`snowball` calls. Soft-PLC / OpenPLC coverage in this brief is therefore limited to papers that also matched the IEC 61131 query (notably OpenPLC appears in [2607.08550](https://arxiv.org/abs/2607.08550)).

**Coverage honesty:** arXiv is preprint-heavy; industrial automation also lives in IEEE/IFAC venues underrepresented here. No retrieved paper discusses Home Assistant specifically.

## Executive summary

arXiv literature on PLC software strongly anchors on **IEC 61131-3** languages and an **abstract scan-cycle** execution model (inputs → logic → outputs). Formal semantics, verification, and code synthesis work all assume that cyclic PLC behaviour ([1009.0817](https://arxiv.org/abs/1009.0817), [1301.3047](https://arxiv.org/abs/1301.3047), [1912.10629](https://arxiv.org/abs/1912.10629), [2607.08550](https://arxiv.org/abs/2607.08550)).

The main **paradigm fork** in the literature is **IEC 61131 (cyclic / widely deployed)** vs **IEC 61499 (event-driven / academically promoted)**. Thramboulidis ([1303.4761](https://arxiv.org/abs/1303.4761)) argues that 61499’s claimed advantages (including event-driven execution) are oversold and that 61131 remains the industrial baseline—directly relevant to whether PLCAssistant should emulate a scan cycle or transpile to HA’s event automations.

A second theme is **PLCs as one layer in a cyber-physical / IoT system**, not the whole stack: SysML/UML + IoT as the glue for cyber interfaces ([1402.3920](https://arxiv.org/abs/1402.3920), [1407.2077](https://arxiv.org/abs/1407.2077)). That maps cleanly to “HA owns devices/entities; soft-PLC owns control logic.”

**Open soft-PLCs** (OpenPLC and related open-hardware controllers) are treated as real IEC 61131-3 targets in recent verification work ([2607.08550](https://arxiv.org/abs/2607.08550)), which also stresses that **scan-cycle models diverge from physical I/O** (ADC resolution, word width)—a warning for binding non-real-time HA entities as “inputs.”

**Implication for SWD-70:** Prefer an architecture that **preserves IEC 61131 scan semantics** (sidecar OpenPLC-class or in-process soft runtime) over pure ST→HA-automation transpile if the goal is “all the capabilities of a PLC.” Treat HA as the **IoT/cyber I/O fabric** (CPS papers), with explicit non-goals on hard real-time. Event-driven transpile remains a lighter alternative but is a **different paradigm** (closer to 61499-style thinking than classic PLC scan).

## Key papers

### Core (architecture / semantics)

| arXiv | Why it matters for SWD-70 |
|-------|---------------------------|
| [1303.4761](https://arxiv.org/abs/1303.4761) | 61131 vs 61499: cyclic industrial baseline vs event-driven academic push; challenges “event-driven = next gen” claims |
| [1402.3920](https://arxiv.org/abs/1402.3920) | PLC (61131) + higher abstraction (SysML/UML) + **IoT as integration technology** for cyber/cyber-physical parts |
| [1407.2077](https://arxiv.org/abs/1407.2077) | CPS development: PLC **or** embedded board targets; IoT as cyber-interface glue—supports “HA entities as I/O” framing |
| [2607.08550](https://arxiv.org/abs/2607.08550) | **OpenPLC** and open-hardware PLCs as IEC 61131-3 platforms; verification over **scan-cycle** model vs hardware-faithful I/O |
| [1009.0817](https://arxiv.org/abs/1009.0817) | Formal SFC→BIP transform; invariant-preserving PLC semantics |
| [1301.3047](https://arxiv.org/abs/1301.3047) | Coq formalization of SFC/IL/LD/FBD and relations between languages |
| [1912.10629](https://arxiv.org/abs/1912.10629) | Ladder as I→logic→O; scan-oriented PLC program shape for verification |
| [2404.14030](https://arxiv.org/abs/2404.14030) | Behavior Trees for modular coordination **on** PLCs (61131 and 61499 strategies)—flexibility without abandoning controllers |
| [2202.10075](https://arxiv.org/abs/2202.10075) | Native IEC 61131-3 as the execution substrate (even for ML inference)—shows value of staying *on* the PLC language/runtime |
| [1405.2409](https://arxiv.org/abs/1405.2409) | Spec→**Structured Text** synthesis for real PLC targets—ST as portable textual PLC language |
| [2410.22159](https://arxiv.org/abs/2410.22159) | ST generation with compiler feedback—ST remains central engineering language |
| [2108.09753](https://arxiv.org/abs/2108.09753) | aPS controlled by PLC/61131 POUs; clone/variability realities of industrial control software |

### Supporting (from same search page)

LLM-assisted LD/ST/SFC work ([2410.15200](https://arxiv.org/abs/2410.15200), [2509.12593](https://arxiv.org/abs/2509.12593), [2311.10401](https://arxiv.org/abs/2311.10401)); verification tooling ([2606.23870](https://arxiv.org/abs/2606.23870), [2606.15461](https://arxiv.org/abs/2607.10499)); complexity metrics ([2212.05918](https://arxiv.org/abs/2212.05918)); MDE ([2212.06607](https://arxiv.org/abs/2212.06607)); smart-grid cyber ranges with PLC-like assets ([2404.00869](https://arxiv.org/abs/2404.00869), [2509.10568](https://arxiv.org/abs/2509.10568)).

## Themes and trends

1. **Scan cycle is the semantic heart of “PLC.”** Verification and formalization papers repeatedly use an abstract scan-cycle model ([2607.08550](https://arxiv.org/abs/2607.08550), [1912.10629](https://arxiv.org/abs/1912.10629)). An architecture that only fires on HA state-change events is not the same object class.

2. **Event-driven ≠ drop-in upgrade.** IEC 61499’s event-driven story is contested ([1303.4761](https://arxiv.org/abs/1303.4761)). Mapping ST to HA automations inherits event-driven tradeoffs (ordering, timers, re-entrancy) rather than PLC scan guarantees.

3. **Separate concerns: devices/IoT fabric vs control runtime.** CPS papers place IoT at cyber interfaces and keep PLC (or embedded) for control ([1402.3920](https://arxiv.org/abs/1402.3920), [1407.2077](https://arxiv.org/abs/1407.2077))—aligns with HA entities as I/O + soft-PLC for logic.

4. **Open soft-PLCs are legitimate 61131 targets.** OpenPLC appears as a first-class open-hardware PLC platform in 2026 verification work ([2607.08550](https://arxiv.org/abs/2607.08550)), supporting a **sidecar soft-PLC** option for PLCAssistant.

5. **I/O fidelity matters.** Hardware-faithful input models discard unrealizable sensor values ([2607.08550](https://arxiv.org/abs/2607.08550)). HA entities (wireless, cloud, polling) need **availability/freshness/fail-safe** policies—not pretence of industrial I/O timing.

6. **ST (and LD) remain the engineering lingua franca** for generation and tooling ([1405.2409](https://arxiv.org/abs/1405.2409), [2410.22159](https://arxiv.org/abs/2410.22159)).

## Gaps and limitations

- **Rate limits** prevented soft-PLC / OpenPLC / PLC+IoT dedicated queries and snowball expansion; OpenPLC evidence is incidental via the IEC 61131 hit list.
- **No Home Assistant / consumer smart-home entity bus** papers in the retrieved set.
- **Little quantitative comparison** of soft-PLC scan latency vs event-driven home automation stacks on commodity hosts.
- Preprint corpus; peer-review status varies (`journal_ref` sparse in this sample).
- Product packaging (HACS vs HAOS addon) is out of scope for arXiv.

## Architecture implications (for `/define SWD-70`)

| Approach | Literature fit | Fit to PLCAssistant goals |
|----------|----------------|---------------------------|
| Soft-PLC sidecar (OpenPLC-class) + HA I/O driver | Strong: OpenPLC as 61131 target ([2607.08550](https://arxiv.org/abs/2607.08550)); CPS/IoT as fabric ([1407.2077](https://arxiv.org/abs/1407.2077)) | Strong for “real PLC” semantics; clear process boundary |
| In-HA soft runtime (scan in addon/integration) | Compatible with scan semantics; less direct precedent | Good UX packaging; must still implement scan + timers honestly |
| ST→HA automation transpile | Weak as *PLC* substitute: event-driven paradigm closer to contested 61499 story ([1303.4761](https://arxiv.org/abs/1303.4761)) | Fast to ship language feel; weak on scan/interlock semantics |
| Hybrid (scan runtime + HA fabric + optional BT/coordination) | Supported: modular coordination *on* PLC ([2404.14030](https://arxiv.org/abs/2404.14030)); CPS split ([1402.3920](https://arxiv.org/abs/1402.3920)) | Best long-term shape if phased |

**Working recommendation (evidence-based, not a final product decision):**  
Adopt **scan-cycle soft-PLC semantics** with **HA entities as a constrained I/O HAL** (freshness, range, fail-safe). Prefer **OpenPLC-class sidecar or equivalent in-process runtime** over transpile-only. Document non-goals: hard real-time, safety certification. Treat transpile as optional *authoring aid*, not the runtime.

## Recommended reading order

1. [1303.4761](https://arxiv.org/abs/1303.4761) — 61131 vs 61499 paradigm stakes  
2. [2607.08550](https://arxiv.org/abs/2607.08550) — OpenPLC / scan-cycle / hardware I/O gap  
3. [1407.2077](https://arxiv.org/abs/1407.2077) / [1402.3920](https://arxiv.org/abs/1402.3920) — CPS + IoT fabric around PLCs  
4. [1301.3047](https://arxiv.org/abs/1301.3047) / [1009.0817](https://arxiv.org/abs/1009.0817) — what “PLC semantics” formally means  
5. [2404.14030](https://arxiv.org/abs/2404.14030) — modular coordination without abandoning PLC  
6. [1405.2409](https://arxiv.org/abs/1405.2409) / [2410.22159](https://arxiv.org/abs/2410.22159) — ST as portable engineering language  

## Sources

Raw search JSON: `docs/research/arxiv_swd70_iec61131_search.json`  
Triage split: `docs/research/arxiv_swd70_triage.json`  

All claims above trace to abstracts/metadata in those files (arXiv IDs as cited). No papers outside the successful Query 1 result set were cited.

## Tracker

- Task: [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70)
- Artifact: `docs/RESEARCH.md`
- Story: [SWD-66](https://marcusknielsen.atlassian.net/browse/SWD-66)

## Next

`/define SWD-70` — Lock architecture (scan soft-PLC + HA I/O HAL vs alternatives) using this brief as input.
