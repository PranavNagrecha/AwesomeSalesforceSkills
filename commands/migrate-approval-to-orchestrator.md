# /migrate-approval-to-orchestrator — Migrate Approval Processes to Flow Orchestrator

Wraps [`agents/approval-to-flow-orchestrator-migrator/AGENT.md`](../agents/approval-to-flow-orchestrator-migrator/AGENT.md). Classifies each approval process, produces Orchestrator design for candidates, plus parallel-run + rollback.

---

## Step 1 — Collect inputs

```
1. Object API name?
2. Target org alias?
3. process_id (optional — else all active approvals on the object)?
```

## Step 2 — Load the agent

Read `agents/approval-to-flow-orchestrator-migrator/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Inventory approvals, classify migration fitness, design Orchestrator per candidate, parallel-run plan, rollback plan.

## Step 4 — Deliver the output

Summary, classification table, per-candidate Orchestrator design, parallel-run plan, rollback plan, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/build-agentforce-action` (existing Wave-1) for approvals re-homed to Agentforce
- `/build-flow` for orchestrator stage subflows

## What this command does NOT do

- Does not activate or deactivate approval processes.
- Does not deploy Orchestrator metadata.
- Does not migrate regulatory-dependent approvals without a compliance review.
