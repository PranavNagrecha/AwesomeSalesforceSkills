# /govern-picklists — Govern picklist hygiene on an sObject (or org)

Wraps [`agents/picklist-governor/AGENT.md`](../agents/picklist-governor/AGENT.md). GVS adoption, inactive-value drift, translation coverage, dependent-picklist chains, integration-usage probe.

---

## Step 1 — Collect inputs

```
1. Scope?  object:<ApiName>  OR  org
2. Target org alias?
3. Include inactive values? yes (default) / no
```

## Step 2 — Load the agent

Read `agents/picklist-governor/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Inventory picklists + GVS, score each, usage probe, emit consolidation plan.

## Step 4 — Deliver the output

Summary, per-picklist findings, dependency graph, consolidation plan, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/audit-record-types` if RT-level picklist filtering is implicated
- `/analyze-field-impact` for any picklist whose values drive downstream integrations

## What this command does NOT do

- Does not modify picklist values in the org.
- Does not deploy GVS migrations.
- Does not clean data rows with invalid picklist values.
