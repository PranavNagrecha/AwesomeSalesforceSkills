# /audit-reports — Audit reports and dashboards for a folder or org

Wraps [`agents/report-and-dashboard-auditor/AGENT.md`](../agents/report-and-dashboard-auditor/AGENT.md). Flags stale reports, unfiltered wide scans, dashboard running-user leakage, subscription abuse, folder sprawl.

---

## Step 1 — Collect inputs

```
1. Scope?  folder:<DeveloperName>  OR  org
2. Target org alias?
```

## Step 2 — Load the agent

Read `agents/report-and-dashboard-auditor/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Inventory reports + dashboards + folders + subscriptions, score each, folder sprawl analysis, emit findings + cleanup.

## Step 4 — Deliver the output

Summary, per-report findings, per-dashboard findings, folder-sprawl analysis, cleanup suggestions, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/audit-sharing` if dashboard running-user leakage is the main story
- `/analyze-field-impact` before deleting fields used only by stale reports

## What this command does NOT do

- Does not delete or modify reports/dashboards/folders.
- Does not change subscription recipients.
- Does not build new reports.
