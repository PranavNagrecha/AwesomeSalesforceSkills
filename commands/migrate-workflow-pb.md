# /migrate-workflow-pb — Migrate Workflow Rules + Process Builders to Flow

Wraps [`agents/workflow-and-pb-migrator/AGENT.md`](../agents/workflow-and-pb-migrator/AGENT.md). Inventories existing declarative automation on an object, produces a consolidated Flow design, and emits a parallel-run + rollback plan.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Object API name?
   Example: Opportunity

2. Target org alias (required — agent reads WF + PB metadata from the org)?

3. Consolidation mode? aggressive / conservative / auto
   - aggressive: one flow per object
   - conservative: one flow per original WF/PB (highest fidelity)
   - auto (default): group by trigger context

4. Include inactive WF/PBs in the migration? yes / no (default no)
```

---

## Step 2 — Load the agent

Read `agents/workflow-and-pb-migrator/AGENT.md` + mandatory reads. Note: Outbound Messages are unsupported — the agent refuses to migrate them.

---

## Step 3 — Execute the plan

1. Inventory existing WF + PB + related flows + triggers on the object
2. Classify each rule / process against the migration table
3. Apply consolidation mode
4. Emit the target flow design (with source + canon citations per element)
5. Parallel-run validation plan (default 7 business days)
6. Rollback plan

---

## Step 4 — Deliver the output

- Summary (WF + PB counts, target flow count, confidence)
- Inventory table
- Target flow design
- Unmigratable items (with explanation)
- Parallel-run plan (with concrete shadow-field + comparison query)
- Rollback plan
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/build-flow` to refine any specific migrated flow
- `/analyze-flow` post-cutover
- `/audit-validation-rules` to check VR vs migrated-flow conflicts
- `/detect-drift` (existing) for inactive rules still cluttering the object

---

## What this command does NOT do

- Does not activate or deactivate Workflow Rules, PBs, or Flows.
- Does not deploy metadata.
- Does not migrate Workflow Outbound Messages (unsupported path — documented in the agent).
- Does not generate rollback SQL/DML — the user owns data-fix after rollback.
