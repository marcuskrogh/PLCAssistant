# Implementation plan: Packaging shape (SWD-84)

## Summary
- **Hybrid packaging:** Soft-PLC runtime + block editor live in a **Home Assistant App** (formerly add-on); a **thin integration** owns tag declarations, entity↔tag bindings, mock/sim entities, and operator services.
- **HA OS only** for v1 — Supervisor Apps path; HA Container installs are out of scope for now.
- **MQTT** is the App ↔ HA bridge; users **must install Mosquitto** (or equivalent MQTT App).
- Program-of-record (JSON-shaped block program) lives in **App persistent data**.
- Deliver a **store-ready custom App from GitHub** (third-party App repository URL), not the official HA Apps store yet.
- Editor reachable via **Supervisor Ingress** and an **optional exposed port**.
- Thin integration is **bundled with the App** (shipped/registered alongside the App install path).

## Scope
**In**
- Packaging contract docs: freeze the hybrid shape; rename Add-on → App in packaging docs; Mosquitto dependency + MQTT topic / payload map
- HA App scaffold: `config.yaml`, Dockerfile, Ingress, optional port, data volume for programs
- MQTT I/O bridge on the App side (live `IoImage` ↔ MQTT); keep in-process stub for non-HA unit tests
- Bundled thin integration: bindings, mock entities, Start/Stop/Reset services; MQTT client toward the App
- GitHub App repository layout + install documentation (add repo URL → install App)
- Acceptance: install path, MQTT mock round-trip, program persistence, Ingress + port reachability

**Out**
- Official Home Assistant Apps store submission / upstream review
- HA Container / Core / Supervised as first-class install targets
- Embedded MQTT broker inside the Soft-PLC App
- Expanding Soft-PLC language / authoring surface (already SWD-82)
- Physical plant / field commissioning
- Real-time OS / `SCHED_FIFO` hardening beyond demo-grade Python scan

## Decisions
- Primary shape = **hybrid** (App + thin integration) — matches wedge sketch and research ecosystem patterns
- v1 install target = **HA OS only**
- Bridge = **MQTT**; hard dependency on **Mosquitto** App (user-installed)
- Program-of-record = **App persistent data** (survives App restart)
- Publication = **custom App from GitHub** (community / third-party repo)
- Thin integration = **bundled with the App**
- Editor access = **Ingress + exposed port**
- In-process `ThinIntegrationStub` remains the path for pytest / non-HA CI

## Constraints
- Preserve SWD-85 scan order and SWD-86 image/quality/bindings contracts
- Soft-PLC must not branch on “mock mode”; mock ≡ field via bindings into the same image
- Integration stays connections-oriented (no program authoring surface in Core)
- App must work with Supervisor lifecycle on HA OS
- Do not claim SIL / certified safety packaging

## Inputs (supportive — not substitutes for decisions above)
- Research: [`docs/RESEARCH.md`](RESEARCH.md) (SWD-84 packaging brief)
- Prior sketch: [`docs/wedge/08-packaging-sketch.md`](wedge/08-packaging-sketch.md)
- I/O stub: [`docs/io/03-thin-integration-stub.md`](io/03-thin-integration-stub.md)
- Surface App (local): `plcassistant/app/`

## Acceptance criteria
- App installs on HA OS from a **GitHub App repository** URL
- With Mosquitto + bundled thin integration configured, mock skid tags flow **App ↔ HA over MQTT**
- Block editor opens via **Ingress** and via the documented **host port**
- Program files in App data **persist across App restart**
- Packaging docs describe the locked hybrid shape (App naming, Mosquitto, MQTT map, bundle path)
- Non-HA unit tests still pass via in-process stub (no live Mosquitto required in CI)

## Work packages
1. **Packaging contract docs** — freeze shape; Add-on→App rename in packaging docs; Mosquitto + MQTT topic map → `docs/packaging/` (or evolve `docs/wedge/08-packaging-sketch.md`)
2. **HA App scaffold** — Dockerfile, `config.yaml`, Ingress, port, data volume
3. **MQTT I/O bridge (App)** — image ↔ MQTT; HA path replaces in-process calls
4. **Bundled thin integration** — bindings, mock entities, services; MQTT toward App
5. **GitHub App repository + install docs** — repo layout, README install steps
6. **Acceptance** — checklist + automated tests where feasible (MQTT round-trip, persistence, docs)

## Open items
- Whether Ingress auth reuses HA session only or needs App-side auth for the exposed port
- Versioning / update channel for the GitHub App repo (see `ha_app/INSTALL.md`)

## Locked during implement
- MQTT topic namespace + payload schema → `docs/packaging/02-mqtt-topics.md` + `plcassistant.io.mqtt_topics`
- Bundle mechanism → documented one-time copy of `custom_components/plcassistant/` (not auto-copy)

## Tracker
- Provider: jira
- Story: [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81)
- Task: [SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84)
- Sub-tasks:
  - [SWD-122](https://marcusknielsen.atlassian.net/browse/SWD-122) — Packaging contract docs
  - [SWD-123](https://marcusknielsen.atlassian.net/browse/SWD-123) — HA App scaffold
  - [SWD-125](https://marcusknielsen.atlassian.net/browse/SWD-125) — MQTT I/O bridge (App)
  - [SWD-126](https://marcusknielsen.atlassian.net/browse/SWD-126) — Bundled thin integration
  - [SWD-127](https://marcusknielsen.atlassian.net/browse/SWD-127) — GitHub App repository + install docs
  - [SWD-124](https://marcusknielsen.atlassian.net/browse/SWD-124) — Acceptance tests + checklist

## Next
Done — phase closed (shipped PR #30 merge `3b64b33`)
