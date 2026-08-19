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

Optional: Salesforce DX project path for local mapping.

If the user says "the last deploy" without a job id or file, STOP.

---

## Step 2 — Load the agent

Read `agents/deployment-failure-triager/AGENT.md` and only the skills listed under Mandatory Reads, plus context-pack files selected from the result.

---

## Step 3 — Execute

Use Cursor subagents when this command runs inside the native plugin: org-grounder → context-librarian → repo-mapper → triager → evidence-reviewer. Pass structured handoffs, not transcripts.

---

## Step 4 — Deliver

Structured diagnosis per the playbook, including evidence-review outcome.

---

## What this command does NOT do

- Does not deploy, cancel, retry, or quick-deploy.
- Does not execute verification commands.
