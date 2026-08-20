# /triage-deployment — Diagnose an existing Salesforce deploy failure

Wraps [`agents/deployment-failure-triager/AGENT.md`](../agents/deployment-failure-triager/AGENT.md).

Read-only. Never starts a deploy. Never uses `--use-most-recent`.

---

## Step 1 — Collect inputs

Need **exactly one** evidence source:

```
A. job_id (0Af…) and optional target-org alias
B. path to sf project deploy report --json
C. CI DeployResult JSON with the same shape
```

Optional canonical input: `project_path` (aliases: `repo_path`, `source_path`). Passed as `project_dir` to `get_deployment_result` when a DX project is known. Discovery from cwd / workspace roots is also supported; standalone mode is valid and diagnosis still runs. If discovery is `ambiguous`, stop guessing and ask for `project_path`.

If the user says "the last deploy" without a job id or file, STOP.

---

## Step 2 — Load the agent

Read `agents/deployment-failure-triager/AGENT.md` and only the skills listed under Mandatory Reads, plus context-pack files selected from the result.

---

## Step 3 — Execute

Use Cursor subagents when this command runs inside the native plugin:

`org-grounder` → optional `project-inspector` → `context-librarian` → `deployment-failure-triager` → `evidence-reviewer`.

Pass structured handoffs, not transcripts. Local project mapping is optional; do not block diagnosis when no DX project is found.

---

## Step 4 — Deliver

Structured diagnosis per the playbook, including evidence-review outcome.

---

## What this command does NOT do

- Does not deploy, cancel, retry, or quick-deploy.
- Does not execute verification commands.
