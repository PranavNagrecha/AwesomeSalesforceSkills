# /consolidate-triggers — Consolidate N triggers on an sObject into one handler

Wraps [`agents/trigger-consolidator/AGENT.md`](../agents/trigger-consolidator/AGENT.md). Finds every trigger on a given sObject and produces a single-handler migration plan using `templates/apex/TriggerHandler.cls` + `TriggerControl.cls`.

---

## Step 1 — Collect inputs

Ask:

```
1. Which sObject should be consolidated?
   Example: Account, Opportunity, MyCustomObject__c

2. Path to your force-app tree?
   Default: force-app/main/default

3. Target-org alias (optional — enables an org-side trigger scan)
```

---

## Step 2 — Load the agent

Read `agents/trigger-consolidator/AGENT.md` fully and every file under its **Mandatory Reads Before Starting**.

---

## Step 3 — Execute

Follow the 5-step plan:
1. Discover triggers (local grep + optional `validate_against_org`)
2. Classify each trigger
3. Draft the consolidation (new handler class + replacement trigger file)
4. Metadata scaffolding (`Trigger_Setting__mdt` record)
5. Deactivation plan (ordered deployment steps)

---

## Step 4 — Deliver

Output per the agent's contract:
- Discovery table
- Proposed consolidation (full code blocks)
- Migration step sequence
- Risk notes (conflicting events, overlapping Flows)
- Citations

---

## Step 5 — Recommend follow-ups

After consolidation, recommend:
- `/analyze-flow` for the sObject to check for coexisting record-triggered flows
- `/refactor-apex` on the new handler to canonicalize its service/selector layers

---

## What this command does NOT do

- Does not refactor the business logic inside triggers — preserves verbatim.
- Does not deploy anything.
- Does not touch managed-package triggers.
