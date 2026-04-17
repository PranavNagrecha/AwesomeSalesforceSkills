# /review-data-model — Review a data-model domain

Wraps [`agents/data-model-reviewer/AGENT.md`](../agents/data-model-reviewer/AGENT.md). Reviews relationships, rollups, External ID coverage, growth forecast, and index candidacy for a root object + its related objects.

---

## Step 1 — Collect inputs

```
1. Root object API name?  (e.g. Opportunity)
2. Target org alias?
3. Include related objects? (Optional — default: infer from EntityDefinition relationships)
```

## Step 2 — Load the agent

Read `agents/data-model-reviewer/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Build domain graph, score relationships, rollup analysis, External ID coverage, growth forecast, index candidacy, emit.

## Step 4 — Deliver the output

Summary, domain graph (ASCII), findings, rollup analysis, growth forecast, index recommendations, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/design-object` for new objects suggested by the review
- `/analyze-field-impact` for External ID rollout
- `/audit-sharing` if cascade behavior is unclear

## What this command does NOT do

- Does not modify relationships or deploy anything.
- Does not design new objects (suggests `/design-object`).
- Does not analyze sharing cascading (suggests `/audit-sharing`).
