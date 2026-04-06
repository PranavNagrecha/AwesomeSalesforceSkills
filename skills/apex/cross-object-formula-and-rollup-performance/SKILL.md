---
name: cross-object-formula-and-rollup-performance
description: "Use when diagnosing or preventing performance problems caused by cross-object formula spanning relationships and roll-up summary field recalculations — especially in LDV orgs. Triggers: 'roll-up summary timing stale in trigger', 'Maximum 15 object references error', 'rollup recalculation timeout on large child set'. NOT for formula syntax authoring (use admin/formula-fields), formula compile-size limits (use apex/formula-field-performance-and-limits), or general governor-limit troubleshooting."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Reliability
tags:
  - cross-object-formula
  - rollup-summary
  - spanning-relationships
  - ldv
  - performance
  - order-of-execution
  - record-locking
triggers:
  - "roll-up summary field shows stale value inside after-update trigger"
  - "Maximum 15 object references error when adding a cross-object formula"
  - "rollup recalculation timing out on large child object with 300k+ records"
  - "cross-object formula not updating when distant parent record changes"
  - "REQUEST_RUNNING_TOO_LONG during rollup recalculation on non-indexed filter field"
inputs:
  - "Object relationship diagram showing parent-child and lookup chains involved"
  - "List of cross-object formula fields and rollup summary fields on the affected objects"
  - "Approximate child record volume per parent for rollup objects"
  - "Whether triggers read rollup values in the same transaction as child DML"
outputs:
  - "Spanning relationship inventory with count against the 15-reference limit"
  - "Rollup timing analysis identifying stale-read risks in triggers"
  - "Recommendation to replace native rollup with Apex or Flow alternative when LDV thresholds are exceeded"
  - "Indexed-field strategy for rollup filter criteria on high-volume objects"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Cross-Object Formula and Rollup Performance

You are a Salesforce performance expert focused on cross-object formula spanning relationships and roll-up summary field recalculation behavior. Use this skill when cross-object formulas hit the spanning limit, rollup values appear stale inside triggers, or rollup recalculations time out on large data volumes.

---

## Before Starting

Gather this context before working on anything in this domain:

- How many unique spanning relationships already exist on the object? The hard limit is 15 per object across all formula fields, validation rules, and workflow rules combined.
- Are any triggers or flows reading parent rollup values in the same transaction that modifies child records? Rollups recalculate at step 13 of the save order, so trigger-time reads see the pre-recalculation value.
- What is the child record volume per parent? Full rollup recalculation on 300k+ children with non-indexed filter criteria risks REQUEST_RUNNING_TOO_LONG.

---

## Core Concepts

### Spanning Relationship Limit

Every cross-object formula reference (e.g., `Opportunity.Account.Owner.Profile.Name`) counts each unique lookup relationship it traverses toward the per-object cap. The limit is 15 unique spanning relationships per object, aggregated across all formula fields, validation rules, workflow field updates, and flows that use cross-object references on that object. Salesforce Support can raise this to a maximum of 20 via case request, but no higher. Adding a new formula that would exceed the cap fails at save time with "Maximum 15 object references" or the equivalent error.

### Rollup Recalculation Timing in the Save Order

Roll-up summary fields recalculate at step 13 of the Salesforce order of execution — after all before and after triggers on the child record, after workflow field updates, and after flow automations. This means any Apex trigger on the parent or child that reads the rollup value during the same transaction sees the old (pre-recalculation) value. The updated value is only available after the parent record's own save cycle completes.

### Rollup Filter Criteria and Distant Cross-Object References

Rollup summary fields support filter criteria, but filters that reference cross-object formula fields on the child do not re-trigger recalculation when the distant referenced record changes. For example, if a rollup filters on a child formula field that reads a grandparent value, editing the grandparent does not cause the rollup to recalculate. The rollup only recalculates when the direct child record is inserted, updated, deleted, or undeleted.

### LDV Rollup Recalculation Timeout

When a parent's rollup must scan 300,000+ child records and the filter criteria reference non-indexed fields, Salesforce may throw REQUEST_RUNNING_TOO_LONG. The platform performs a full recalculation rather than an incremental one when filter criteria are involved, so the query must touch every qualifying child row.

---

## Common Patterns

### Pattern 1: Spanning Relationship Inventory Audit

**When to use:** Before adding a new cross-object formula or when the "Maximum 15 object references" error appears.

**How it works:**

1. Query all formula fields on the object via Tooling API: `SELECT Id, TableEnumOrId, Formula FROM CustomField WHERE TableEnumOrId = 'ObjectName' AND Formula != null`.
2. Parse each formula for dot-notated cross-object references (e.g., `Account.Owner.Name`).
3. Extract the unique relationship paths — each unique lookup hop counts as one spanning relationship.
4. Sum spanning relationships across formula fields, validation rules (query `ValidationRule` via Tooling API), and workflow field updates.
5. Compare the total against the 15-reference limit. If above 12, flag as high risk.

**Why not the alternative:** Manually reviewing formulas in Setup is error-prone because the count is cumulative across multiple metadata types, not visible in a single UI.

### Pattern 2: Deferred Rollup Read via Async Apex

**When to use:** When a trigger on the child or parent must read the updated rollup value and act on it.

**How it works:**

1. In the after trigger, enqueue a Queueable that accepts the parent record IDs.
2. The Queueable runs in a new transaction, after rollup recalculation has completed.
3. Re-query the parent to get the fresh rollup value, then execute the dependent logic.

```apex
public class RollupDependentAction implements Queueable {
    private Set<Id> parentIds;
    public RollupDependentAction(Set<Id> parentIds) {
        this.parentIds = parentIds;
    }
    public void execute(QueueableContext ctx) {
        List<Account> parents = [
            SELECT Id, Total_Amount__c  // rollup field
            FROM Account
            WHERE Id IN :parentIds
        ];
        // Now Total_Amount__c reflects the completed recalculation
        for (Account a : parents) {
            if (a.Total_Amount__c > 1000000) {
                // downstream logic
            }
        }
    }
}
```

**Why not the alternative:** Reading the rollup in the same trigger transaction returns the stale pre-recalculation value. Future methods work but cannot be chained or accept SObject parameters.

### Pattern 3: Apex-Managed Rollup for LDV Objects

**When to use:** When native rollup recalculations time out on objects with 300k+ children, or when rollup filter criteria require non-indexed field evaluation.

**How it works:**

1. Remove the native rollup summary field.
2. Create a stored number/currency field on the parent to hold the calculated value.
3. Write an after-insert, after-update, after-delete, after-undelete trigger on the child that incrementally adjusts the parent field value.
4. Use `FOR UPDATE` on the parent query to prevent concurrent updates from creating race conditions.
5. For complex filters, evaluate the filter in Apex where you control indexing and query selectivity.

```apex
// Incremental rollup in child after-insert trigger
Map<Id, Decimal> deltas = new Map<Id, Decimal>();
for (OpportunityLineItem oli : Trigger.new) {
    Decimal current = deltas.containsKey(oli.OpportunityId)
        ? deltas.get(oli.OpportunityId) : 0;
    deltas.put(oli.OpportunityId, current + oli.TotalPrice);
}
List<Opportunity> parents = [
    SELECT Id, Custom_Total__c
    FROM Opportunity
    WHERE Id IN :deltas.keySet()
    FOR UPDATE
];
for (Opportunity opp : parents) {
    opp.Custom_Total__c = (opp.Custom_Total__c == null ? 0 : opp.Custom_Total__c)
        + deltas.get(opp.Id);
}
update parents;
```

**Why not the alternative:** Native rollups perform full recalculations when filter criteria exist. On LDV objects this causes timeouts. The incremental Apex approach touches only the delta.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Object nearing 15 spanning relationships | Consolidate formulas or replace cross-object formulas with stored fields synced via Flow/trigger | Prevents hard save-time failure when limit is exceeded |
| Trigger needs to read updated rollup value | Enqueue Queueable to read rollup in a new transaction | Rollup recalculates at step 13 — trigger sees stale value |
| Rollup on object with 300k+ children | Replace native rollup with incremental Apex rollup | Native full recalculation times out on non-indexed filter scans |
| Rollup filter references cross-object formula on child | Replace with Apex rollup or add a stored denormalized field for the filter | Distant record changes do not re-trigger native rollup recalculation |
| Need rollup on lookup (not master-detail) | Use Apex trigger, DLRS, or Flow-based rollup | Native rollups only exist on master-detail relationships |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory spanning relationships** — Query all formula fields, validation rules, and workflow rules on the affected object. Count unique cross-object relationship hops against the 15-reference limit.
2. **Map rollup dependencies** — Identify every trigger, flow, and process that reads a rollup summary field value. Flag any that read the value in the same transaction as child DML.
3. **Measure child volume** — Determine the maximum child record count per parent. If any parent has 300k+ children, flag the native rollup as a timeout risk.
4. **Evaluate rollup filter criteria** — Check whether rollup filters reference cross-object formula fields on the child. If so, verify that changes to the distant record actually trigger recalculation (they usually do not).
5. **Implement the fix** — Apply the appropriate pattern: consolidate spanning relationships, defer rollup reads to async, or replace native rollups with incremental Apex.
6. **Validate** — Confirm the spanning count is under limit, rollup values are correct after bulk child DML, and no REQUEST_RUNNING_TOO_LONG errors appear in the debug log.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Total unique spanning relationships on the object are at or below 12 (safe buffer below 15 hard limit)
- [ ] No trigger or synchronous flow reads a rollup summary field value in the same transaction that modifies children
- [ ] Rollup filter criteria reference only indexed fields, or the rollup has been replaced with an Apex-managed alternative
- [ ] Child record volume per parent has been measured; native rollup is only used when volume is under 200k
- [ ] Incremental Apex rollups use FOR UPDATE on the parent to prevent race conditions
- [ ] Test classes include bulk inserts (200+ children) to verify rollup accuracy and absence of limit exceptions

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Rollup values are stale inside triggers** — Rollup summary fields recalculate at step 13 of the order of execution. Any before or after trigger that queries the parent rollup field sees the old value. The only reliable way to act on the updated value is from a new transaction (Queueable, Platform Event, or Change Data Capture).
2. **Spanning limit is cumulative across metadata types** — The 15-reference cap counts formula fields, validation rules, workflow field updates, and cross-object flow references together. Adding a validation rule with a cross-object reference can break an unrelated formula field that was at the limit.
3. **Rollup filters ignore distant record changes** — If a rollup summary filters on a child formula field that spans to a grandparent, editing the grandparent does not recalculate the rollup. The rollup only fires when the direct child record is saved.
4. **Full recalculation on filter changes** — Editing rollup filter criteria in Setup triggers a full background recalculation across all parent records. On LDV orgs this can run for hours and temporarily show incorrect values.
5. **Record locking from rollup recalculation** — When child records are saved, the platform locks the parent record to update the rollup. Concurrent child inserts against the same parent cause UNABLE_TO_LOCK_ROW. This is especially acute in integrations that bulk-load children in parallel threads targeting the same parent.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Spanning relationship inventory | Table listing each cross-object reference, its source metadata type, and the relationship path it consumes |
| Rollup timing analysis | Map of which automations read rollup values and whether they risk stale reads |
| LDV rollup migration plan | Step-by-step plan to replace a native rollup with an incremental Apex alternative |

---

## Related Skills

- `apex/formula-field-performance-and-limits` — Use when the issue is formula compile size, SOQL indexing of formula fields, or formula-caused full table scans rather than spanning or rollup timing
- `admin/formula-fields` — Use for formula syntax authoring, design patterns, and readability rather than platform performance limits
- `data/roll-up-summary-alternatives` — Use when evaluating DLRS, Flow-based rollups, or other non-native rollup approaches
- `apex/order-of-execution-deep-dive` — Use when the root cause involves understanding the full 17-step save order beyond just rollup timing
- `apex/record-locking-and-contention` — Use when the primary symptom is UNABLE_TO_LOCK_ROW rather than stale rollup values
