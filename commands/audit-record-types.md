# /audit-record-types — Audit Record Types + Page Layouts

Wraps [`agents/record-type-and-layout-auditor/AGENT.md`](../agents/record-type-and-layout-auditor/AGENT.md). Identifies record-type proliferation, Master Layout as primary, orphan RTs, and LRP mapping gaps.

---

## Step 1 — Collect inputs

```
1. Object API name?
2. Target org alias?
```

## Step 2 — Load the agent

Read `agents/record-type-and-layout-auditor/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Inventory RTs + layouts + assignments, score against patterns, LRP mapping check, emit findings + remediation.

## Step 4 — Deliver the output

Summary, record type table, findings table, remediation suggestions, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/audit-record-page` for the Lightning Record Page layer
- `/govern-picklists` if picklist drift is the main story

## What this command does NOT do

- Does not activate/deactivate record types.
- Does not modify layouts or LRPs.
- Does not redesign picklist values.
