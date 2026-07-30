# Roadmap: Configurable mock dynamics

## Direction
- Move beyond a **hard-wired example skid mock** toward a **broad, configurable mock** of tags and underlying dynamics.
- Operators should configure mocks primarily from the **thin Home Assistant integration** (UI or equivalent), using **basic unit operations**, **custom differential equations**, and a **collected ODE** stepped on the Soft-PLC **sampling interval**.
- The current tank/reservoir skid remains available as a **selectable preset**, not the only plant model.

## Themes to investigate
| Phase | Theme | Why it matters | Deferred to | Issue |
|-------|-------|----------------|--------------|-------|
| 1 | Soft-PLC ↔ integration mock ownership | Docs put plant under the integration; runtime hard-wires `Skid`/`MockProcess` in the App — this choice shapes everything else | **Done** (App 0.1.21) | [SWD-145](https://marcusknielsen.atlassian.net/browse/SWD-145) |
| 2 | Configurable dynamics core + skid preset | States/tags + collected ODE at scan period; skid as first preset | **Done** (App 0.1.22) | [SWD-146](https://marcusknielsen.atlassian.net/browse/SWD-146) |
| 3 | Unit-op library + custom equation authoring | Easy mocks vs expressive custom DEs | **Done** (App 0.1.23) | [SWD-144](https://marcusknielsen.atlassian.net/browse/SWD-144) |
| 4 | Integration mock UI + preset selection | Configure and select presets in HA, not only in code | **Done** (App 0.1.24) | [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143) |

## Open questions
- ~~Where the ODE solver should run~~ → **locked (SWD-145/146):** integration-owned simulator; Soft-PLC mock-unaware
- ~~How Soft-PLC stays mock-agnostic~~ → **locked:** MQTT plant IN; `HeldProcess` on Soft-PLC
- ~~What “unit operation” means for v1 and how custom equations are expressed safely~~ → **locked** (SWD-144)
- ~~How presets are selected/edited in HA UI~~ → **locked** (SWD-143): Options flow + options persistence + service; reload rebuilds plant
- ~~Sidebar block editor for unit-ops / ODEs~~ → **locked** (SWD-166): Dynamics tab + model store (App 0.1.25)
- ~~Per-equation state/measurement authoring~~ → **locked** (SWD-167): one-row state ODEs + measurement `y=g(x,u,θ)` (App 0.1.26)
- How far mock-off / field I/O must remain a first-class path

## Explicitly deferred
- Soft-PLC App plant UI (mock ≠ PLC program)
- Mid-scan live model-graph rewiring
- replacing Soft-PLC control programming with plant math (mock ≠ PLC program)
- physical plant / field commissioning (still follow-on)
- Broad chem-eng catalog beyond skid-derived ops → follow-on

## Tracker
- Provider: jira
- Story: [SWD-142](https://marcusknielsen.atlassian.net/browse/SWD-142) — **Done** (all theme Tasks Done)
- Tasks: [SWD-145](https://marcusknielsen.atlassian.net/browse/SWD-145) (Done), [SWD-146](https://marcusknielsen.atlassian.net/browse/SWD-146) (Done), [SWD-144](https://marcusknielsen.atlassian.net/browse/SWD-144) (Done), [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143) (Done — PR #66)
- Iterate: [SWD-166](https://marcusknielsen.atlassian.net/browse/SWD-166) (Done — PR #68), [SWD-167](https://marcusknielsen.atlassian.net/browse/SWD-167) (Done — PR #69, App 0.1.26)
- Prior initiative: [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81) (Done)

## Next
Done — initiative complete (SWD-167 iterate shipped).
