# /review-security-posture — Security Posture Review

Wraps [`agents/security-posture-reviewer/AGENT.md`](../agents/security-posture-reviewer/AGENT.md).

Read-only. Never mutates Salesforce.

---

## Step 1 — Collect inputs

Required: **scope**.

Optional: `result_path` (fixture JSON for `get_code_analysis_result`), `project_path`, `item_limit`.

If the user omits required identifiers, STOP. Do not guess.

---

## Step 2 — Load the agent

Read `agents/security-posture-reviewer/AGENT.md` and only the skills listed under Mandatory Reads.

---

## Step 3 — Execute

Use Cursor subagents when this command runs inside the native plugin:

`org-grounder` → optional `project-inspector` → `context-librarian` → `security-posture-reviewer` → `evidence-reviewer`.

Pass structured handoffs, not transcripts.

---

## Step 4 — Deliver

Structured diagnosis per the playbook, including evidence-review outcome.

---

## What this command does NOT do

- Does not mutate org data, metadata, or permissions.
- Does not execute verification commands.
