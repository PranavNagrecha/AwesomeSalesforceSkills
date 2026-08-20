# /compare-orgs — Multi-Org Drift Analysis

Wraps [`agents/multi-org-drift-analyzer/AGENT.md`](../agents/multi-org-drift-analyzer/AGENT.md).

Read-only. Never mutates Salesforce.

---

## Step 1 — Collect inputs

Required: **left_org_or_snapshot, right_org_or_snapshot**.

Optional: `result_path` (fixture JSON for `compare_org_snapshots`), `project_path`, `item_limit`.

If the user omits required identifiers, STOP. Do not guess.

---

## Step 2 — Load the agent

Read `agents/multi-org-drift-analyzer/AGENT.md` and only the skills listed under Mandatory Reads.

---

## Step 3 — Execute

Use Cursor subagents when this command runs inside the native plugin:

`org-grounder` → optional `project-inspector` → `context-librarian` → `multi-org-drift-analyzer` → `evidence-reviewer`.

Pass structured handoffs, not transcripts.

---

## Step 4 — Deliver

Structured diagnosis per the playbook, including evidence-review outcome.

---

## What this command does NOT do

- Does not mutate org data, metadata, or permissions.
- Does not execute verification commands.
