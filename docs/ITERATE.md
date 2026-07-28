# Iterate: App Update stale image + hass.components after reinstall

## Prior work
- Task: SWD-128 (PR #40, App 0.1.6 start hardening)
- Also: PR #39 (`async_subscribe` MQTT fix, App 0.1.5)
- Spec context: `plc_assistant/Dockerfile`, `plc_assistant/run.sh`, `custom_components/plcassistant/`

## Problem
1. **Update button shows but installed App version stays previous** after Update.
2. **Uninstall/reinstall** still loads old thin integration:
   ```text
   AttributeError: 'HomeAssistant' object has no attribute 'components'
   File "/config/custom_components/plcassistant/__init__.py", line 138
   ```
   That line is pre-0.1.5 `hass.components.mqtt.async_subscribe` (already fixed on `main`).

## Cause
HAOS local-build Apps can keep **stale Docker/containerd build layers** across Update/reinstall. The running image may still ship the old bundled `custom_components`, so auto-install copies or skips as “up to date” while Core keeps the broken subscribe path.

## Acceptance criteria
1. Dockerfile consumes Supervisor `BUILD_VERSION` in a layer **before** package/integration `COPY`, and sets `io.hass.version`.
2. App start force-syncs thin integration when App version stamp changes **or** DST still contains `hass.components`.
3. Runtime migration rewrites remaining `hass.components.mqtt` subscribe → `async_subscribe` even if the image bundle is stale.
4. App + integration manifest version **0.1.7**; README/updates doc mention Update cache / `docker builder prune` if Update still sticks.
5. Tests cover migration + version-stamp force-sync.

## Out of scope
- Publishing pre-built `image:` to GHCR (follow-on)
- Changing Supervisor/containerd itself

## Work packages
1. Dockerfile cache-bust + labels + version bump
2. run.sh stamp force-sync + hass.components migration
3. Docs + regression tests

## Tracker
- Task: [SWD-129](https://marcusknielsen.atlassian.net/browse/SWD-129)
- Relates: SWD-128
- Branch: `cursor/fix-app-update-stale-image-9777`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/41

## Next
`/review-fix SWD-129` — Review and auto-fix until clean
