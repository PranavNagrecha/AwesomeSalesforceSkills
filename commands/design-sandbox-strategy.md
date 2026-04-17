# /design-sandbox-strategy — Design or audit sandbox + scratch-org strategy

Wraps [`agents/sandbox-strategy-designer/AGENT.md`](../agents/sandbox-strategy-designer/AGENT.md). Produces environment ladder, scratch-org pool configs, refresh calendar with blackouts, and masking plan per data-sensitivity class.

---

## Step 1 — Collect inputs

```
1. Mode?  design | audit
2. Target org alias (prod, for audit)?
3. Team size?  { developers, admins, qa }
4. Concurrent workstreams?
5. Release cadence?  weekly / biweekly / monthly / quarterly
6. Data sensitivity?  pii / phi / pci / none
```

## Step 2 — Load the agent

Read `agents/sandbox-strategy-designer/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Workstream → sandbox mapping → scratch pool sizing → refresh cadence + blackouts → masking/seeding → templates → (audit) usage diff.

## Step 4 — Deliver the output

Summary, environment ladder, pool configs, calendar, masking plan, audit findings, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/plan-release-train` for cadence alignment
- `/assess-waf` for HA/DR posture

## What this command does NOT do

- Does not provision, refresh, or delete sandboxes.
- Does not run masking operations.
- Does not purchase sandbox licenses.
