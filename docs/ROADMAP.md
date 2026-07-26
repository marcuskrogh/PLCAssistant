# Roadmap: PLCAssistant — Virtual PLC for Home Assistant

## Direction
- Build a **virtual / soft-PLC** experience for **lab, hobby, and small-scale process equipment**, using Home Assistant as a **low-friction I/O platform** (easy device connect, control, and logging), with HMI and historian leaning on HA strengths (Lovelace / dashboards, InfluxDB + Grafana).
- Ambition spans **approachable industrial control patterns** (loops, feedback, safety) **and** a path toward a **credible soft-PLC substitute**, with programming that is **very high-level and easy** but still **deeply customizable**.
- **Home-as-process** is treated as a **future expansion or implicit byproduct**, not a current initiative direction.

## Themes to investigate
| Phase | Theme | Why it matters | Deferred to | Issue |
|-------|-------|----------------|--------------|-------|
| 1 | Lab / hobby / small-process wedge | Sharpen who this is for and what “success” looks like in that world | define ✓ → implement | [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83) |
| 2 | HA entities as PLC I/O | Core inversion: devices live in HA, then participate in PLC-style control | define / research | [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86) |
| 3 | Control semantics | What “PLC-like” means here: loops, feedback, safety, timing — without locking runtime design yet | research | [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85) |
| 4 | Programming surface | Easy high-level entry with a deep customization path | research / define | [SWD-82](https://marcusknielsen.atlassian.net/browse/SWD-82) |
| 5 | Packaging shape | Integration vs app/add-on vs hybrid — still intentionally open | research | [SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84) |

## Open questions
- Where the PLC runtime should live relative to HA (inside vs beside), and what “integration” vs “app” should mean
- How far “credible soft-PLC” must go for the lab wedge vs later
- How much of historian/HMI is pure reuse of HA vs needs PLC-aware conventions
- What “safety” means at this ambition level (soft interlocks vs stronger guarantees)
- How progressive the easy→customizable programming path should feel
- What, if anything, should be kept open so home-as-process can emerge later without driving current scope

## Explicitly deferred
- define — scope, behaviour, acceptance, work packages
- research / model — as needed per theme (especially control semantics, programming surface, packaging)
- home-as-process as an explicit product direction (may remain an implicit expansion later)

## Tracker
- Provider: jira
- Story: [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81)
- Tasks: [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83), [SWD-86](https://marcusknielsen.atlassian.net/browse/SWD-86), [SWD-85](https://marcusknielsen.atlassian.net/browse/SWD-85), [SWD-82](https://marcusknielsen.atlassian.net/browse/SWD-82), [SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84)

## Next
`/implement SWD-83` — Build lab/hobby wedge per `docs/PLAN.md`
