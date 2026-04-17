# /analyze-flow — Flow vs Apex routing + bulkification review

Wraps [`agents/flow-analyzer/AGENT.md`](../agents/flow-analyzer/AGENT.md). For a Flow or an sObject, routes via `standards/decision-trees/automation-selection.md`, checks bulkification, and flags trigger/flow co-existence risks.

---

## Step 1 — Collect inputs

Ask:

```
1. Either a Flow path or an sObject API name?
   Example flow path: force-app/main/default/flows/Lead_AutoConvert.flow-meta.xml
   Example object:    Lead

2. Target-org alias? (optional — enables list_flows_on_object)
```

If the user gave a flow path, skip the object question. If they gave an object, scan `force-app/main/default/flows/` for matching flows.

---

## Step 2 — Load the agent

Read `agents/flow-analyzer/AGENT.md` fully + the automation decision tree + flow skills listed in **Mandatory Reads**.

---

## Step 3 — Execute

Follow the 5-step plan:
1. Gather flows in scope (local + optional org-side via `list_flows_on_object`)
2. Apply the automation decision tree to each flow (KEEP / FIX_IN_PLACE / MIGRATE_TO_APEX / MIGRATE_TO_AGENTFORCE)
3. Bulkification checks (DML/SOQL in loops, missing fault paths, untyped collections)
4. Co-existence check (trigger + flow on same event)
5. Recommendations with specific element changes

---

## Step 4 — Deliver

- Summary with verdict distribution
- Per-flow report (verdict, decision-tree branch, findings, fixes)
- Co-existence section if triggers + flows overlap
- Citations

---

## Step 5 — Recommend follow-ups

- `/consolidate-triggers` if co-existence is flagged and Apex should own the event.
- `/refactor-apex` if a flow should migrate to Apex — applied to the new handler.
- `/request-skill` if a flow pattern has no canonical skill.

---

## What this command does NOT do

- Does not modify the flow XML.
- Does not activate or deactivate flows in the org.
- Does not pass judgment on Flow vs Apex outside the decision tree.
