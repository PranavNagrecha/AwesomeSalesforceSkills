# /triage-apex-tests — Diagnose an existing Apex test run failure

Wraps [`agents/apex-test-failure-triager/AGENT.md`](../agents/apex-test-failure-triager/AGENT.md).

Read-only. Never starts a test run. Never uses `--use-most-recent`.

---

## Step 1 — Collect inputs

Need **exactly one** evidence source:

```
A. test_run_id (707…) and optional target-org alias
B. path to sf apex get test --json output
C. CI Apex test-result JSON with the same shape
```

Optional canonical input: `project_path` (aliases: `repo_path`, `source_path`). Passed as `project_dir` to `get_apex_test_run` when a DX project is known. Discovery from cwd / workspace roots is also supported; standalone mode is valid and diagnosis still runs. If discovery is `ambiguous`, stop guessing and ask for `project_path`.

Optional: `method_limit` to bound failing methods per page (default 100).

If the user says "the last test run" without a run id or file, STOP.

---

## Step 2 — Load the agent

Read `agents/apex-test-failure-triager/AGENT.md` and only the skills listed under Mandatory Reads, plus context-pack files selected from the result.

---

## Step 3 — Execute

Use Cursor subagents when this command runs inside the native plugin:

`org-grounder` → optional `project-inspector` → `context-librarian` → `apex-test-failure-triager` → `evidence-reviewer`.

Pass structured handoffs, not transcripts. Local project mapping is optional; do not block diagnosis when no DX project is found.

---

## Step 4 — Deliver

Structured diagnosis per the playbook, including evidence-review outcome.

---

## What this command does NOT do

- Does not start, schedule, or re-run Apex tests.
- Does not execute verification commands.
- Does not deploy or mutate org data.
