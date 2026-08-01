# Iterate: PID cards Configuration error + default mode Remote

## Prior work
- Task: [SWD-219](https://marcusknielsen.atlassian.net/browse/SWD-219) (Relates SWD-183)
- PRs: #82 (0.1.39), #81 (0.1.38)
- Spec context: `docs/io/06-pid-faceplate.md`, Operate Lovelace YAML

## Problem
1. Operate dashboard shows **Configuration error** for PID / block-list custom cards.
2. Level loop mode boots as **remote**; skid does not follow Manual/Auto operator path. Default must be **Manual**.

## Clarifications
- Screenshot: fallback entities show Level loop mode = remote; three Configuration error cards above Process.

## Acceptance criteria
- [x] Lovelace PID + block-list cards register as storage-mode Lovelace resources (`?v=` cache-bust); YAML mode falls back to `add_extra_js_url`
- [x] Card JS guards `customElements.define`; remove broken `getConfigElement` that returns a row element
- [x] Default `LEVEL_MODE` / `FLOW_MODE` = Manual (`0`) in Soft-PLC Datablock, HA catalog, Number meta, Soft-PLC mux fallback, compound sensor initial state
- [x] Number entity setup/hydration must not mode-flip when publishing default MAN/REM SP values
- [x] Stock Operate dashboard version bumped so App refresh picks up card registration notes
- [x] Tests cover defaults, no-flip-on-hydrate, and resource-registration source contract
- [x] App/integration **0.1.40**; dual trees synced

## Out of scope
- Classic CV Manual / output Manual
- Redesigning faceplate UX beyond making cards work + Manual default

## Work packages
1. Lovelace resource registration + card JS hardening
2. Manual default + no mode-flip on hydrate
3. Tests + version + docs

## Tracker
- Task: [SWD-220](https://marcusknielsen.atlassian.net/browse/SWD-220)
- Relates: SWD-219
- Branch: `cursor/swd-220-pid-cards-manual-default-a52c`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/83 (App 0.1.40)
- Review-fix: CLEAN after 2 iterations

## Next
Done — phase closed.