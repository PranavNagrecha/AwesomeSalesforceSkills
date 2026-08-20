# /triage-integration — Integration Incident Triage

Wraps [`agents/integration-incident-triager/AGENT.md`](../agents/integration-incident-triager/AGENT.md).

Read-only. Never mutates Salesforce.

---

## Step 1 — Collect inputs

Required: **integration, time_window**.

Optional: `result_path` (fixture JSON for `get_integration_config_summary`), `project_path`, `item_limit`.

If the user omits required identifiers, STOP. Do not guess.

---

## Step 2 — Load the agent

Read `agents/integration-incident-triager/AGENT.md` and only the skills listed under Mandatory Reads.

---

## Step 3 — Execute

Use Cursor subagents when this command runs inside the native plugin:

`org-grounder` → optional `project-inspector` → `context-librarian` → `integration-incident-triager` → `evidence-reviewer`.

Pass structured handoffs, not transcripts.

---

## Step 4 — Deliver

Structured diagnosis per the playbook, including evidence-review outcome.

---

## What this command does NOT do

- Does not mutate org data, metadata, or permissions.
- Does not execute verification commands.
