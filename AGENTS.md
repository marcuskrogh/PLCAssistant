# Agent instructions

<!-- marcuskrogh/skills:begin -->
**Prefer workflow.** When the user describes a feature, bug, problem, idea,
investigation, or follow-up — even without naming a skill — invoke
[`.agents/skills/workflows/SKILL.md`](.agents/skills/workflows/SKILL.md): infer
the supported pipeline, then load and run only that skill. Do not freestyle
coding or ad-hoc planning when a catalog workflow fits.

Continuation cues: bare **next** / **ship** still apply (see
`.agents/skills/workflow/reference.md`). Explicit `/skill` names win over
re-routing.

Authoring skills or concepts → [`.agents/skills/writing-for-agents/SKILL.md`](.agents/skills/writing-for-agents/SKILL.md).
<!-- marcuskrogh/skills:end -->

## Pipeline map

Skills are synced at cloud/environment startup from
[marcuskrogh/skills](https://github.com/marcuskrogh/skills) (not committed).
`.cursor/install.sh` and `.cursor/environment.json` `start` both run
`.agents/sync-skills.sh` so agents pick up latest `main` on setup/boot.

| Intent | Entry |
|--------|--------|
| Feature / initiative | `/explore` → `/define` → `/implement` → `/review-fix` → `/ship` (optional `/research` / `/model`) |
| Defect | `/bug` → `/implement` → `/review-fix` → `/ship` |
| Post-ship follow-up | `/iterate` → `/review-fix` → `/ship` |
| Status | `/summarise` |
| Workspace not set up | `/setup` |

Read `docs/agents/WORKSPACE.md` and `.agents/skills/workflow/reference.md` when running pipeline work.

**Only deviate** when no recognised workflow fits — for example a general question, a one-off explanation, or work clearly outside the feature / bug / iterate pipelines. Do not freestyle delivery (tickets, branches, PRs, reviews, ship) when a skill workflow applies.
