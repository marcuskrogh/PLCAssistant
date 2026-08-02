# Iterate: PID faceplate card — SP edit bugs + climate-inspired visual refresh

## Prior work
- Task: [SWD-225](https://marcusknielsen.atlassian.net/browse/SWD-225)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/88 (App 0.1.45)
- Spec context: PID loops engage; faceplate SP editing + card look still weak

## Problem
1. While the Soft-PLC is active, PID card SP fields are buggy: deleting/editing
   (e.g. Man SP `0.2` → `0.3`) auto-jumps the caret and produces values like
   `30` instead of `0.3` (HTML `type="number"` + live hass restomps).
2. The PID card looks plain — needs a climate-card-inspired visual refresh:
   mode colours, clear active SP / PV / CV hierarchy, more engaging layout.

## Acceptance criteria
- [x] SP Man/Auto/Rem edits preserve intermediate text (`0.`, empty, partial)
      across live hass updates; caret does not jump; Set commits a valid number
- [x] Active mode is colour-coded (Man / Auto / Rem); active SP source row is
      visually emphasized; PV / active SP / CV are first-class readouts
- [x] Card remains a single Lovelace custom card (`plcassistant-pid-card`);
      mode + Set behaviour unchanged (Set still flips mode per faceplate contract)
- [x] App/integration **0.1.46**; dashboard **25**; dual trees synced; tests green

## Out of scope
- Classic output Manual (operator sets CV directly)
- New HA entity attributes beyond what the compound sensor already exposes
- Full climate domain migration

## Work packages
1. Fix draft SP editing (text + inputmode; stable draft while focused/dirty) — done
2. Climate-inspired visual redesign of `pid-loop-card.js` — done
3. Version bump + acceptance tests + dual-tree sync — done

## Review-fix
- Iter 1: dirty-on-focus freeze + color-mix fallbacks — fixed
- Iter 2: CLEAN

## Tracker
- Task: [SWD-226](https://marcusknielsen.atlassian.net/browse/SWD-226)
- Relates: SWD-225
- Branch: `cursor/swd-226-pid-card-sp-edit-visual-5ef6`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/89
- Shipped: App **0.1.46**

## Next
Done — phase closed.
