# Agent instructions

## Prefer skills workflows

Always prefer a recognised workflow from the synced skills in `.agents/skills/` (from [marcuskrogh/skills](https://github.com/marcuskrogh/skills)).

| Intent | Entry |
|--------|--------|
| Feature / initiative | `/explore` → `/define` → `/implement` → `/review-fix` → `/ship` (optional `/research` / `/model`) |
| Defect | `/bug` → `/implement` → `/review-fix` → `/ship` |
| Post-ship follow-up | `/iterate` → `/review-fix` → `/ship` |
| Status | `/summarise` |
| Workspace not set up | `/setup` |

Read `docs/agents/WORKSPACE.md` and `.agents/skills/workflow/reference.md` when running pipeline work. Continuation cues **`next`** (one step) and **`ship`** (finish remaining) follow that contract.

**Only deviate** when no recognised workflow fits — for example a general question, a one-off explanation, or work clearly outside the feature / bug / iterate pipelines. Do not freestyle delivery (tickets, branches, PRs, reviews, ship) when a skill workflow applies.
