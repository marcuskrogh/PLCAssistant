# Research: Compare state estimation methods for SDEs

**Tracker:** [SWD-113](https://marcusknielsen.atlassian.net/browse/SWD-113)  
**Scope:** Independent research track — **not** PLCAssistant / [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81)  
**Date:** 2026-07-27  
**Tooling:** `scripts/arxiv_research.py` (stdlib arXiv Atom client)

## Question

How do continuous-discrete state estimation methods for systems involving stochastic differential equations (SDEs) compare — on accuracy, computational cost, nonlinearity / non-Gaussianity, stiffness, and when to prefer each?

Focus methods:

1. Extended Kalman filter (EKF / CD-EKF)
2. Unscented Kalman filter (UKF / CD-UKF)
3. Cubature Kalman filter (CKF / CD-CKF)
4. Ensemble Kalman filter (EnKF / CD-EnKF)
5. Particle filter (PF / CD-PF)
6. Adjacent: moving horizon estimation (MHE), deep / Fokker–Planck approximators

## Strategy

| Step | What |
|------|------|
| Seed queries | continuous-discrete + SDE state estimation; Kalman vs particle / unscented / cubature / ensemble |
| Lookup cores | [2205.02730](https://arxiv.org/abs/2205.02730), [2212.02139](https://arxiv.org/abs/2212.02139), [2303.04035](https://arxiv.org/abs/2303.04035), [1604.04498](https://arxiv.org/abs/1604.04498), Kulikova/Kulikov CD-UKF/CKF numerics |
| Snowball | Authors/categories from cores (noisy — hand-filtered physics/comms false positives) |
| Triage | Keep CD filtering comparisons, stiff-SDE filter studies, DA/CSTR/MFTS benchmarks; drop unrelated Kalman-in-name-only papers |
| Grounding | Method taxonomy via Fokker–Planck / Bayesian DA approximations (Diaa-Eldeen et al.) |

Raw JSON under `/tmp/sde-estimation-research/` (not committed).

## Problem setting

Continuous-discrete (CD) models:

\[
\begin{aligned}
dx(t) &= f(t,x,u,d,\theta)\,dt + \sigma(t,x,u,d,\theta)\,d\omega(t), \\
y(t_k) &= h(t_k,x(t_k),\theta) + v(t_k).
\end{aligned}
\]

Exact conditional density evolution between measurements is the **Fokker–Planck / Kolmogorov forward PDE**. Dimension equals state dimension → impractical beyond a few states ([Jazwinski](https://arxiv.org/abs/2212.02139) framing in Nielsen et al.). All practical filters are **approximate Bayesian updates**: time update (propagate prior via SDE) + measurement update (assimilate \(y_{t_k}\)).

## Method map (what each approximates)

| Method | Time-update idea | Posterior shape | Needs Jacobians? | Cost scaling (typical) |
|--------|------------------|-----------------|------------------|------------------------|
| **CD-EKF** | Integrate mean + linearized covariance ODEs | Gaussian | Yes | Low (1 trajectory + \(P\) ODE / sensitivity) |
| **CD-UKF** | Propagate \(2n+1\) (or augmented) sigma points through nonlinear SDE | Gaussian from sample moments | No | Moderate (\(\propto n\)) |
| **CD-CKF** | Third-degree cubature points + (often) Itô–Taylor discretization | Gaussian | No | Moderate (\(\propto n\)), similar class to UKF |
| **CD-EnKF** | Monte Carlo ensemble; Kalman update in ensemble space | Implicitly Gaussian update | No | High (\(\propto N_{\text{ens}}\)); localization/inflation often needed |
| **CD-PF** | Weighted particles + resampling (e.g. SIR) | Nonparametric | No | Very high; curse of dimensionality |
| **MHE** | Optimize trajectory over a horizon (constraints OK) | Point / MAP-ish; uncertainty secondary | Via NLP | High (online NLP); strong on constraints |
| **Deep / FP solvers** | Learn density / BSDE / splitting approximations | Flexible | N/A (train) | Research / high-dim niche |

Shared Bayesian view ([2303.04035](https://arxiv.org/abs/2303.04035)): KF exact for linear-Gaussian; EKF = dynamical linearization + Gaussian; UKF = deterministic sampling + Gaussian; EnKF = MC + Gaussian Kalman update; PF = MC of full posterior (fewest distributional assumptions, highest sample cost).

## Empirical comparisons (literature)

### A. Modified four-tank system (MFTS) — non-stiff CD SDEs

[Nielsen et al., arXiv:2205.02730](https://arxiv.org/abs/2205.02730) / [2212.02139](https://arxiv.org/abs/2212.02139): Matlab, explicit integration, Joseph-form EKF. 30 min, 120 samples; EnKF \(N=250\), PF \(N=1000\).

| | EKF | UKF | EnKF | PF |
|--|-----|-----|------|-----|
| Time update [s] | 0.31 | 2.9 | 34 | 136 |
| Meas. update [s] | 0.012 | 0.041 | 0.23 | 1.05 |
| MAPE states [%] | 2.55 | 2.97 | **2.35** | 2.40 |
| MAPE disturbances [%] | 15.7 | 17.5 | 14.7 | **13.7** |

**Takeaway:** All four track states/disturbances successfully. **EKF cheapest**; **EnKF/PF slightly more accurate** at ~10²–10³× time-update cost. On this mildly nonlinear plant, UKF did not beat EKF on MAPE (and was slower).

### B. Stochastic CSTR — joint state + parameter estimation

[Diaa-Eldeen, Nielsen, Jørgensen, arXiv:2303.04035](https://arxiv.org/abs/2303.04035): adiabatic CSTR SDE; estimate \(C_A,C_B,T,\beta\); \(N_{\text{ens}}=N_{\text{PF}}=1000\).

| | EKF | UKF | EnKF | PF |
|--|-----|-----|------|-----|
| \(MSE_x\) | 0.66 | 0.64 | **0.48** | 0.53 |
| \(MSE_p\) | 6.30 | 6.30 | **4.52** | 4.95 |
| \(t_{CPU}\) / step [s] | **0.030** | 0.082 | 4.03 | 4.17 |

**Takeaway:** **EnKF best accuracy**; EKF/UKF similar MSE; PF close to EnKF but not better here. **EnKF more robust than PF to reducing ensemble size** down toward state dimension; PF collapsed earlier. EKF remains the efficiency default when Jacobians are cheap.

### C. Stiff continuous-discrete SDEs — EKF vs UKF vs CKF

[Kulikov & Kulikova, arXiv:1604.04498](https://arxiv.org/abs/1604.04498): Van der Pol and related models, nonstiff vs stiff (\(\lambda\) up to \(10^4\)).

- **Nonstiff:** CD-CKF ≳ CD-UKF ≳ CD-EKF (higher-order Gaussian moment matching wins), especially at longer sampling intervals.
- **Stiff:** accuracies degrade sharply; **CD-EKF can outperform CD-UKF/CD-CKF** — counter to the “UKF/CKF always better” folklore. Stiff CD-SDEs need careful discretization / square-root / stiff ODE numerics, not just a “better” sigma-point transform ([2310.04126](https://arxiv.org/abs/2310.04126), [2311.11299](https://arxiv.org/abs/2311.11299)).

### D. Adjacent families (not head-to-head in the same MFTS/CSTR tables)

| Family | Relative position |
|--------|-------------------|
| **MHE** | Best when **constraints** and nonlinear model fidelity matter; heavier than EKF; often more robust to bad initials than EKF (Haseltine & Rawlings-type comparisons). Complementary to PF (hybrid MHE+PF discussed in process-control tutorials). |
| **Deep density / BSDE / FP ML** | Target **high-dimensional** filtering where particle methods fail; still early vs industrial CD-EKF practice ([2511.07261](https://arxiv.org/abs/2511.07261)). |

## Comparison axes (synthesis)

| Axis | Winner / guidance |
|------|-------------------|
| **Speed / APC embedding** | **EKF** first; UKF/CKF if Jacobians painful or mild nonlinearity needs better moment match |
| **Mild–moderate nonlinearity, Gaussian-ish noise** | EKF ≈ UKF often; don’t assume UKF wins without a twin experiment |
| **Strong nonlinearity / non-Gaussian posterior** | **PF** (full distribution) or **EnKF** (practical middle ground); MHE if constraints dominate |
| **Joint parameter + state (augmented)** | EnKF strong in CSTR twin; watch dual-estimation bias vs joint augmentation |
| **High dimension** | EnKF (+ localization/inflation); PF scales poorly; EKF covariance ODE can also hurt |
| **Stiffness** | Prefer **stable numerics + EKF (or square-root CD filters)**; sigma-point/IT discretizations can lose |
| **Long sampling intervals** | Higher-order Gaussian filters (UKF/CKF) or finer SDE steps matter more; EKF linearization drifts |
| **Uncertainty quantification** | PF / large ensemble reference; Kalman family only gives Gaussian \(P\) |

## Decision cheat-sheet

```
IF linear-Gaussian CD → Kalman filter (exact)
ELIF stiff SDE + need industrial reliability → CD-EKF with robust stiff integration / Joseph or square-root form
ELIF mild nonlinearity, cheap Jacobians, real-time APC → CD-EKF
ELIF mild–moderate nonlinearity, no Jacobians → CD-UKF or CD-CKF
ELIF multimodal / strongly non-Gaussian, low–moderate dim → CD-PF (budget particles carefully)
ELIF nonlinear, moderate–high dim, Gaussian update acceptable → CD-EnKF (+ localization)
ELIF hard state constraints / MAP trajectory → MHE (optionally hybrid with PF/EKF)
ELIF very high dim density estimation research → deep FP / BSDE filters
```

## Themes

1. **All CD filters are Fokker–Planck approximations** — choose by which error you can afford (linearization vs Gaussian closure vs sample size vs NLP).
2. **Accuracy ≠ order of moment matching** when stiffness or discretization dominates (Kulikov/Kulikova).
3. **EnKF often matches or beats PF at lower \(N\)** on process examples that stay near-Gaussian after update (CSTR dual estimation).
4. **UKF is not a free upgrade over EKF** on every plant (MFTS MAPE; stiff cases).
5. **Numerics of the time update** (explicit vs stiff solvers, Itô–Taylor order, square-root covariance) are first-class accuracy factors, not implementation footnotes.
6. **MHE is the constraint-aware sibling**, not a drop-in replacement in the EKF–PF speed ladder.

## Gaps

- Few **single-benchmark, multi-method** studies spanning EKF/UKF/CKF/EnKF/PF/**MHE** with identical SDE discretizations and tuning protocols.
- **Stiff + high-dimensional** CD filtering still under-served by theory and software.
- Fair comparisons need **matched process-noise / measurement-noise / integrator step** — published tables sometimes retune \(\sigma,\lambda\) per filter (noted in MFTS setup).
- Deep FP filters lack mature process-control head-to-heads against EnKF/PF on CSTRs/tank systems.

## Suggested reading order

1. [2205.02730](https://arxiv.org/abs/2205.02730) — compact CD EKF/UKF/EnKF/PF + MFTS numbers  
2. [2303.04035](https://arxiv.org/abs/2303.04035) — Bayesian DA taxonomy + CSTR joint estimation table  
3. [1604.04498](https://arxiv.org/abs/1604.04498) — stiff vs nonstiff EKF/UKF/CKF  
4. [2310.04126](https://arxiv.org/abs/2310.04126) — accurate CD-UKF numerics (MATLAB ODE / square-root)  
5. Haseltine & Rawlings (MHE vs EKF) — when optimization beats recursive Gaussians  
6. [2511.07261](https://arxiv.org/abs/2511.07261) — only if pursuing high-dim deep density filters  

## Sources

**Core arXiv:**
- [2205.02730](https://arxiv.org/abs/2205.02730) — Nielsen et al., CD methods + MFTS  
- [2212.02139](https://arxiv.org/abs/2212.02139) — Nielsen et al., FOCAPO/CPC companion  
- [2303.04035](https://arxiv.org/abs/2303.04035) — Diaa-Eldeen et al., DA + CSTR  
- [1604.04498](https://arxiv.org/abs/1604.04498) — Kulikov & Kulikova, stiff EKF vs UKF/CKF  
- [2310.04126](https://arxiv.org/abs/2310.04126) — Kulikova & Kulikov, CD-UKF frameworks  
- [2311.11299](https://arxiv.org/abs/2311.11299) — square-root CD-EKF covariance factors  
- [2511.07261](https://arxiv.org/abs/2511.07261) — deep density high-dim filtering  

**External (non-arXiv Atom):**
- Arasaratnam, Haykin, Hurd — CD cubature Kalman filter (IEEE TSP 2010)  
- Haseltine & Rawlings — critical EKF vs MHE evaluation  
- Rawlings & Bakshi — particle filtering and MHE survey (Comp. Chem. Eng.)

**Tooling:** arXiv Atom API via `scripts/arxiv_research.py`

## Tracker

- Story [SWD-113](https://marcusknielsen.atlassian.net/browse/SWD-113) — independent of PLCAssistant; research artifact is this doc.
- Do **not** route next steps into `/define SWD-82`.

## Next

Research synthesis complete for SWD-113. Optional follow-ons (separate tickets if pursued):

- Reproduce MFTS/CSTR tables in one shared codebase with locked \(\sigma\), step size, and seeds  
- Add CD-CKF + MHE to the same harness  
- Stiffness sweep (Van der Pol-style) for EKF/UKF/CKF with identical integrators  
