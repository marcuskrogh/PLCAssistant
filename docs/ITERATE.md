# Iterate: Store Latest stuck behind GitHub App version

## Prior work
- Task: SWD-129 (PR #41, App 0.1.7 Docker cache-bust + hass.components migrate)
- Also: single-config store discovery (removed duplicate `ha_app` App config)
- Spec context: `docs/packaging/04-updates.md`, `plc_assistant/config.yaml`, `repository.yaml`

## Problem
On HA OS after 0.1.7 shipped on GitHub `main`:

1. UI claims an update is available.
2. The update detail/menu shows **installed = 0.1.6** and **latest = 0.1.6**.
3. That “latest” is wrong — GitHub `plc_assistant/config.yaml` is already newer.

This is **Supervisor store discovery / stale update-entity metadata**, not the Docker layer-cache bug fixed in SWD-129.

Two overlapping failure modes:

| Mode | What you see | Cause |
|------|----------------|-------|
| A. Store git stuck | Apps page **and** Updates dialog both show Latest = old | Supervisor’s shallow clone under `/data/addons/git/…` did not advance; or frontend never reloaded store |
| B. Update entity lag | Apps page shows Update to new version, but Updates / more-info still says installed = latest = old | Core `HassioAddOnDataUpdateCoordinator` can lag ~15 min after store reload (HA Core quirk) |

## Acceptance criteria
1. Install/update docs pin the repository URL as `https://github.com/marcuskrogh/PLCAssistant#main`.
2. Docs explain how to verify GitHub version vs HA **Latest**, and recovery: Check for updates → hard-refresh → Core restart; if Latest still stuck, remove/re-add the repository (`#main`).
3. App + integration version bumped to **0.1.8** so a successful store refresh shows a clear new Latest.
4. Tests cover `#main` URL in README / packaging docs and mention stuck-Latest recovery.

## Out of scope
- Fixing Home Assistant Core’s update-entity coordinator (upstream)
- Pre-built `image:` / GHCR publishing (follow-on)

## Work packages
1. Docs: `#main` pin + stuck-Latest recovery
2. Version bump 0.1.8 + sync manifests / Dockerfile default
3. Tests

## Tracker
- Task: [SWD-130](https://marcusknielsen.atlassian.net/browse/SWD-130)
- Relates: SWD-129

## Next
`/review-fix SWD-130` — Review and auto-fix until clean
