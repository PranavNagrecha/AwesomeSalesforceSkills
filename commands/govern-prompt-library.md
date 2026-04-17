# /govern-prompt-library — Govern Prompt Builder template library

Wraps [`agents/prompt-library-governor/AGENT.md`](../agents/prompt-library-governor/AGENT.md). Inventory, duplicate detection, grounding citation checks, Trust Layer alignment, owner + version hygiene, usage report, and consolidation plan.

---

## Step 1 — Collect inputs

```
1. Target org alias?
2. Scope?  all (default) | type:FieldGeneration | type:EmailGeneration | type:Flex | ...
```

## Step 2 — Load the agent

Read `agents/prompt-library-governor/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Inventory → dedupe → grounding checks → Trust Layer alignment → owner/version hygiene → usage → consolidation plan.

## Step 4 — Deliver the output

Summary, inventory, duplicate clusters, grounding + Trust Layer gaps, consolidation plan, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/review-agentforce-action` if templates are consumed by agent actions
- `/catalog-integrations` if templates trigger callouts

## What this command does NOT do

- Does not modify, activate, or deprecate templates.
- Does not rewrite prompts.
- Does not change model selection.
