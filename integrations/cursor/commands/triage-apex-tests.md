---
name: triage-apex-tests
description: Diagnose an existing Apex test run failure from a test run ID (707…) or a local CLI JSON fixture. Read-only. Never starts a test run.
---

# /triage-apex-tests

Coordinate these Cursor subagents in order. Pass structured handoffs only (no transcripts):

1. `sf-org-grounder` — fixture file **or** `get_apex_test_run(test_run_id, target_org, project_dir?)`
2. `sf-project-inspector` — **optional** local DX project discovery / file mapping (skippable when standalone)
3. `sf-context-librarian` — select ≤8 domain skill/reference files (hard limit 12) using P02 apex failure kinds
4. `apex-test-failure-triager` — diagnose (works without `project_path` / `source_path`)
5. `sf-evidence-reviewer` — reject unsupported/unsafe claims

Then follow `agents/apex-test-failure-triager/AGENT.md` output contract.

## Collect inputs (do not guess a run ID)

Need **one** of:

- **A.** `test_run_id` (707…) and optional `target_org` alias
- **B.** Path to `sf apex get test --json` output (`result_path` or `result_file`)
- **C.** A supported CI Apex test-result JSON with the same shape

Optional canonical input: `project_path` (aliases: `repo_path`, `source_path`). When omitted, run project discovery from cwd or bounded workspace roots. `standalone` continues diagnosis without local mapping. `ambiguous` must not guess — ask for `project_path`.

Optional: `method_limit` for paginated failing methods.

If the user says "latest test run" or omits a run ID without a file, **refuse**. Do not pass `--use-most-recent`.

## Safety

Do not run `sf apex run test`, `sf apex run`, or deploy commands.
Show verification commands; do not execute them.

## Persistence

Write redacted telemetry under `.sfskills/runs/<run_id>/` (gitignored). Prefer envelope paths allowed by the product contract.
