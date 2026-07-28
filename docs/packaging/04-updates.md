# 04 — App updates (Supervisor store)

**Plan:** [`docs/PLAN.md`](../PLAN.md) · Shape: [`01-shape.md`](01-shape.md)

## How Supervisor learns about a new version

Custom GitHub App repositories are **pulled on demand**, not watched.

1. Developer bumps `version` in [`plc_assistant/config.yaml`](../../plc_assistant/config.yaml) and merges to `main`.
2. On the HA host: **Settings → Apps → ⋮ → Check for updates** → Supervisor shallow-fetches the repo branch.
3. Supervisor compares **installed** `version` to the store copy of `config.yaml`.
4. If they differ, the App detail page shows **Update**.

Hard-refresh the browser after step 2 (store UI is often cached). Prefer adding the repository as:

```text
https://github.com/marcuskrogh/PLCAssistant#main
```

so Supervisor pins the `main` branch explicitly. Keep [`repository.yaml`](../../repository.yaml) / App `config.yaml` `url` as the bare homepage (no `#branch`) — only the Supervisor **Repositories** field uses the fragment.

There is **no** GitHub webhook into Supervisor. Shipping a new commit without bumping `version` will not offer an Update button (rebuild requires uninstall/reinstall or a version bump).

## Invariant (must hold for every future release)

Supervisor recursively discovers every `config.yaml` / `config.yml` / `config.json` in the repository.

This repo must contain **exactly one** such App config:

```text
plc_assistant/config.yaml    ← only App (slug: plcassistant)
```

A second file with the same `slug` makes update detection unreliable (store can stick on an old version until the repository is removed and re-added). CI enforces this in `tests/test_github_app_repo.py`.

`ha_app/` is **docs-only** (install pointer). Never put an App `config.yaml` there.

## Release checklist (general — every update)

1. Change runtime / package / integration as needed.
2. If `plcassistant/` or `custom_components/plcassistant/` changed, run:
   ```bash
   ./scripts/sync-ha-app-package.sh
   ```
3. Bump **`version`** in **both** `plc_assistant/config.yaml` and
   `custom_components/plcassistant/manifest.json` to the **same** value
   (required for the Update button and so HA’s integration version matches the App).
   Also keep `plc_assistant/Dockerfile` `ARG BUILD_VERSION=` equal to that value.
   CI enforces App ↔ integration version equality.
4. Run `pytest` (includes the single-App-config guard + version lock).
5. Merge to `main`.
6. On HA: **Check for updates** → hard-refresh → **Update** PLCAssistant → restart Core
   so the synced thin integration reloads.

## Version lock (App ≡ integration)

The App and the bundled thin integration **always share one version string**.

| File | Field |
|------|-------|
| `plc_assistant/config.yaml` | `version` |
| `custom_components/plcassistant/manifest.json` | `version` |
| `plc_assistant/Dockerfile` | `ARG BUILD_VERSION=` (default equals config) |

Do not ship an App bump without the matching integration manifest bump (and vice versa).
After sync, `plc_assistant/custom_components/plcassistant/manifest.json` must match too.

### If Update does not change the installed version

On some HA OS releases, local-build Apps reuse **containerd/Docker layer cache**, so Update can finish while the container still runs old files (thin integration may keep pre-0.1.5 `hass.components` MQTT code).

Mitigations in-repo (0.1.7+):

- Dockerfile uses Supervisor `BUILD_VERSION` before `COPY` to invalidate layers on each `version` bump.
- App start force-syncs the thin integration when the App version stamp changes, and migrates any remaining `hass.components` subscribe path on disk.

Operator fallback: hard-refresh after **Check for updates**, restart Core after App Update, or `docker builder prune` then uninstall/reinstall.

### If Latest is stuck behind GitHub

When GitHub `main` already has a newer `plc_assistant/config.yaml` `version`, but HA still shows **Latest = installed** (for example both `0.1.6`):

1. Confirm the GitHub file version.
2. **Settings → Apps → ⋮ → Repositories** — if the URL is missing `#main`, remove it and re-add `https://github.com/marcuskrogh/PLCAssistant#main`, then hard-refresh and confirm **Latest**.
3. Otherwise: **Check for updates** → hard-refresh → **Restart Home Assistant Core** (Core update entities can lag ~15 minutes after a successful store reload).
4. If still stuck: remove/re-add `#main` again, then Check for updates + hard-refresh.
5. Inspect Supervisor logs for `Can't update` / corrupt-repository errors.

This is separate from the Docker layer-cache issue above. Either the store clone never advanced (Mode A), or Core’s update entity is still showing the pre-reload Latest (Mode B).

## Optional later improvement

Pre-building and publishing container images (`image:` in `config.yaml`) makes installs faster and avoids local build cache issues, but update discovery still uses the same `version` + Check for updates flow.
