# Implementation plan: Lab / hobby wedge — gravity-drained tank skid (SWD-83)

## Summary
- Primary example: **one process tank + reservoir**, recycled water loop: reservoir → **variable-speed inlet pump** → tank → **gravity drain** → reservoir.
- First wedge proves **cascade control** (level → flow setpoint → pump speed) plus an **illustrative safety layer**, on a **mock first**; **physical rig is the next iteration** and is required for **overall** system success.
- Preliminary packaging: **HA Add-on (app)** for runtime/mock engine + **thin config integration** for entity binding and operator services.
- Later examples (two-tank; four-tank with split valve) are **out of this Task**.

## Scope
**In**
- Reference skid: 1 tank + reservoir; **pump-only** actuator; gravity drain (no outlet pump / no control valve in v1)
- Automatic cascade: **level loop** outputs **flow setpoint**; **flow loop** tracks via **pump speed** + inlet flow sensor
- Safety (illustrative middle ground):
  1. High tank level → stop pump (latched)
  2. Low reservoir level → stop pump (dry-run protect, latched)
  3. Loss-of-signal on tank level, reservoir level, or flow → stop pump (latched)
  4. Latched trip + **operator reset**
  5. HMI **operator start/stop** (Start only if permissives OK; Stop always)
- I/O: tank level, reservoir level, inlet volumetric flow, pump speed feedback if available; pump speed command; HMI start/stop, setpoints, trip/reset, key measurements
- **Mock path** as this Task’s delivery bar; product must **allow mocking / simulated processes**
- Historian/HMI via normal HA paths (Lovelace / logging) as reuse, not a new stack in this Task
- Preliminary packaging: HA Add-on + thin config integration (working choice; full evaluation remains SWD-84)

**Out**
- Home-as-process as a goal for this phase
- Two-tank and four-tank / split-valve examples (later)
- Physical rig build/wiring as **this** Task’s done bar (follow-on iteration; still required for whole-product success)
- Full industrial safety framework (SIL, certified safety PLC, rich bypass/audit model beyond reset)
- Final packaging freeze / exhaustive alternatives study (SWD-84) — preliminary shape is chosen above
- Full programming-language and soft-PLC runtime internals beyond what the packaging sketch and control/safety specs require (SWD-82 / SWD-85 / SWD-86)

## Decisions
- Wedge audience: lab / hobby / small process equipment
- Control story: cascade level → flow → pump speed
- Safety story: the five behaviors above
- Mock first; physical next; both needed for overall success
- One-tank + reservoir only for this example
- Start as **HA Add-on + thin config integration**

## Constraints
- HA remains the low-friction I/O / logging / HMI surface
- Must not paint into a corner that blocks later multi-tank / valve examples
- Entity-binding mechanics, deep scan/runtime semantics, and authoring UX stay with sibling Tasks where not needed for the skid specs and packaging sketch

## Acceptance criteria
- Documented reference skid matches the scope above (process narrative, I/O list, control + safety story)
- On **mock**: operator can **Start/Stop** from HMI; cascade holds/responds to level & flow setpoints; high-tank, low-reservoir, loss-of-signal each **trip, latch, and require reset**; Stop always works
- Mock/simulation support called out as a system requirement (not a one-off test hack)
- Preliminary Add-on + thin integration responsibilities documented enough to host the mock path
- Physical rig listed as **required follow-on** for overall success (not silently dropped)
- Explicit out-of-scope list retained for later examples

## Work packages
1. **Reference process spec** — P&ID-level narrative, recycled loop, one-tank + reservoir boundaries
2. **I/O & HMI contract for the skid** — signals, setpoints, start/stop/reset, displays
3. **Control story spec** — cascade level→flow→speed behavior and operating modes needed for the demo
4. **Safety story spec** — the five behaviors, latch/reset, permissives for Start
5. **Mock process requirements** — simulated process behavior + how mocking is a first-class capability
6. **Mock acceptance scenarios** — runnable checklist covering cascade + each safety case + Start/Stop
7. **Follow-on note** — physical rig iteration + later two-tank / four-tank examples (pointers only)
8. **Preliminary packaging sketch** — Add-on vs integration responsibilities, config surface enough to support mock acceptance (not a full installable product yet)

## Open items
- Exact add-on/runtime stack inside the Add-on
- PID/tuning and timing semantics (SWD-85 / possible `/model`)
- Entity mapping mechanics in HA (SWD-86)
- Programming authoring UX (SWD-82)
- Full packaging alternatives (SWD-84)
- Physical bill of materials and wiring (next iteration after mock)

## Tracker
- Provider: jira
- Story: [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81)
- Task: [SWD-83](https://marcusknielsen.atlassian.net/browse/SWD-83)
- Sub-tasks:
  - [SWD-88](https://marcusknielsen.atlassian.net/browse/SWD-88) — Reference process spec
  - [SWD-87](https://marcusknielsen.atlassian.net/browse/SWD-87) — I/O & HMI contract for the skid
  - [SWD-92](https://marcusknielsen.atlassian.net/browse/SWD-92) — Control story spec
  - [SWD-93](https://marcusknielsen.atlassian.net/browse/SWD-93) — Safety story spec
  - [SWD-90](https://marcusknielsen.atlassian.net/browse/SWD-90) — Mock process requirements
  - [SWD-89](https://marcusknielsen.atlassian.net/browse/SWD-89) — Mock acceptance scenarios
  - [SWD-91](https://marcusknielsen.atlassian.net/browse/SWD-91) — Follow-on note (physical + later examples)
  - [SWD-94](https://marcusknielsen.atlassian.net/browse/SWD-94) — Preliminary packaging sketch

## Next
`/implement SWD-83` — Build per this plan
