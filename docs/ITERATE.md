# Iterate: Supervisor job-group errors after App reinstall

## Prior work
- Task: SWD-84 (packaging shape)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/30 (and follow-ups through 0.1.5 / PR #39)
- Spec context: `docs/packaging/`, `plc_assistant/run.sh`, thin-integration auto-install

## Problem
After reinstalling App **0.1.5**, configuring the App/integration logs:

```text
Failed to to call /addons/1173ddd6_plcassistant/stop - Another job is running for job group app_1173ddd6_plcassistant
Failed to to call /addons/1173ddd6_plcassistant/stats - App 1173ddd6_plcassistant is not running
```

Supervisor serializes jobs per App. Reinstall/start holds the job group; Configuration Save triggers stop/restart and collides. Stats fail because the container is not running yet.

Amplifier in our tree: `run.sh` uses `set -eu`, so a thin-integration install failure aborts the Soft-PLC process → crash loop → perpetual start jobs + “not running”. Synchronous MQTT connect before `serve_forever` can also delay readiness.

## Clarifications
- Logs are from `homeassistant.components.hassio` (Supervisor websocket), not the thin integration config flow itself.
- Pure Supervisor race during overlapping stop/start cannot be eliminated in App code; we harden startup and document recovery.

## Acceptance criteria
1. Thin-integration install failures are logged and do **not** prevent the App from starting.
2. MQTT broker connect does not block the editor HTTP server from accepting requests.
3. README documents wait-for-Started + stuck-job recovery for this Supervisor error.
4. App `version` bumped so Supervisor can deliver the fix.
5. Regression tests cover install-failure resilience (and non-blocking MQTT boot path).

## Out of scope
- Pre-built App container images (`image:` in `config.yaml`)
- Changing Supervisor itself
- Thin integration config-flow UX redesign

## Work packages
1. Harden `run.sh` install path + defer MQTT connect in HA runtime
2. Docs troubleshooting + version bump `0.1.6`
3. Regression tests

## Tracker
- Task: [SWD-128](https://marcusknielsen.atlassian.net/browse/SWD-128)
- Relates: SWD-84
- Branch: `cursor/fix-app-supervisor-jobs-9777`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/40

## Next
`/review-fix SWD-128` — Review and auto-fix until clean
