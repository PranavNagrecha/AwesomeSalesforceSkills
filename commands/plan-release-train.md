# /plan-release-train — Plan or audit a Salesforce release train

Wraps [`agents/release-train-planner/AGENT.md`](../agents/release-train-planner/AGENT.md). Produces package strategy, branching model, environment promotion path, release calendar, CI/CD gates, and hotfix playbook.

---

## Step 1 — Collect inputs

```
1. Mode?  design | audit
2. Team size?
3. Release cadence?  weekly / biweekly / monthly / quarterly
4. Package strategy (optional)?  unlocked / 2gp-managed / org-dependent / metadata-only
5. Customer count (optional)?  1 for internal, N for ISV
6. Regions (optional)?
```

## Step 2 — Load the agent

Read `agents/release-train-planner/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Package choice → branching model → environment path → calendar (with Platform freezes) → CI/CD gates → hotfix → (audit) git diff vs stated model.

## Step 4 — Deliver the output

Summary, package strategy, branching model, promotion table, 180-day calendar, CI/CD gates, hotfix playbook, audit findings, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/design-sandbox-strategy` for refresh cadence alignment
- `/assess-waf` for NFR coverage

## What this command does NOT do

- Does not cut branches, tag releases, or deploy packages.
- Does not run CI pipelines.
- Does not set up DevOps tooling (plan only).
