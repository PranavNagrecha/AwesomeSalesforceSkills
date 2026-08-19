---
name: triage-deployment
description: Diagnose an existing Salesforce deployment failure from a job ID or a local CLI JSON fixture. Read-only. Never starts a deploy.
---

# /triage-deployment

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `get_deployment_result(job_id, target_org, project_dir?)`
2. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12)
3. `sf-repo-mapper` — map components to the user-supplied DX project path
4. `deployment-failure-triager` — diagnose
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/deployment-failure-triager/AGENT.md` output contract.

## Collect inputs (do not guess a job ID)

Need **one** of:

- **A.** `job_id` (0Af…) and optional `target_org` alias
- **B.** Path to `sf project deploy report --json` output
- **C.** A supported CI deploy-result JSON with the same DeployResult shape

Also ask for the Salesforce DX project path when local mapping is required.

If the user says "latest deploy" or omits a job ID without a file, **refuse**. Do not pass `--use-most-recent`.

## Safety

Do not run `sf project deploy start|validate|quick|cancel|resume`.
Show verification commands; do not execute them.

## Persistence

Write redacted telemetry under `.sfskills/runs/<run_id>/` (gitignored). Prefer envelope paths allowed by the product contract.
