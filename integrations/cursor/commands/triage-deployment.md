---
name: triage-deployment
description: Diagnose an existing Salesforce deployment failure from a job ID or a local CLI JSON fixture. Read-only. Never starts a deploy.
---

# /triage-deployment

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `get_deployment_result(job_id, target_org, project_dir?)`
2. `sf-project-inspector` — **optional** local DX project discovery / file mapping (skippable when standalone)
3. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12)
4. `deployment-failure-triager` — diagnose (works without `project_path` / `source_path`)
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/deployment-failure-triager/AGENT.md` output contract.

## Collect inputs (do not guess a job ID)

Need **one** of:

- **A.** `job_id` (0Af…) and optional `target_org` alias
- **B.** Path to `sf project deploy report --json` output
- **C.** A supported CI deploy-result JSON with the same DeployResult shape

Optional canonical input: `project_path` (aliases: `repo_path`, `source_path`). When omitted, run project discovery from cwd or bounded workspace roots. `standalone` continues diagnosis without local mapping. `ambiguous` must not guess — ask for `project_path`.

If the user says "latest deploy" or omits a job ID without a file, **refuse**. Do not pass `--use-most-recent`.

## Safety

Do not run `sf project deploy start|validate|quick|cancel|resume`.
Show verification commands; do not execute them.

## Persistence

Write redacted telemetry under `.sfskills/runs/<run_id>/` (gitignored). Prefer envelope paths allowed by the product contract.
