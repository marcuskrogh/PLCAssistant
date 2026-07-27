# Research: Control semantics (SWD-85)

**Tracker:** [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85)  
**Parent:** [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81) · Roadmap theme 3  
**Date:** 2026-07-26  
**Tooling:** `scripts/arxiv_research.py` (stdlib arXiv Atom client)

## Question

What must “PLC-like” **control semantics** mean for PLCAssistant (lab / hobby soft-PLC on Home Assistant) — especially:

1. Must-have loops, feedback, and timing for a soft-PLC *feeling*
2. What “safety” means at this ambition (not SIL / certified safety PLC)
3. How HA’s event-driven world should interact with PLC cyclic expectations

Scope: inform `/define SWD-85` without locking runtime packaging (SWD-84) or programming surface (SWD-82).

## Strategy

| Step | What |
|------|------|
| Seed queries | soft/software PLC; IEC 61131 + scan/cyclic; programmable-logic runtime; industrial automation controllers / behavior trees; OpenPLC |
| Lookup cores | Formal ST/LD/SFC semantics, 61131 vs 61499, scan-cycle timing, OpenPLC security, cascade PID safety |
| Snowball | Authors/categories from cores (noisy — many physics/PLC=power-line false positives; hand-filtered) |
| Triage | Keep IEC 61131-3 / OpenPLC / scan-cycle / cascade control; drop power-line comms, HEP, generic LLM codegen unless PLC-runtime relevant |
| Grounding | Cross-check against wedge control/safety stories (`docs/wedge/03`, `04`) and I/O image (`docs/io/`) |

Raw JSON under `/tmp/swd85-research/` (not committed).

## Summary (answers for define)

### Must-have soft-PLC semantics

Literature and prior art converge on a **cyclic scan model** as the distinctive PLC runtime contract, not event callbacks:

1. **Scan cycle** — read inputs → evaluate logic → write outputs, repeatedly, with a notion of cycle time / retentive state across scans ([K-ESBMC](https://arxiv.org/abs/2607.10499), [ESBMC-PLC](https://arxiv.org/abs/2606.15461), [Scanning the Cycle](https://arxiv.org/abs/2102.08985)).
2. **Deterministic I/O image** — logic sees a frozen input image for the scan; outputs commit at end of scan (already aligned with SWD-86).
3. **Continuous control as FB-like blocks** — cascade PI(D) with clamps / anti-windup; literature treats cascade gain tuning and stability as first-class ([Safety-Aware Cascade Tuning](https://arxiv.org/abs/2010.15211)); wedge already requires directional cascade, not certified tuning.
4. **Discrete orchestration** — modes, permissives, latched trips (wedge `STOP`/`RUNNING`/`TRIPPED`) map cleanly to SFC-style sequential structure or simple state machines; formal SFC work ([Coq SFC](https://arxiv.org/abs/1301.3047), [CERTPLC](https://arxiv.org/abs/1102.3529)) shows why latch/reset semantics need an explicit model.
5. **Timers / edges as scan-relative** — TON/TOF/edge detection defined in scan ticks or wall-clock sampled once per scan (LD formalizations in K-ESBMC).

**IEC 61499 event-driven FBs** are a research alternative for distributed CPS ([61131 vs 61499](https://arxiv.org/abs/1303.4761)); industry still centers **61131 cyclic**. For HA adjacency, prefer **cyclic soft-PLC core** with HA as I/O/HMI bus — not adopting 61499 as the primary mental model.

**Behavior trees** ([BT in industrial controllers](https://arxiv.org/abs/2404.14030)) are a useful *programming-surface* idea for modularity (SWD-82), not a substitute for the scan contract.

### Safety at this ambition

Academic “safety” for PLCs usually means **formal verification of LD/ST/SFC** or security of soft-PLC stacks ([OpenPLC issues](https://arxiv.org/abs/2509.22664)), not SIL certification.

For PLCAssistant v1 (already locked in wedge safety story):

| Keep | Defer |
|------|-------|
| Latched trips, Start permissives, immediate stop CV | SIL / certified safety PLC / dual-channel |
| Trip on non-GOOD PV (LOS) using SWD-86 quality | Formal model checking of user programs |
| Safety evaluated **every scan**, before/overriding continuous control | Rich bypass/audit frameworks |
| Illustrative “middle-ground” semantics | Claiming IEC 61508/62061 compliance |

OpenPLC security work is a reminder: soft-PLC on commodity hosts needs basic isolation/auth later (packaging / SWD-84), but is out of control-semantics define scope.

### HA event-driven vs PLC cyclic

| Layer | Role |
|-------|------|
| HA | Entity state changes, services, dashboards — **asynchronous** |
| Thin integration (SWD-86) | Sample/declare bindings; mock entities |
| Soft-PLC runtime | Own the **scan clock**; build I/O image each cycle; run cascade + safety; flush OUT |

Practical contract for define:

- HA events **update a sample buffer**; they do **not** directly execute control logic mid-scan.
- Scan period is configurable; undersampling / stale samples → `UNCERTAIN`/`BAD` (existing quality model), not ad-hoc event handlers.
- OUT writes every scan (SWD-86) so HA actuators see PLC-paced commands even when PVs are quiet.
- Optional future: “scan overrun” / jitter diagnostics for hobby credibility — not SIL timing guarantees.

## Key papers

| arXiv | Title | Why it matters |
|-------|-------|----------------|
| [2607.10499](https://arxiv.org/abs/2607.10499) | K-ESBMC: Executable formal semantics of IEC 61131-3 LD | Scan-for-scan oracle vs OpenPLC/Matiec; retentive scan cycle, timers, edges |
| [2606.15461](https://arxiv.org/abs/2606.15461) | ESBMC-PLC | Models PLC scan as `while(true)` + nondeterministic inputs — crisp runtime picture |
| [2202.04076](https://arxiv.org/abs/2202.04076) | K-ST | Formal ST semantics from IEC 61131-3 + vendor manuals |
| [1301.3047](https://arxiv.org/abs/1301.3047) | Coq semantics for PLC (SFC/IL/LD/FBD) | Multi-language top-level control-flow; latch/sequence thinking |
| [1303.4761](https://arxiv.org/abs/1303.4761) | IEC 61499 vs 61131 | Why cyclic 61131 remains the industrial default vs event FBs |
| [2102.08985](https://arxiv.org/abs/2102.08985) | Scanning the Cycle | Scan cycle as observable PLC fingerprint — timing is part of the product feel |
| [2010.15211](https://arxiv.org/abs/2010.15211) | Safety-aware cascade PID tuning | Cascade + constraints; tuning ≠ safety interlocks |
| [2404.14030](https://arxiv.org/abs/2404.14030) | Behavior trees in industrial controllers | Modular high-level control — feed SWD-82, not scan replacement |
| [2509.22664](https://arxiv.org/abs/2509.22664) | OpenPLC security issues | Soft-PLC on Pi/PC: trust boundary / packaging caution |
| [2504.04224](https://arxiv.org/abs/2504.04224) | Robustness & safety in low-code factory automation | Adjacent “approachable industrial” ambition without overclaiming SIL |

## Themes

1. **Scan is the product metaphor** — users expect cyclic evaluate + I/O image, not pure HA automations.
2. **61131-shaped, not 61499-first** — keep cyclic core; event distribution stays HA’s job.
3. **Separate “process safety interlocks” from “formal/verified PLC”** — wedge latch/LOS is enough for SWD-85 define.
4. **Cascade PID is continuous FB semantics inside the scan** — clamps, anti-windup, bumpless; quantitative autotune optional later.
5. **OpenPLC/Matiec as reference peers** — useful for behavioral comparison, not a required dependency.
6. **Programming surface ≠ semantics** — BTs / ST / high-level DSL can sit atop the same scan + FB contract (SWD-82).

## Gaps

- Little peer-reviewed work on **Home Assistant ↔ soft-PLC** bridging; design must be original, guided by PLC scan + HA entity realities (SWD-86).
- Soft-PLC *feel* timing (jitter, overrun UX) under-specified in papers aimed at ICS security or formal methods.
- Cascade tuning literature assumes plants/labs richer than our mock skid — define should set **demo-grade** timing/gains, not research autotune.
- No need to adopt full IEC language semantics now; formal papers are **conceptual anchors**, not implementation mandates.

## Suggested reading order

1. [1303.4761](https://arxiv.org/abs/1303.4761) — frame 61131 vs 61499  
2. [2606.15461](https://arxiv.org/abs/2606.15461) / [2607.10499](https://arxiv.org/abs/2607.10499) — scan-cycle mental model (+ OpenPLC alignment)  
3. Wedge `03-control-story.md` + `04-safety-story.md` — product constraints already locked  
4. [2010.15211](https://arxiv.org/abs/2010.15211) — cascade continuous-control expectations  
5. [2404.14030](https://arxiv.org/abs/2404.14030) — only if jumping ahead to SWD-82  
6. [2509.22664](https://arxiv.org/abs/2509.22664) — packaging/threat note for SWD-84  

## Implications for `/define SWD-85`

Draft define should lock (conceptually, not necessarily code):

- **Scan scheduler** contract (period, order: IN → safety → control → OUT)
- **Mode / permissive / trip** evaluation relative to continuous loops
- **PID/FB minimum semantics** for cascade (sample time = scan or explicit `Ts`, clamps, anti-windup, bumpless init)
- **Safety precedence** every scan; interaction with non-GOOD quality (already in wedge)
- Explicit **non-goals**: SIL, full IEC language runtime, 61499 distribution, HA-automation-as-PLC

## Sources

- arXiv Atom API via `scripts/arxiv_research.py`
- Repo: `docs/ROADMAP.md`, `docs/wedge/03-control-story.md`, `docs/wedge/04-safety-story.md`, `docs/io/`

## Tracker

- Task [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85) is **In Review** (review-fix CLEAN); research artifact is this doc; definition is `docs/PLAN.md`.
- Story [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81) Next → `/ship SWD-85`.

## Next

`/ship SWD-85` — merge implement PR #18
