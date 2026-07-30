# Iterate: Restart required on Settings → Updates (SWD-168)

## Prior work
- Task: [SWD-138](https://marcusknielsen.atlassian.net/browse/SWD-138) — auto Core restart after thin-integration sync
- PR: [#53](https://github.com/marcuskrogh/PLCAssistant/pull/53)
- Spec context: `docs/packaging/04-updates.md`, `plc_assistant/run.sh`

## Problem
App update detection works (Settings → check for updates shows PLCAssistant). After the App syncs the thin integration, Core must restart for the new integration code to load. Other integrations (HACS-style) show **Restart required** on the same Settings → System → Updates page; PLCAssistant does not.

## Clarifications
- Keep existing auto Core restart (SWD-138); add visible pending-restart UX when Core has not yet picked up the synced files.
- Signal = on-disk `manifest.json` version ≠ version loaded into memory at import time (HACS-equivalent pending restart).
- The Update entity ships in the thin integration, so the first upgrade *to* 0.1.27 still relies on auto/manual Core restart; the card appears on later syncs once 0.1.27+ is already loaded.

## Acceptance criteria
- [ ] Thin integration registers an `update` entity for PLCAssistant.
- [ ] When disk version ≠ loaded version, the Updates page shows the entity with a HACS-style Restart required `release_summary` (`ha-alert`).
- [ ] A fixable repair issue (`restart_required`) offers Restart Home Assistant.
- [ ] When versions match after Core restart, update entity is off and the repair is cleared.
- [ ] Auto Core restart path unchanged.
- [ ] Docs (`04-updates.md`) mention the Restart required indicator.
- [ ] Tests cover version helpers + wiring (no HA import in CI); App ↔ integration version bumped together.

## Out of scope
- Customizing the Supervisor App update entity itself
- Removing or changing `PLCASSISTANT_AUTO_CORE_RESTART` defaults

## Work packages
1. Pure helpers: read loaded vs disk version; pending-restart predicate
2. `update` platform + repair issue create/clear + strings
3. Wire platform in `__init__.py`; bump version; docs + tests; sync App package

## Tracker
- Task: [SWD-168](https://marcusknielsen.atlassian.net/browse/SWD-168)
- Relates: [SWD-138](https://marcusknielsen.atlassian.net/browse/SWD-138)
- PR: [#70](https://github.com/marcuskrogh/PLCAssistant/pull/70)
- Branch: `cursor/swd-168-restart-required-0337`

## Next
`/review-fix SWD-168` — Review and auto-fix until clean
