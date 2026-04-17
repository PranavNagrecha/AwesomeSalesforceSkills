# /audit-sharing — Audit the org's record-level access model

Wraps [`agents/sharing-audit-agent/AGENT.md`](../agents/sharing-audit-agent/AGENT.md). Returns OWD + sharing-rule findings, data-skew hot-list, recalc-cost estimate, and Experience Cloud guest exposure.

---

## Step 1 — Collect inputs

```
1. Scope?  object:<ApiName>  OR  org
2. Target org alias (required)?
```

## Step 2 — Load the agent

Read `agents/sharing-audit-agent/AGENT.md` + mandatory reads, including `standards/decision-trees/sharing-selection.md`.

## Step 3 — Execute the plan

Fetch model, classify per decision tree, data-skew probe, guest-user probe, recalc-cost estimate, emit findings.

## Step 4 — Deliver the output

Summary, model snapshot, findings table, data-skew hot-list, recalc-cost estimate, guest-user exposure, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/architect-perms` for persona-level access gaps
- `/review-data-model` if cross-object cascade is the real problem

## What this command does NOT do

- Does not modify OWD or sharing rules.
- Does not design persona-level FLS.
- Does not fix data skew (flags; remediation is separate).
