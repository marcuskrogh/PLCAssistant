# Implementation plan: Integration mock UI + preset selection (SWD-143)

## Summary
- Let operators **select a plant dynamics preset** (`skid`, `skid_composed`, …) and apply **numeric param overrides** from the thin Home Assistant integration — not from Soft-PLC or hard-wired code.
- Persist selection on the **config entry**; rebuild the plant simulator on apply (reload), keeping Soft-PLC **mock-unaware**.

## Scope
**In**
- Config-entry **Options flow** (“Configure”) for `dynamics_preset` + optional `dynamics_params` overrides
- Wire `HassPlantSimulator` / `PlantSimulator.for_preset` to the configured preset + params (default remains code `skid`)
- Service `plcassistant.set_dynamics_preset` that writes the same options SoT and reloads the plant
- Active-preset visibility (sensor state/attributes) + Lovelace/HMI operator copy
- Docs + tests + App/integration version bump (**0.1.24**)
- Dual-tree sync via `./scripts/sync-ha-app-package.sh`

**Out**
- Soft-PLC App Ingress / block-editor plant UI (mock ≠ PLC program)
- Full unit-op graph / equation authoring UI (file/YAML documents remain the authoring path from SWD-144)
- Mid-scan live rewiring of the model graph (apply = rebuild from initials)
- Mock-off / field I/O commissioning changes
- Scan-edge lockstep; Soft-PLC programming/control/safety changes
- Persisted live plant **state** across Core restart (still reset to model initials)

## Decisions
1. **UI surface:** Config-entry **Options flow** is the primary chooser. No custom panel and no Soft-PLC Ingress plant UI. Lovelace documents how to configure; it is not a second authoring surface.
2. **Apply model:** Changing preset/params **rebuilds** the plant simulator (stop → new `PlantSimulator.for_preset` → start). Plant state returns to model initials. Existing plant Number **nudges** stay the live state path; param overrides are not live mid-scan.
3. **Preset list:** Driven by `list_presets()` / registry (`skid`, `skid_composed`, plus any future documents under `dynamics/models/`). Unknown names fail at apply/load with a clear error — never crash mid-tick.
4. **Customize depth (v1):** Select preset + optional **numeric param overrides** (keys from `param_defaults`). No HA unit-op graph editor; composed documents stay file-based.
5. **Persistence:** `config_entry.options` keys `dynamics_preset` (str, default `"skid"`) and `dynamics_params` (mapping of float overrides, default `{}`). Options win over hard-wired defaults; `data.mock_mode` still gates whether a simulator runs.
6. **Service:** `set_dynamics_preset` updates options (same keys) and triggers the same reload path as Options flow — one SoT.
7. **Visibility:** Expose active preset (and optionally effective params) on a thin integration sensor/attributes so operators and Lovelace can see what is running.
8. **Soft-PLC boundary locked:** Plant math stays under `custom_components/plcassistant/dynamics/`. Soft-PLC stays `HeldProcess` + MQTT plant IN. Do not import Soft-PLC surface for plant config.
9. **Versioning:** App + integration **0.1.24**; dual trees synced.

## Constraints
- Soft-PLC remains mock-unaware
- HA-free dynamics modules stay free of `homeassistant` imports; options/service/simulator wrappers may use HA
- Preserve MQTT topic/payload contracts; plant Numbers remain display/nudge while simulator owns tags
- One simulator task per config entry
- Default live preset remains `skid` when options omit the key (zero operator regression)

## Acceptance criteria
1. Options flow lists available presets and persists `dynamics_preset` / `dynamics_params` on the config entry.
2. After apply/reload, `HassPlantSimulator` runs the selected registry preset with overrides; default without options is still `skid`.
3. Selecting `skid_composed` runs the composed document path (oracle-equivalent dynamics from SWD-144).
4. Invalid preset name fails apply/setup with a clear error; running tick path never raises from bad config mid-scan.
5. Service `set_dynamics_preset` updates the same options and reloads equivalently to Options flow.
6. Active preset is visible via integration sensor/attributes; Lovelace copy tells operators where to configure.
7. Soft-PLC App does not gain plant math or preset APIs.
8. Automated tests cover: options→registry wiring, param overrides, invalid preset, default `skid`.
9. App + integration versions bumped to **0.1.24** and dual trees synced.

## Work packages
1. **Options flow + persistence** — OptionsFlow schema; constants; entry update + plant reload hook ([SWD-162](https://marcusknielsen.atlassian.net/browse/SWD-162))
2. **Simulator wiring** — preset/params into `HassPlantSimulator` / `for_preset`; active-preset sensor attrs ([SWD-163](https://marcusknielsen.atlassian.net/browse/SWD-163))
3. **Service + Lovelace copy** — `set_dynamics_preset`; HMI/help text for chooser ([SWD-164](https://marcusknielsen.atlassian.net/browse/SWD-164))
4. **Acceptance + packaging** — tests, docs, version **0.1.24**, dual-tree sync ([SWD-165](https://marcusknielsen.atlassian.net/browse/SWD-165))

## Tracker
- Provider: jira
- Story: [SWD-142](https://marcusknielsen.atlassian.net/browse/SWD-142)
- Task: [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143)
- Sub-tasks: [SWD-162](https://marcusknielsen.atlassian.net/browse/SWD-162) options, [SWD-163](https://marcusknielsen.atlassian.net/browse/SWD-163) simulator wiring, [SWD-164](https://marcusknielsen.atlassian.net/browse/SWD-164) service/Lovelace, [SWD-165](https://marcusknielsen.atlassian.net/browse/SWD-165) acceptance
- Prior: [SWD-144](https://marcusknielsen.atlassian.net/browse/SWD-144) Done (App 0.1.23)
- Branch: `cursor/swd-143-mock-ui-presets-33f4`
- Implement: App **0.1.24**

## Next
`/review-fix SWD-143`