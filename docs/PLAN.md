# Implementation plan: Soft-PLC ↔ integration mock ownership (SWD-145)

## Summary
- Stand-alone **process simulator** lives in the **thin Home Assistant integration**. Soft-PLC remains **mock-unaware** and treats all I/O as real field signals.
- Process ↔ Soft-PLC communication is **MQTT** (mock path ≡ field path).
- The integration may **observe** Soft-PLC essentials (e.g. `scan_period_s` on MQTT status) so the future simulator can step with the Soft-PLC sample interval; Soft-PLC does **not** receive mock/plant identity back.
- **Remove** App-owned plant (`MockProcess` / skid physics) from the **live** Soft-PLC App scan path **in this Task**. Process dynamics stay dark until the integration simulator ([SWD-146](https://marcusknielsen.atlassian.net/browse/SWD-146)).
- Soft-PLC keeps **control / safety / image I/O**; plant PVs become Soft-PLC **IN** via MQTT.

## Scope
**In**
- Ownership contract docs (packaging, wedge mock process, I/O notes)
- Soft-PLC exposes `scan_period_s` on retained MQTT `status` (for integration observe)
- Remove live App plant from scan path; Soft-PLC no longer synthesizes plant PVs as OUT
- Flip plant process tags (`LT_TANK`, `LT_RES`, `FT_INLET`, …) to Soft-PLC **IN** bindings
- Soft-PLC continues control/safety OUT (`CMD_SPEED`, `MODE`, `PERM_OK`, `TRIP_ACTIVE`, active SPs as applicable)
- Bindings / HMI / file-bridge cleanup so plant OUT is not assumed from Soft-PLC
- Tests updated for intentional process-motion gap

**Out**
- Integration stand-alone simulator / unit ops / custom ODEs → [SWD-146](https://marcusknielsen.atlassian.net/browse/SWD-146)
- Integration mock UI + preset selection → [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143)
- Unit-op library / equation authoring details → [SWD-144](https://marcusknielsen.atlassian.net/browse/SWD-144)
- Soft-PLC programming surface changes (blocks/editor)
- Physical field commissioning

## Decisions
1. **Integration owns** the stand-alone process simulator; Soft-PLC never branches on “mock mode.”
2. **One-way observe:** integration may read Soft-PLC MQTT status (including `scan_period_s`); Soft-PLC gets no mock identity back.
3. **Process ↔ PLC I/O = MQTT** for this path (mock ≡ field).
4. **Remove App plant now**; accept dark process until SWD-146 (operator-approved gap).
5. **`MockProcess` may remain as a library for unit tests**, not in the live HA App scan path.
6. Integration UI for entity↔tag wiring and dynamics authoring is **owned conceptually here** but **implemented** in SWD-143 / SWD-146.

## Constraints
- Preserve Soft-PLC scan order (IN → SAFETY → CONTROL → OUT) without plant synthesis in OUT
- Do not add Soft-PLC APIs that mean “mock mode”
- MQTT topic/payload contracts remain the bridge; file bridge may still hydrate HMI when MQTT is silent but is not the process↔PLC plant path
- App + integration version lock remains
- Dual trees under `plc_assistant/` stay synced

## Inputs (supportive — not substitutes for decisions above)
- Roadmap: [`docs/ROADMAP.md`](ROADMAP.md) (SWD-142)
- Prior packaging: [`docs/packaging/01-shape.md`](packaging/01-shape.md)
- Prior mock layers: [`docs/wedge/05-mock-process.md`](wedge/05-mock-process.md)

## Acceptance criteria
1. Docs state: integration-owned stand-alone simulator; Soft-PLC mock-unaware; MQTT process↔PLC; one-way status observe including `scan_period_s`.
2. Soft-PLC retained MQTT `status` includes `scan_period_s` (numeric seconds).
3. Live HA App scan does **not** run plant physics and does **not** publish plant PVs (`LT_TANK`, `LT_RES`, `FT_INLET`) as Soft-PLC OUT.
4. Soft-PLC still runs control/safety with MQTT IN/OUT for operator cmds and CVs/status.
5. Automated tests updated; process-motion acceptance deferred or explicitly marked expected-dark until SWD-146.
6. No Soft-PLC code path that enables “mock mode” for plant.

## Work packages
1. **Ownership docs** — packaging / wedge / I/O contract updates for integration-owned simulator + MQTT + one-way observe
2. **Expose `scan_period_s`** — Soft-PLC MQTT status (+ tests)
3. **Remove App plant from live scan** — drop `MockProcess`/`Skid` plant from App `SkidImageLogic` path; plant tags as IN
4. **Bindings / HMI / file-bridge cleanup** — stop assuming Soft-PLC plant OUT; adjust defaults and HMI copy for gap
5. **Tests + acceptance** — update suites; document intentional process gap until SWD-146

## Open items
- Full simulator stepping from observed `scan_period_s` → SWD-146
- Entity↔tag wiring UI + presets → SWD-143
- Whether offline CI keeps a local `MockProcess` helper vs a thinner IN fixture (implement choice; library retention allowed)

## Tracker
- Provider: jira
- Story: [SWD-142](https://marcusknielsen.atlassian.net/browse/SWD-142)
- Task: [SWD-145](https://marcusknielsen.atlassian.net/browse/SWD-145)
- Sub-tasks: [SWD-149](https://marcusknielsen.atlassian.net/browse/SWD-149) docs, [SWD-150](https://marcusknielsen.atlassian.net/browse/SWD-150) scan_period_s, [SWD-147](https://marcusknielsen.atlassian.net/browse/SWD-147) remove App plant, [SWD-148](https://marcusknielsen.atlassian.net/browse/SWD-148) bindings/HMI/file-bridge, [SWD-151](https://marcusknielsen.atlassian.net/browse/SWD-151) tests
- Branch: `cursor/swd-145-mock-ownership-33f4`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/59

## Next
Shipped (PR #59 + #60). Next: `/define SWD-146`
