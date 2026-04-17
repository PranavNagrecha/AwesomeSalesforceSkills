# /design-sales-stages — Design or audit Opportunity sales stages

Wraps [`agents/sales-stage-designer/AGENT.md`](../agents/sales-stage-designer/AGENT.md). Produces a stage ladder with probabilities, forecast categories, exit criteria, Path + validation-rule gates.

---

## Step 1 — Collect inputs

```
1. Mode?  design | audit
2. Target org alias (audit)?
3. Business motion (design)?  e.g. new-logo SaaS, renewal, professional services
4. Avg cycle length in days (design)?
5. Record type (optional)?
```

## Step 2 — Load the agent

Read `agents/sales-stage-designer/AGENT.md` + mandatory reads, including `templates/admin/validation-rule-patterns.md`.

## Step 3 — Execute the plan

Size the ladder → forecast-category mapping → stage-gate fields → Path + VRs → history tracking → Forecasts wiring → (audit) cross-check.

## Step 4 — Deliver the output

Summary, stage-ladder table, VRs + Path, Forecasts notes, audit findings, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/audit-reports` for pipeline review coverage
- `/design-lead-routing` for top-of-funnel alignment

## What this command does NOT do

- Does not deploy stages, VRs, or Path configs.
- Does not build pipeline reports/dashboards.
- Does not train sales reps.
