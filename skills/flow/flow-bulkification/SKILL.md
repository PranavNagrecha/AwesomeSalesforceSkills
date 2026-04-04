---
name: flow-bulkification
description: "Use when designing, reviewing, or troubleshooting Salesforce Flows that must survive data loads, integrations, or high-volume record changes without hitting transaction limits. Triggers: 'Get Records in loop', 'Flow bulkification', 'data loader causing flow errors', 'DML in loop', 'record-triggered flow scale'. NOT for general screen-flow UX or Flow type selection when scale is not the main risk."
category: flow
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Scalability
  - Performance
  - Reliability
tags:
  - flow-bulkification
  - governor-limits
  - record-triggered-flow
  - collections
  - scalability
triggers:
  - "flow is failing during data loads or imports"
  - "get records inside a loop in flow"
  - "record triggered flow hitting governor limits"
  - "how do I bulkify a flow for 200 records"
  - "after save flow creates too many updates"
inputs:
  - "flow type and trigger context"
  - "expected record volume per transaction or schedule"
  - "whether the flow queries or updates related records"
outputs:
  - "bulkification review findings"
  - "collection-based flow redesign guidance"
  - "decision on whether Flow should stay Flow or move to Apex"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when a Flow works for one record in a sandbox but becomes dangerous when data arrives in volume. The objective is to redesign the automation around collection handling, low-query patterns, and safe transaction scope before imports, integrations, or mass updates make it fail.

## Before Starting

- What is the maximum expected volume: user save, API batch, scheduled run, or bulk data load?
- Is the flow record-triggered, scheduled, autolaunched, or a subflow called from another bulk process?
- Which elements read or write related records, call Apex, or branch in loops?

## Core Concepts

### Record-Triggered Flows Still Consume Shared Limits

Flows are not exempt from Salesforce governor limits. A record-triggered flow can run in the same transaction budget as Apex, validation rules, and other automation. If the design assumes each interview is isolated, imports and integrations will expose the mistake quickly.

### Collection-First Design Beats Per-Record Thinking

The safe pattern is to collect identifiers, query once, shape data in memory, and write once where possible. The unsafe pattern is a `Loop` that performs `Get Records`, `Update Records`, or Apex actions for each iteration. Flow makes it visually easy to build the second pattern, which is why explicit review matters.

### Before-Save And After-Save Have Different Scale Costs

Before-save flows are the most efficient place to update fields on the triggering record because they avoid extra DML. After-save flows are necessary for related-record work, but they are more expensive and must be designed with far more caution under load.

### Bulkification Sometimes Means Escalating Out Of Flow

If the use case requires deep joins, heavy fan-out, callouts per record, or nightly processing across very large datasets, the correct bulkification answer may be Batch Apex, Queueable dispatch, Platform Events, or a scheduled integration rather than more Flow complexity.

## Common Patterns

### Query Once, Reuse In The Loop

**When to use:** The flow must compare or update child or sibling records for many triggering records.

**How it works:** Gather the relevant IDs, perform one `Get Records`, store the results in a collection, and reference that collection inside the loop instead of querying repeatedly.

**Why not the alternative:** `Get Records` inside a loop converts record volume directly into query count and fails under load.

### Build An Update Collection And Commit Once

**When to use:** The flow needs to update many related records.

**How it works:** Use assignments inside the loop to prepare a collection variable, then execute a single `Update Records` element after the loop.

**Why not the alternative:** Per-iteration DML burns row and statement limits and is harder to recover from when one record fails.

### Offload Heavy Work To Async Or Apex

**When to use:** The flow must do expensive work that does not belong in the saving transaction.

**How it works:** Use scheduled paths, a thin invocable Apex boundary, or an event-driven pattern so the flow remains a coordinator instead of the entire processing engine.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Update only fields on the triggering record | Before-save record-triggered flow | Lowest transaction cost |
| Update related records for many triggering records | After-save flow with collection pattern | Related DML requires after-save but must stay collection-based |
| Large nightly or imported dataset with complex joins | Batch Apex or async pattern | Flow becomes harder to bulkify than code at this scale |
| Loop contains queries, DML, or invocable Apex | Refactor immediately | This is the highest-risk Flow bulkification smell |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] No `Get Records`, `Create`, `Update`, `Delete`, or Apex action is executed per loop iteration without a justified exception.
- [ ] Before-save is used when only the triggering record needs field changes.
- [ ] Related-record writes are collected and committed intentionally.
- [ ] The design considers imports, integrations, and data-loader scenarios, not just one-click UI saves.
- [ ] Fault handling exists for the bulk path, not only the single-record happy path.
- [ ] The team explicitly decided whether Flow is still the right implementation at the expected scale.

## Salesforce-Specific Gotchas

1. **One import can trigger many interviews in one governor budget** — a flow that looks fine during manual testing can fail when 200 records arrive together.
2. **After-save updates on the same record are more expensive than before-save field changes** — using after-save for simple enrichment wastes transaction budget and can trigger more automation.
3. **Subflows do not magically bulkify a bad design** — moving a query-in-loop pattern into a subflow only hides it.
4. **Invocable Apex called from Flow still shares the transaction** — wrapping heavy work in Apex helps only if the Apex code is genuinely bulk-safe.

## Output Artifacts

| Artifact | Description |
|---|---|
| Bulkification review | Findings on loop design, query count risk, DML fan-out, and async boundaries |
| Flow redesign plan | Collection-based pattern or before-save/after-save refactor recommendation |
| Escalation decision | Guidance on whether the workload should stay in Flow or move to Apex |

## Related Skills

- `flow/record-triggered-flow-patterns` — use when the main question is before-save vs after-save behavior and entry criteria rather than scale mechanics.
- `flow/fault-handling` — use alongside this skill so the high-volume path fails predictably.
- `apex/governor-limits` — use when the safe answer is to move heavy processing into code.
