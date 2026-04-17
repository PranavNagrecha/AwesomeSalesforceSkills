# /design-lead-routing — Design or audit lead routing

Wraps [`agents/lead-routing-rules-designer/AGENT.md`](../agents/lead-routing-rules-designer/AGENT.md). Produces a routing matrix (source × geo × product → owner), queue + assignment rule design, territory layer, SLA wiring, and conversion handoff rules.

---

## Step 1 — Collect inputs

```
1. Mode?  design | audit
2. Target org alias (audit)?
3. Lead sources (design)?
4. Geographies (design)?
5. Products (optional)?
6. SLA per source (optional, minutes)?
```

## Step 2 — Load the agent

Read `agents/lead-routing-rules-designer/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Dimensioned matrix → queue vs user → territory → SLA → conversion handoff → dedup ordering → (audit) rule inventory.

## Step 4 — Deliver the output

Summary, routing matrix, queue + rule design, territory notes, SLA wiring, conversion rules, audit findings, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/design-duplicate-rule` (ordering: dedup BEFORE assignment)
- `/architect-perms` for queue membership PSGs

## What this command does NOT do

- Does not activate assignment rules.
- Does not create queues or public groups.
- Does not build round-robin Flows.
