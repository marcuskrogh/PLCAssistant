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
| 4 | Integration mock UI + preset selection | Configure and select presets in HA, not only in code | **In Review** (App 0.1.24) | [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143) |

## Open questions
- ~~Where the ODE solver should run~~ → **locked (SWD-145/146):** integration-owned simulator; Soft-PLC mock-unaware
- ~~How Soft-PLC stays mock-agnostic~~ → **locked:** MQTT plant IN; `HeldProcess` on Soft-PLC
- ~~What “unit operation” means for v1 and how custom equations are expressed safely~~ → **locked** (SWD-144)
- ~~How presets are selected/edited in HA UI~~ → **locked in** [`docs/PLAN.md`](PLAN.md) (SWD-143 define): Options flow + options persistence + service; reload rebuilds plant
- How far mock-off / field I/O must remain a first-class path

## Explicitly deferred
- Full unit-op graph / equation authoring UI (file/YAML remains authoring path)
- Soft-PLC App plant UI (mock ≠ PLC program)
- Mid-scan live model-graph rewiring
- replacing Soft-PLC control programming with plant math (mock ≠ PLC program)
- physical plant / field commissioning (still follow-on)
- Broad chem-eng catalog beyond skid-derived ops → follow-on after SWD-144

## Tracker
- Provider: jira
- Story: [SWD-142](https://marcusknielsen.atlassian.net/browse/SWD-142)
- Tasks: [SWD-145](https://marcusknielsen.atlassian.net/browse/SWD-145) (Done), [SWD-146](https://marcusknielsen.atlassian.net/browse/SWD-146) (Done), [SWD-144](https://marcusknielsen.atlassian.net/browse/SWD-144) (Done), [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143)
- Prior initiative: [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81) (Done)

## Next
`/review-fix SWD-143` — Integration mock UI + preset selection (App 0.1.24)
