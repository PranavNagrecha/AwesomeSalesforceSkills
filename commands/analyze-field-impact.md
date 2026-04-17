# /analyze-field-impact — Score the blast radius of renaming or deleting a field

Wraps [`agents/field-impact-analyzer/AGENT.md`](../agents/field-impact-analyzer/AGENT.md). Returns a risk-scored inventory of every place a field is referenced.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Object API name?
   Example: Account

2. Field API name?
   Example: Industry  (or Industry__c for custom fields)

3. Target org alias (required — live-org probe is mandatory)?
   Example: prod, uat, mydevsandbox

4. Intent: rename / delete / audit?
   (Changes severity thresholds; default = audit)

5. Repo path (optional)?
   Default: force-app/main/default
```

If `target_org_alias` is missing, STOP — the agent refuses without live-org access.

---

## Step 2 — Load the agent

Read `agents/field-impact-analyzer/AGENT.md` in full, plus every file under **Mandatory Reads Before Starting**.

---

## Step 3 — Execute the plan

Follow the 5-step plan exactly — confirm the field exists, enumerate repo references, enumerate org references via MCP tools (`list_flows_on_object`, `list_validation_rules`, `tooling_query`), score risk, propose mitigation.

---

## Step 4 — Deliver the output

Return the Output Contract block:
- Summary with P0/P1/P2 + confidence
- Reference inventory table
- Risk breakdown
- Mitigation plan (phased, no auto-patch)
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

Based on what the agent found, suggest (but do not auto-invoke):
- `/design-object` if model-level redesign is implied
- `/architect-perms` if FLS cleanup is surfaced
- `/preflight-load` if the field is in upcoming loads
- `/detect-drift` if the field appears in managed-package namespaces or unclear origins

---

## What this command does NOT do

- Does not rename, delete, or modify the field.
- Does not analyze more than one field per invocation.
- Does not deploy any metadata patch.
