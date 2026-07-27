# Roadmap: PLCAssistant — Virtual PLC for Home Assistant

## Direction
- Build a **virtual / soft-PLC** experience for **lab, hobby, and small-scale process equipment**, using Home Assistant as a **low-friction I/O platform** (easy device connect, control, and logging), with HMI and historian leaning on HA strengths (Lovelace / dashboards, InfluxDB + Grafana).
- Ambition spans **approachable industrial control patterns** (loops, feedback, safety) **and** a path toward a **credible soft-PLC substitute**, with programming that is **very high-level and easy** but still **deeply customizable**.
- **Home-as-process** is treated as a **future expansion or implicit byproduct**, not a current initiative direction.

## Themes to investigate
| Phase | Theme | Why it matters | Deferred to | Issue |
|-------|-------|----------------|--------------|-------|
| 1 | Lab / hobby / small-process wedge | Sharpen who this is for and what “success” looks like in that world | **Done** — [PR #11](https://github.com/marcuskrogh/PLCAssistant/pull/11) | [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) |
| 2 | HA entities as PLC I/O | Core inversion: devices live in HA, then participate in PLC-style control | **Done** — [PR #14](https://github.com/marcuskrogh/PLCAssistant/pull/14) merge `b64a0cd` | [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86) |
| 3 | Control semantics | What “PLC-like” means here: loops, feedback, safety, timing — without locking runtime design yet | **Done** — [PR #18](https://github.com/marcuskrogh/PLCAssistant/pull/18) merge `a51cdbe` | [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85) |
| 4 | Programming surface | Easy high-level entry with a deep customization path | implement → review | [SWD-82](https://marcusknielsen.atlassian.net/browse/SWD-82) · [`docs/PLAN.md`](PLAN.md) · [`docs/surface/`](surface/01-block-model.md) |
| 5 | Packaging shape | Integration vs app/add-on vs hybrid — still intentionally open | research | [SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84) |

## Open questions
- Where the PLC runtime should live relative to HA (inside vs beside), and what “integration” vs “app” should mean (preliminary: Add-on + thin integration; mock/sim owned by thin integration per SWD-86)
- How far “credible soft-PLC” must go for the lab wedge vs later
- How much of historian/HMI is pure reuse of HA vs needs PLC-aware conventions
- How progressive the easy→customizable programming path should feel
- What, if anything, should be kept open so home-as-process can emerge later without driving current scope

## Explicitly deferred
- research / model — as needed per remaining themes
- home-as-process as an explicit product direction (may remain an implicit expansion later)
- physical rig (follow-on after mock; required for overall success)

## Tracker
- Provider: jira
- Story: [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81) (open — sibling phases remain)
- Tasks: [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) **Done**, [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86) **Done**, [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85) **Done**, [SWD-82](https://marcusknielsen.atlassian.net/browse/SWD-82), [SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84)

## Next
`/review-fix SWD-82` — Programming surface implement ready for review
