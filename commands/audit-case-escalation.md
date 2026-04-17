# /audit-case-escalation — Audit Case escalation surface

Wraps [`agents/case-escalation-auditor/AGENT.md`](../agents/case-escalation-auditor/AGENT.md). Scores assignment + escalation rules, entitlement coverage, milestone instrumentation, and ownership black-holes. Produces a prioritized remediation backlog.

---

## Step 1 — Collect inputs

```
1. Target org alias?
2. Scope?  org (default) | record_type:Case.<RT>
3. Customer segments (optional)?  basic / premium / enterprise
```

## Step 2 — Load the agent

Read `agents/case-escalation-auditor/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Inventory → coverage analysis → black-hole probe → escalation-action correctness → milestone instrumentation → remediation backlog.

## Step 4 — Deliver the output

Summary, coverage table, findings, remediation backlog, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/design-lead-routing` if assignment fabric is compromised
- `/audit-sharing` if ownership reassignment reveals visibility holes

## What this command does NOT do

- Does not modify rules, entitlements, or milestones.
- Does not stop/start milestone timers.
- Does not size headcount.
