# Research brief: Standards and scientific backing for implemented PLC blocks, model unit-ops, and the example skid

**Tracker:** [SWD-384](https://marcusknielsen.atlassian.net/browse/SWD-384)  
**Date:** 2026-08-18  
**Tooling:** `scripts/arxiv_research.py` + WebSearch / WebFetch (four axes)

This brief is a **validation of what is already shipped**. It does not decide product, UX, or acceptance. Citations stay in this document. They are **not** to be copied into the App, Lovelace cards, or backend runtime.

---

## Question

Do the **currently implemented** Soft-PLC blocks, plant-model unit-ops, and the example one-tank recycled skid:

1. **Conform** to available industrial standards (where a standard actually governs the item)
2. Have **scientific / textbook / peer-reviewed** backing for the mathematics
3. Where they **diverge**, is that an honest product choice, a simplification, or a gap

Inventory under test (code, not aspiration):

| Layer | What exists today |
|-------|-------------------|
| **PLC library** | One builtin `PID` template (`plcassistant.surface.builtin`, `plcassistant.control.pid`) |
| **Scan** | `IN → SAFETY → CONTROL → OUT` (`plcassistant.control.scan`) |
| **SP path** | Faceplate setpoint rate limiter (`plcassistant.control.ramp`) |
| **Example PLC program** | Two PID copies `level_pi` (LIC) → `flow_pi` (FIC) → `CMD_SPEED` |
| **Safety (not library FBs)** | HH tank, LL reservoir, LOS latch, reset-to-STOP, Start permissives, Stop always (`plcassistant.wedge.safety`) |
| **Model unit-ops** | `tank`, `pump`, `orifice`, `lag`, `custom_ode` (`custom_components/plcassistant/dynamics/ops.py`) |
| **Example plant** | Closed recycle reservoir ↔ process tank; presets `skid` / `skid_composed` |

Verdict vocabulary used below: **conform** / **partial** / **diverge** / **not-in-scope**. Paywalled full standards are marked; clause numbers are **not** invented.

## Axes covered

| Axis | Status | Notes |
|------|--------|-------|
| Preprints (arXiv) | covered | Multi-query `arxiv_research.py`; core hit is Lund incremental-PID line (arXiv:2604.15918) plus Torricelli drain papers. Empty on pump affinity, inventory limiter, scan order, SP ramp. |
| Formal written | covered | ISA-TR5.9 InTech excerpt; Sundström et al. IFAC 2024 open post-print; IEC 61131-3 secondary overviews; OPC UA StatusCode; IEC 61508/61511 public overviews; Kantor / Skogestad tank notes. Full ISA-TR5.9, IEC 61131-3, IEC 61511 texts remain paywalled. |
| Web discovery | covered | ISA hubs, IronPLC scan cycle, cascade tutorials, Engineering ToolBox affinity, Siemens SP ramp docs. |
| Informal / practitioner | covered | Siemens FB41, Rockwell PIDE/PPID, Emerson DeltaV, ABB CtrlPidParallel, trip/permissive primers, Modelica OpenTank. **Always labeled informal.** |

## Search strategy

| Axis | Queries / targets |
|------|-------------------|
| Preprints | Incremental PID discretization; cascade tank level/flow; Torricelli orifice drain; anti-windup PID; first-order lag discrete; pump affinity (no useful hits) |
| Formal | ISA-TR5.9 InTech; doi:10.1016/j.ifacol.2024.08.090 + Lund post-print; ISA-5.1 series page; IEC 61131-3 public overviews; OPC UA Part 8 §7.3; IEC 61508/61511 overviews; Kantor CBE30338 gravity-drained tank |
| Web | Cascade LIC→FIC; Torricelli; Skogestad Ch. 11 volume balance; Siemens RampFunction / ROC_LIM; Engineering ToolBox affinity |
| Informal | Vendor PID FBs (Siemens, Rockwell, Emerson, ABB, Beckhoff); InstrumentationTools trips/interlocks; Quanser coupled tanks; Modelica Fluid OpenTank |

---

## Executive summary

**Overall:** the shipped control math and the lumped plant are **well-backed**. The example skid is a **standard teaching topology**. Several product choices **diverge from DCS convention** on purpose. Nothing found requires adding citations to the App.

**PLC PID (strongest match).** The builtin block is ISA-TR5.9 **Parallel** in naming (independent `kp` / `ki` / `kd`) and Sundström, Hägglund, Bauer, Eker, Soltesz, *Reference Implementation of the PID Controller*, IFAC-PapersOnLine 58(7), 370–375, 2024 (doi:10.1016/j.ifacol.2024.08.090) in **incremental law**: control-signal increments, critically damped second-order ZOH measurement filter, `Tx = dt/ts`, tracking, feed-forward inside the clamp, output Manual (`auto` / `uman`), external `windup` flag, positional bias `u0` when `ki = 0`, D on filtered PV. The open post-print was retrieved. The paper itself says ISA 2023 is about **nomenclature and use**, not a code listing — so “ISA-TR5.9 Parallel + IFAC incremental” is the correct dual claim.

**Known PID partials / divergences.**

- ISA-TR5.9 (InTech excerpt) assumes PV / SP / CO in **percent of EU range**. This product uses engineering units (m, L/min, %). That is a documented TR5.9 warning, not a bug — **partial**.
- Lovelace **Man / Auto / Rem** is a **setpoint-source mux**. ISA / DCS / the IFAC paper define **Manual as output Manual** (`u = uman`). The `auto` / `uman` pins implement the standard meaning. The Lovelace mux does **not**. That is an **intentional diverge**, already noted in prior faceplate research.
- Wedge cascade copies set `tf_ts = 0` (filter bypass) so old PI tunings still settle. The paper default is `Tf/Ts = 10`. **Partial** (documented product choice).
- `gamma` (D setpoint weight) is unused. Full two-degree-of-freedom PID in Åström/Hägglund has both `b` and `c`. **Partial**.

**Scan.** Public IEC 61131-3 overviews describe **read inputs → execute → write outputs**, typical 1–100 ms. This product’s `IN → SAFETY → CONTROL → OUT` is that metaphor plus a **product** safety-before-control split. Python equations are **not** IEC 61131-3 language compliance (ST / LD / FBD). The code already says so. **Partial** (metaphor) / **not-in-scope** (languages).

**Model unit-ops (textbook physics, not a process-simulator standard).**

- `tank`: \(A\,dh/dt = q_\mathrm{in}-q_\mathrm{out}\) — **conform** (Kantor CBE30338; Skogestad volume balance).
- `orifice`: \(q = k\sqrt{h}\) — **conform** as lumped Torricelli / Bernoulli (Kantor \(q_\mathrm{out}=C_v\sqrt{h}\); Skogestad turbulent \(q_\mathrm{out}=k_t\sqrt{h}\)). `k` absorbs \(C_d A\sqrt{2g}\); viscosity and vena contracta are omitted (Kantor states Torricelli is an approximation).
- `lag` / pump first-order flow lag: \(y \leftarrow y+(1-e^{-\Delta t/\tau})(u-y)\) — **conform** (exact discrete map of a PT1 under ZOH / exponential Euler).
- `pump`: \(q \propto\) speed × suction derate — **partial**. Affinity law 1 is \(Q \propto N\) at constant diameter (Engineering ToolBox). Head \(H \propto N^2\) and the pump–system intersection are not modeled. Linear % maps are common on teaching rigs (Quanser), not on centrifugal VFD studies.
- `custom_ode`: forward Euler — **partial**. Adequate for qualitative operator training if \(\Delta t\) stays small (default substep ≤ 0.1 s); RK4 is the practitioner preference for accuracy.
- Inventory limiter: discrete mass conservation so a step cannot over-empty or over-fill — **conform** to conservation, **no** named standard. Ad hoc but physically required for a closed recycle at finite \(\Delta t\).

**Example system.** Reservoir → VFD pump → process tank → gravity orifice → reservoir with **level → flow cascade** is standard advanced-regulatory practice (outer LIC writes inner FIC SP; inner writes the final element). Inner-loop-faster is structurally true (pump \(\tau \approx 0.5\,\mathrm{s}\) vs tank holdup). HH / LL / LOS **latch + reset-to-STOP + no auto-restart** matches practitioner trip semantics (InstrumentationTools) and IEC 61511 *themes* in public supplements. Product docs saying **not SIL** match IEC 61508 / 61511 / 62061 scope (those standards require a lifecycle and a SIL target). `TagQuality` GOOD / UNCERTAIN / BAD matches OPC UA **severity**, not ISA-18.2 (alarms) and not the full OPC SubCode set.

**Nothing in this brief should be pasted into user-facing surfaces.** The App already avoids claiming SIL, IEC language compliance, or “the PDF that draws the faceplate.” Keep it that way.

---

## Key sources

| Title | Axis | ID/URL | Relevance |
|-------|------|--------|-----------|
| ISA-TR5.9-2023 InTech excerpt (Morgan & McMillan) | Formal | [isa.org InTech](https://www.isa.org/intech-home/2023/june-2023/features/isa-tr5-9-2023-realizing-and-achieving-best-pid) | Names Parallel / Standard / Series; PV, SP, CO; independent `kc`/`ki`/`kd`; prefers % of EU range |
| Sundström et al., IFAC-PapersOnLine 58(7) 370–375 | Formal | doi:[10.1016/j.ifacol.2024.08.090](https://doi.org/10.1016/j.ifacol.2024.08.090); [Lund post-print](https://lucris.lub.lu.se/ws/files/177637056/sundstrom24a.pdf) | Incremental reference: listings 1–4; `auto`/`uman`; filter; `Tx`; `windup` |
| A Practical Guide to PID Controller Implementation | Preprints | arXiv:[2604.15918](https://arxiv.org/abs/2604.15918) | Same Lund/Hägglund line; open companion discussion of incremental vs positional |
| IEC 61131-3 scan (secondary) | Web | [IronPLC](https://www.ironplc.com/explanation/what-is-iec-61131-3.html) | Read inputs → execute → write outputs; typical 1–100 ms. Full IEC paywalled |
| Kantor, Gravity-Drained Tank | Formal (teaching) | [CBE30338 §2.2](https://jckantor.github.io/CBE30338/02.02-Gravity-Drained-Tank.html) | Torricelli \(v=\sqrt{2gh}\); \(A\,dh/dt=q_\mathrm{in}-q_\mathrm{out}\); \(q_\mathrm{out}=C_v\sqrt{h}\) |
| Skogestad, Process dynamics Ch. 11 | Formal (teaching) | [NTNU PDF](https://skoge.folk.ntnu.no/prosessregulering/course-material/Skogestad-Ch11.pdf) | Volume balance; turbulent \(q_\mathrm{out}=k_t\sqrt{h}\) |
| OPC UA Part 8 §7.3 | Formal | [OPC 10000-8](https://reference.opcfoundation.org/Core/Part8/v105/docs/7.3) | BAD / UNCERTAIN / GOOD severity for data access |
| Cascade tutorial (OptiControls) | Web | [opticontrols.com](https://blog.opticontrols.com/a-tutorial-on-cascade-control/) | Level driving flow SP; inner ≥ ~3× faster; tune inner first |
| Pump affinity laws | Web | [Engineering ToolBox](https://www.engineeringtoolbox.com/amp/affinity-laws-d_408.html) | \(q_1/q_2 = n_1/n_2\) at constant diameter |
| Trips, interlocks, permissives | Informal | [InstrumentationTools](https://instrumentationtools.com/basics-of-trips-interlocks-permissives/) | Latch until reset; reset does not auto-start |
| Rockwell PIDE | Informal | [Studio 5000 PIDE](https://www.rockwellautomation.com/en-us/docs/studio-5000-logix-designer/38-00/contents-ditamap/instruction-set/process-control-instructions/pide.html) | Manual = CV; cascade = SPCascade from primary CVEU |
| Drainage / Torricelli ODE | Preprints | arXiv:[2511.00023](https://arxiv.org/abs/2511.00023) | \(A(h)\,dh/dt = -ka\sqrt{2gh}\) |

---

## Validation matrix

### PLC blocks and scan

| Item (code) | Governing source | Verdict | Evidence | Notes |
|-------------|------------------|---------|----------|-------|
| Builtin PID **Parallel** (`form: parallel`, independent `kp`/`ki`/`kd`) | ISA-TR5.9-2023 (InTech excerpt) | **conform** (naming) | InTech: “Proportional, integral, and derivative terms are individually added”; `ki` reciprocal of time | Full TR paywalled. Series/Standard not implemented (docs already say later). |
| PID signals in engineering units | ISA-TR5.9 (same excerpt) | **partial** | InTech: PV/SP/CO “assumed … percent of engineering unit (EU) range”; engineering-unit PIDs “disruptive of tuning methods” | Product uses m, L/min, %. Consistent internally; not TR5.9’s preferred scaling. |
| Incremental / velocity law | Sundström et al. 2024 | **conform** | Post-print: “We use the incremental (velocity) form, motivated by its intrinsic integrator anti-windup and bumpless transfer behavior.” | `dup+dui+dud+duff` added to `u_old` then clamp. |
| `ki` in 1/s, `Dui = ki * e * dt` | Sundström listing 1 (`Dui=ki*(r-yf)*Tx` with `Tx=dt/ts`) | **conform** | Post-print listing 1 + §3.5 | Equivalent once `Tx = dt/ts`. |
| `ki = 0` → positional bias `u0` | Sundström listing 1 | **conform** | Code `u_old_run = u0 if not ki_on` | P / PD path. |
| Measurement filter, `tf_ts` default 10, ZOH A/B | Sundström listings 2–3, `TfTs=10.0` | **conform** | Post-print §3.4–3.5 critically damped 2nd-order; listing 3 `h1=Tx/TfTs` | Matches `zoh_fy` in `pid.py`. |
| Wedge cascade `tf_ts = 0` | Same paper default 10 | **partial** | `pid_params_for_pi` sets `tf_ts: 0.0` | Filter bypass so existing PI tunings still settle. Finite-difference D if `kd≠0`. |
| D on filtered PV (`gamma` unused) | Sundström; Åström/Hägglund 2DOF | **partial** | Paper D uses `dyf`; `b` setpoint weight on P | `beta` backed; `c`/`gamma` unused. |
| Output Manual `auto` / `uman` | Sundström listing 1 | **conform** | “When auto==false, the control signal is given by the input uman.” | True DCS Manual. |
| Lovelace Man / Auto / Rem as SP mux | ISA/DCS Manual; Rockwell PIDE; Emerson | **diverge** (intentional) | PIDE: Manual sets **CV**; cascade uses SPCascade | Pins exist for real Manual; Lovelace mux is SP source. Do not relabel Lovelace “Manual” as ISA Manual. |
| External `windup` 0/1/2/3 | Sundström listing 4 | **conform** | none / upper / lower / both | Clamp of `Dui` only. |
| Tracking `track` / `utrack` | Sundström listing 1 | **conform** | Increment added to `utrack` | Paper: tracking only meaningful in auto. |
| Feed-forward `uff` inside clamp | Sundström | **conform** | `duff` then saturate | |
| Jitter `Tx = dt/ts` | Sundström §3.5 | **conform** | `Tx=(t-t_old)/Ts` in listing 5 | Soft-PLC injects `dt`. |
| `running` permit pin | No standard PID pin | **not-in-scope** / product | Wedge Start | Distinct from output Manual. |
| SP ramp (`ramp_setpoint`, units/s) | Vendor practice (Siemens RampFunction / SP_ROC; DeltaV SP_RATE_*) | **conform** (practice) | Siemens: ramp “Between setpoint source and setpoint input of the controller” | Not an ISA clause retrieved. Paper §3.4 rate-limits **inside** PID; we limit the **operator SP path**. Cascade SP from level can still step — same split DeltaV documents (SP_RATE often Auto-only). |
| Scan `IN → SAFETY → CONTROL → OUT` | IEC 61131-3 cyclic I→logic→O (secondary) | **partial** | IronPLC: read inputs, execute, write outputs; typical 1–100 ms | SAFETY-before-CONTROL is **product** (same-scan trip). Not a retrieved IEC clause. |
| Python equations vs ST/LD/FBD | IEC 61131-3 | **not-in-scope** | IronPLC / PLCopen overviews | Honest: metaphor only. No PLCopen mandatory PID equation found. |
| Period 0.1 s | IEC overviews; RSLogix cascade example | **conform** (practice) | “typical scan … 1 and 100 milliseconds” | Hobby overrun counters ≠ SIL timing. |
| ISA-5.1 `isa_tag` LIC / FIC | ANSI/ISA-5.1-2024 (summary) | **conform** (intent) | Letter tables in secondary ISA-5.1 guides | Full glyph tables paywalled. Tag *names* `LT_TANK` are project-style, not `LIC-101` (**partial** naming). |
| PV / SP / CO vs CV / MV | ISA-TR5.9 CO; IFAC r/y/u | **partial** | InTech uses CO; faceplate often MV | Internal `cv` ≈ CO. Consistent if not mixed in one surface. |

### Model unit-ops and integrator

| Item (code) | Governing source | Verdict | Evidence | Notes |
|-------------|------------------|---------|----------|-------|
| `tank` mass balance, constant area | Kantor; Skogestad Ch. 11 | **conform** | Kantor: \(A\,dh/dt = q_\mathrm{in}-q_\mathrm{out}\); Skogestad: \(dV/dt=q_\mathrm{in}-q_\mathrm{out}\), \(V=Ah\) | L/min ↔ m conversion in `process.py` is documented. |
| `orifice` \(q=k\sqrt{\max(h,0)}\) | Torricelli / Bernoulli lumped | **conform** (idealized) | Kantor \(q_\mathrm{out}=C_v\sqrt{h}\); arXiv:2511.00023 \(A(h)dh/dt=-ka\sqrt{2gh}\) | `k` lumps \(C_d A\sqrt{2g}\). Viscosity / vena contracta omitted (Kantor: approximation). |
| `pump` \(q_\mathrm{max}\times(\mathrm{cmd}/100)\times\mathrm{derate}\) | Affinity law 1; teaching rigs | **partial** | ToolBox \(q_1/q_2=n_1/n_2\); Quanser linear “pump flow constant” (informal) | No \(H\propto N^2\), no NPSH physics. Suction derate is a heuristic. |
| `lag` / pump τ: \(\alpha=1-e^{-\Delta t/\tau}\) | Discrete PT1 | **conform** | Exact ZOH map of \(\tau\dot y+y=u\) | Better than raw Euler on exponentials. |
| `custom_ode` forward Euler | Numerical ODE practice | **partial** | Euler \(y_{n+1}=y_n+h f\) (Wikipedia; teaching texts) | Stable only for small \(h\). Practitioner OTS often RK4 (informal). |
| Fixed-step ≤ 0.1 s | Same Euler stability | **partial** | Product `max_substep_s = 0.1` | Fine for this lab-scale plant; not a general guarantee. |
| Inventory flow limiter (closed recycle) | Conservation of mass | **conform** (physics) / no standard name | Prevents creating/destroying volume in one \(\Delta t\) | Required at finite step; not in Torricelli papers. |
| `skid_composed.json` wiring | Same physics as `MockProcess` | **conform** (internal) | pump + orifice + two tanks + lag | Oracle tests already require composed ≈ code skid. |

### Example system (wedge skid)

| Item | Governing source | Verdict | Evidence | Notes |
|------|------------------|---------|----------|-------|
| Topology: reservoir → pump → tank → gravity drain → reservoir | Teaching gravity-drained tank + recycle | **conform** | Kantor + Skogestad building blocks | No control valve in v1 is a **scope** choice, not a physics error. |
| Cascade LIC → FIC → pump speed | Cascade control practice | **conform** | OptiControls: “level controller driving the set point of a flow controller”; Rockwell: master CVEU → slave SPCascade; “valve, pump” as FCE | Tune inner first (practice). |
| Inner loop faster | Cascade rule of thumb 3×–10× | **partial** | OptiControls ≥3×; practitioner 5–10× | Pump \(\tau=0.5\,\mathrm{s}\) vs tank minutes-scale holdup is structurally faster; no commissioning check. |
| PI-only cascade (`kd=0`) | Practitioner (inner often P/PI) | **conform** | Automation.com / Schneider PPI notes (informal) | D stub unused. |
| Lab scale \(A=0.05\,\mathrm{m}^2\), \(H=0.4\,\mathrm{m}\), \(Q_\mathrm{max}=8\,\mathrm{L/min}\) | Didactic tanks | **conform** (class) | Quanser coupled tanks ~30 cm class (informal) | Defaults, not a standard. |
| HH / LL / LOS latched trips | Practitioner trips; IEC 61511 *themes* | **conform** (practice) | InstrumentationTools: remain until **manually reset**; reset **does not auto-start** | Matches `SafetyLayer`. |
| Not SIL / not certified SCS | IEC 61508 / 61511 / 62061 | **conform** to the “NOT” claim | Public overviews: SIL + lifecycle | Do not imply SIS independence (IEC 61511: SIS ≠ BPCS). |
| Same-scan force `CMD_SPEED=0` | Product safety-precedence | **partial** | No retrieved IEC clause for this four-phase split | Sound interlock practice. |
| `TagQuality` GOOD/BAD/UNCERTAIN | OPC UA StatusCode severity | **partial** | OPC 10000-8 §7.3 BAD / UNCERTAIN / GOOD | Reason codes are a small set; not ISA-18.2 (alarms). |
| `is_good` collapses UNCERTAIN with BAD for trips | Conservative safety default | **partial** | OPC distinguishes Uncertain vs Bad | Stricter than “use last-good on Uncertain”. Documented. |

---

## Themes and trends

### 1. Two documents answer two PID questions

ISA-TR5.9 names the **form** (Parallel vs Standard vs Series) and the **signals** (PV, SP, CO). Sundström et al. 2024 give a **digital incremental listing**. The paper cites ISA 2023 for nomenclature, not as the implementation. The shipped block is correctly described as both. Vendor defaults are often **Series/Standard** (Emerson, some Siemens FB41 reports) — Parallel is a valid TR5.9 form, not “the” industrial default.

### 2. Manual has one standard meaning

Across the IFAC listing, Rockwell PIDE, Siemens `MAN_ON`, and DCS faceplates, **Manual means the operator writes the controller output**. Cascade/remote means the **setpoint** comes from another block. This product implements both: `auto`/`uman` for output Manual, Lovelace mux for SP source. Mixing those labels on the HMI is the main **standards-language** risk — not a math error.

### 3. Plant models are first-principles lumps, not CFD

Torricelli + constant-area mass balance + PT1 actuator lag is the **canonical** undergraduate gravity-drained tank. Closed recycle plus an inventory clamp is the extra discrete-time honesty this lab needs. Linear pump maps are teaching-grade. They are **not** ISO 9906 pump tests and **not** affinity-complete.

### 4. Safety literature is a ceiling, not a template

IEC 61508/61511/62061 describe what a **SIL-rated** function looks like. The skid’s five behaviors match **trip/permissive culture** (latch, deliberate restart, stop-always). Product text that refuses SIL is the standards-correct statement.

### 5. Preprints add physics and PID, not PLC architecture

arXiv backs incremental PID (Lund line) and Torricelli drains. It does **not** back scan phase order, ISA tag letters, or VFD affinity on this skid. Those sit on formal / practitioner axes.

---

## Gaps and limitations

| Gap | Why it matters | Severity for this product |
|-----|----------------|---------------------------|
| Full ISA-TR5.9, IEC 61131-3, IEC 61511 texts paywalled | Cannot cite clause numbers | Expected; summaries used |
| No PLCopen canonical PID FB equation in the public corpus | Cannot claim “the IEC PID” | Already not claimed |
| Pump map ignores head–system intersection | Flow vs speed is not a real centrifugal curve | Acceptable for a **control teaching** skid; not for energy/NPSH stories |
| `custom_ode` Euler only | Stiff user equations can go unstable | Mitigated by 0.1 s substep on the shipped plant |
| Lovelace Manual ≠ ISA Manual | Operator vocabulary | Already documented; do not “fix” by renaming without UX work |
| Engineering-unit PID vs TR5.9 % scaling | Tuning recipes that assume 0–100% PV/CO | Internal clamps are consistent; importing vendor tunings needs care |
| Wedge `tf_ts=0` | Cascade PI not running the paper’s filter | Intentional; factory PID template still defaults `tf_ts=10` |
| No arXiv/standard for inventory limiter, suction derate, `running` pin | Engineering choices | Physics-motivated, not normative |
| Tag names `LT_TANK` vs ISA `LIC-101` | P&ID export | Demo clarity vs ISA loop numbers |

**Insufficient evidence (marked, not guessed):** exact ISA-TR5.9 annex performance metrics; IEC 61511 clause IDs for reset; ANSI/ISA-5.1 full symbol tables.

---

## Recommended reading order

1. Sundström et al. 2024 post-print (listings 1–4) — what `pid_scan` / `PID_EQUATION` transcribe.
2. ISA-TR5.9 InTech excerpt — Parallel vs Standard vs Series; PV/SP/CO; % range warning.
3. Kantor CBE30338 §2.2 — tank + Torricelli orifice.
4. Skogestad Ch. 11 — volume balance and \(\sqrt{h}\) outflow.
5. IronPLC IEC 61131-3 scan overview — cyclic I/O metaphor (not language compliance).
6. OPC UA Part 8 §7.3 — quality severity triad.
7. OptiControls cascade tutorial — LIC→FIC structure and inner-faster rule.
8. InstrumentationTools trips/interlocks (informal) — latch and no auto-restart.

---

## Role in pipeline

Finding docs for later `/model` or `/define` **if** someone wants to close a gap (for example: ISA Manual on the faceplate, Series form, affinity pump, RK4 custom_ode). Supportive context only — **not** a product plan.

The operator asked for validation only. Citations stay here. Do not add source lists, DOIs, or standard numbers to the App, Lovelace, or backend strings.

## Sources

1. Morgan, P. and McMillan, G. K. (2023). ISA-TR5.9-2023: Realizing and Achieving Best PID. *InTech*. https://www.isa.org/intech-home/2023/june-2023/features/isa-tr5-9-2023-realizing-and-achieving-best-pid — **Formal** (secondary excerpt of paywalled TR).
2. Sundström, E., Hägglund, T., Bauer, M., Eker, J., Soltesz, K. (2024). Reference Implementation of the PID Controller. *IFAC-PapersOnLine* 58(7), 370–375. doi:10.1016/j.ifacol.2024.08.090. Open post-print: https://lucris.lub.lu.se/ws/files/177637056/sundstrom24a.pdf — **Formal**.
3. Sundström et al. related preprint. *A Practical Guide to PID Controller Implementation*. arXiv:2604.15918 — **Preprints**.
4. ISA. ISA-TR5.9-2023 product page. https://www.isa.org/products/isa-tr5-9-2023-proportional-integral-derivative-pi — **Formal** (paywalled full text).
5. ISA-5 standards series hub. https://www.isa.org/standards-and-publications/isa-standards/isa-5-standard — **Formal**.
6. Kantor, J. CBE30338 §2.2 Gravity Drained Tank. https://jckantor.github.io/CBE30338/02.02-Gravity-Drained-Tank.html — **Formal** (open teaching).
7. Skogestad, S. Process dynamics, Chapter 11. https://skoge.folk.ntnu.no/prosessregulering/course-material/Skogestad-Ch11.pdf — **Formal** (open teaching).
8. IronPLC. What is IEC 61131-3? https://www.ironplc.com/explanation/what-is-iec-61131-3.html — **Web discovery** (secondary).
9. OPC Foundation. OPC 10000-8 §7.3 Data Access status codes. https://reference.opcfoundation.org/Core/Part8/v105/docs/7.3 — **Formal**.
10. Engineering ToolBox. Affinity Laws for pumps. https://www.engineeringtoolbox.com/amp/affinity-laws-d_408.html — **Web discovery**.
11. OptiControls. A Tutorial on Cascade Control. https://blog.opticontrols.com/a-tutorial-on-cascade-control/ — **Web discovery**.
12. Siemens TIA Portal. RampFunction (setpoint path). https://docs.tia.siemens.cloud/ — **Informal** (vendor).
13. Rockwell Automation. PIDE instruction. Studio 5000 docs — **Informal**.
14. InstrumentationTools. Basics of trips, interlocks, permissives. https://instrumentationtools.com/basics-of-trips-interlocks-permissives/ — **Informal**.
15. Jones et al. Bayesian reversal of liquid level in a draining tank. arXiv:2605.29193 — **Preprints**.
16. Drainage Time and Shape: Inequalities from Torricelli's Law. arXiv:2511.00023 — **Preprints**.
17. Caparroz et al. Anti-Windup in PID Control. arXiv:2606.01959 — **Preprints**.
18. IEC 61508 Association. What is IEC 61508? https://61508.org/knowledge/what-is-iec-61508/ — **Formal** (overview, not full standard).
19. Wikipedia. Torricelli's law; Euler method — **Web discovery** (encyclopedic orientation only).
20. Quanser Coupled Tanks product page — **Informal** (lab-scale class).
21. Modelica.Fluid.Vessels.OpenTank documentation — **Informal** (practitioner library).

Code inventory (not sources): `plcassistant/control/pid.py`, `plcassistant/surface/builtin.py`, `plcassistant/control/scan.py`, `plcassistant/control/ramp.py`, `plcassistant/wedge/process.py`, `plcassistant/wedge/safety.py`, `custom_components/plcassistant/dynamics/ops.py`, `custom_components/plcassistant/dynamics/models/skid_composed.json`.

## Tracker

- Task: SWD-384
- Artifact: docs/RESEARCH.md
- Branch: `cursor/swd-384-validate-plc-model-0f45`
- PR: — (research never opens a PR from this skill; cloud delivery may still attach a draft for review)

## Next

none — validation brief only; no product change. Optional later: `/model SWD-384` if a math artifact is wanted, or `/define` if a gap (ISA Manual faceplate, affinity pump, Series form) becomes work.
