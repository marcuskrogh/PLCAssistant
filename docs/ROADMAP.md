# Roadmap: Configurable mock dynamics

## Direction
- Move beyond a **hard-wired example skid mock** toward a **broad, configurable mock** of tags and underlying dynamics.
- Operators should configure mocks primarily from the **thin Home Assistant integration** (UI or equivalent), using **basic unit operations**, **custom differential equations**, and a **collected ODE** stepped on the Soft-PLC **sampling interval**.
- The current tank/reservoir skid remains available as a **selectable preset**, not the only plant model.

## Themes to investigate
| Phase | Theme | Why it matters | Deferred to | Issue |
|-------|-------|----------------|--------------|-------|
| 1 | Soft-PLC ↔ integration mock ownership | Docs put plant under the integration; runtime hard-wires `Skid`/`MockProcess` in the App — this choice shapes everything else | define | [SWD-145](https://marcusknielsen.atlassian.net/browse/SWD-145) |
| 2 | Configurable dynamics core + skid preset | States/tags + collected ODE at scan period; skid as first preset | define (model if math-blocked) | [SWD-146](https://marcusknielsen.atlassian.net/browse/SWD-146) |
| 3 | Unit-op library + custom equation authoring | Easy mocks vs expressive custom DEs | define | [SWD-144](https://marcusknielsen.atlassian.net/browse/SWD-144) |
| 4 | Integration mock UI + preset selection | Configure and select presets in HA, not only in code | define | [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143) |

## Open questions
- Where the **ODE solver** should run (Soft-PLC App, thin integration, or shared library) vs where the **UI** configures it
- How Soft-PLC stays **mock-agnostic** (image/bindings) while plant dynamics become selectable
- What “unit operation” means for v1 and how custom equations are expressed safely
- How presets relate to today’s wedge HMI/tag contract and acceptance tests
- How far mock-off / field I/O must remain a first-class path

## Explicitly deferred
- define — scope, behaviour, acceptance, work packages per theme
- research / model — as needed (especially ODE / solver formalism)
- replacing Soft-PLC control programming with plant math (mock ≠ PLC program)
- physical plant / field commissioning (still follow-on)

## Tracker
- Provider: jira
- Story: [SWD-142](https://marcusknielsen.atlassian.net/browse/SWD-142)
- Tasks: [SWD-145](https://marcusknielsen.atlassian.net/browse/SWD-145), [SWD-146](https://marcusknielsen.atlassian.net/browse/SWD-146), [SWD-144](https://marcusknielsen.atlassian.net/browse/SWD-144), [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143)
- Prior initiative: [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81) (Done)

## Next
`/review-fix SWD-145` — ownership implement on PR #59 (App 0.1.20); then `/ship SWD-145` · next theme `/define SWD-146`
