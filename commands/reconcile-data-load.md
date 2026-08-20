# /reconcile-data-load — Data Migration Reconciliation

Wraps [`agents/data-migration-reconciler/AGENT.md`](../agents/data-migration-reconciler/AGENT.md).

Read-only. Never mutates Salesforce.

---

## Step 1 — Collect inputs

Required: **migration_manifest, result_files**.

Optional: `result_path` (fixture JSON for `get_data_load_result`), `project_path`, `item_limit`.

If the user omits required identifiers, STOP. Do not guess.

---

## Step 2 — Load the agent

Read `agents/data-migration-reconciler/AGENT.md` and only the skills listed under Mandatory Reads.

---

## Step 3 — Execute

Use Cursor subagents when this command runs inside the native plugin:

`org-grounder` → optional `project-inspector` → `context-librarian` → `data-migration-reconciler` → `evidence-reviewer`.

Pass structured handoffs, not transcripts.

---

## Step 4 — Deliver

Structured diagnosis per the playbook, including evidence-review outcome.

---

## What this command does NOT do

- Does not mutate org data, metadata, or permissions.
- Does not execute verification commands.
