# /audit-record-page — Audit Lightning Record Pages on an sObject

Wraps [`agents/lightning-record-page-auditor/AGENT.md`](../agents/lightning-record-page-auditor/AGENT.md). Scores pages for Dynamic Forms, render cost, related-list strategy, Path, and custom-LWC weight.

---

## Step 1 — Collect inputs

```
1. Object API name?
2. Target org alias?
```

## Step 2 — Load the agent

Read `agents/lightning-record-page-auditor/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Inventory record pages, fetch content, score each page, check page assignments, emit per-page + org-level.

## Step 4 — Deliver the output

Summary, per-page findings, org-level metrics, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/audit-record-types` for the underlying page-layout layer
- `/audit-lwc` (existing Wave-1) for any custom LWCs surfaced

## What this command does NOT do

- Does not modify or deploy record pages.
- Does not do deep LWC analysis (use `/audit-lwc`).
