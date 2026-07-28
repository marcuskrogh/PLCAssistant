# 04 — App updates (Supervisor store)

**Plan:** [`docs/PLAN.md`](../PLAN.md) · Shape: [`01-shape.md`](01-shape.md)

## How Supervisor learns about a new version

Custom GitHub App repositories are **pulled on demand**, not watched.

1. Developer bumps `version` in [`plc_assistant/config.yaml`](../../plc_assistant/config.yaml) and merges to `main`.
2. On the HA host: **Settings → Apps → ⋮ → Check for updates** → Supervisor `git pull`s the repo.
3. Supervisor compares **installed** `version` to the store copy of `config.yaml`.
4. If they differ, the App detail page shows **Update**.

Hard-refresh the browser after step 2 (store UI is often cached).

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
3. Bump **`version`** in `plc_assistant/config.yaml` (required for the Update button).
4. Run `pytest` (includes the single-App-config guard).
5. Merge to `main`.
6. On HA: **Check for updates** → hard-refresh → **Update** PLCAssistant.

No repository remove/re-add should be required when the invariant holds.

## Optional later improvement

Pre-building and publishing container images (`image:` in `config.yaml`) makes installs faster, but update discovery still uses the same `version` + Check for updates flow.
