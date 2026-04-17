---
name: flow-migration-from-trigger
description: "Decide whether an existing Apex trigger should be rewritten as a Flow, and execute the migration safely. Covers the decision criteria (complexity, ownership, performance), side-by-side rollout, test-coverage parity, and the inverse case (recognize when Flow should stay Apex). NOT for migrating Process Builder / Workflow Rule to Flow (use those migration skills). NOT for brand-new automation decisions (use automation-selection.md)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Performance
tags:
  - flow
  - apex
  - migration
  - trigger
  - modernization
  - admin-maintainability
triggers:
  - "migrate apex trigger to flow"
  - "replace trigger with flow"
  - "admin-owned automation from apex"
  - "apex to flow migration decision"
  - "simplify trigger handler with flow"
inputs:
  - Target Apex trigger + handler files
  - Current test coverage + test classes
  - Admin vs developer ownership post-migration
  - Performance SLA if any
outputs:
  - Decision recommendation (migrate / keep / partial)
  - Migration plan with side-by-side rollout
  - Flow design that preserves trigger semantics
  - Test-coverage parity assertions
  - Rollback plan if migration fails
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Flow Migration from Trigger

## When to use this skill

Activate when:

- An existing Apex trigger could plausibly be expressed as a Flow — typically a simple "when X changes, update Y" pattern.
- Admin team wants to own the automation going forward; Apex ownership is friction.
- A trigger handler has grown unwieldy and specific pieces of it would benefit from declarative maintenance.
- You're evaluating a legacy org where triggers predate Flow-recommended patterns.

Do NOT use this skill for:
- Migrating Process Builder or Workflow Rules to Flow (use `skills/flow/process-builder-to-flow-migration` / `workflow-rule-to-flow-migration`).
- Deciding automation tech for a brand-new requirement (use `standards/decision-trees/automation-selection.md`).
- Full-blown replatforming where everything moves to Agentforce or external middleware (out of scope).

## Core concept — not every trigger should migrate

Apex triggers earn their complexity. Migration is justified when Flow can credibly carry the load AND admin ownership is desirable. Migration is harmful when:

- The trigger orchestrates complex transaction control (SavePoints, multi-SOQL joins, recursion control) that Flow doesn't express cleanly.
- The trigger issues callouts, which are constrained in Flow's After-Save context.
- The trigger runs in high-volume contexts where the per-element overhead of Flow (vs tight Apex) matters.

## Migration decision matrix

| Trigger characteristic | Migrate to Flow? |
|---|---|
| Single-object field derivation | ✅ Yes — use Before-Save record-triggered flow |
| Create related records on save | ✅ Yes — After-Save record-triggered flow |
| Cross-object updates with moderate logic | ✅ Yes — After-Save record-triggered flow |
| Bulk processing (1000+ records per transaction) | ⚠️ Maybe — benchmark before migrating |
| Callouts or async work | ⚠️ Route via Scheduled Path or Platform Event |
| SavePoint / complex transaction control | ❌ No — keep Apex |
| Recursion control via static context | ❌ No — keep Apex |
| Integration with @future / Queueable | ❌ No — keep Apex |
| Custom exception wrapping / logging frameworks | ❌ No — keep Apex |
| SOQL-heavy joins and aggregations | ❌ No — keep Apex |

## Recommended Workflow

1. **Read the trigger + handler** end-to-end. Note all DML, SOQL, and decision branches.
2. **Classify each branch** against the decision matrix. If any branch is "No", consider keeping Apex OR splitting the trigger (keep complex branches in Apex, migrate simple branches to Flow).
3. **Inventory tests.** Every test case that exercises the trigger must still pass after migration. If coverage is weak, shore it up BEFORE migration, not after.
4. **Design the Flow.** Match the trigger's timing (Before-Save vs After-Save), bulk context, and field updates.
5. **Plan side-by-side rollout.** Deploy the Flow inactive; activate in sandbox; run existing tests; smoke-test against a business-representative data set; activate in prod behind a Custom Permission for a subset of users.
6. **Deactivate the trigger.** Don't delete until 2+ release cycles confirm the Flow is stable. Keep the trigger source code for rollback.
7. **Declare migration complete** only when: tests green, zero runtime errors for 30 days, admin team confirms ownership.

## Key patterns

### Pattern 1 — Simple field-derivation migration

Original trigger handler:

```apex
for (Account acc : Trigger.new) {
    if (acc.Billing_Country__c == 'United States') {
        acc.Region__c = 'NA';
    } else if (acc.Billing_Country__c == 'Germany') {
        acc.Region__c = 'EMEA';
    }
}
```

Flow equivalent (Before-Save record-triggered):

```
[Decision: Billing_Country__c]
  ├── "United States" → [Assignment: $Record.Region__c = 'NA']
  ├── "Germany"       → [Assignment: $Record.Region__c = 'EMEA']
  └── default         → [Assignment: $Record.Region__c = 'ROW']
```

Benefits post-migration:
- Admin can add new country → region mappings without code.
- Before-Save avoids DML cost (free field update).
- Same transaction semantics as the original trigger.

### Pattern 2 — Partial migration

Handler with two responsibilities:
- Simple branch: set `Region__c` from country (migrate).
- Complex branch: SOQL-join parent account's preferences + SavePoint + external callout (keep in Apex).

Split:
- Flow handles region.
- Trigger now only runs the complex branch.
- Both coexist; each fires on the same save.

The test suite must verify both fire in the correct order (Before-Save Flow fires first, then Apex After-Insert/Update trigger).

### Pattern 3 — Side-by-side rollout with Custom Permission

```
Trigger handler:
  if (!FeatureManagement.checkPermission('New_Flow_Active')) {
      // run the old logic
  } else {
      // skip; flow will handle
  }
```

Admins grant `New_Flow_Active` Custom Permission to a PSG; ramps from 1 user → 10% → 100%. If regression, revoke PSG; old logic resumes.

### Pattern 4 — Bulk benchmark before migration

Bulk-heavy trigger (1000+ records per batch): before migrating, measure per-record time in Apex vs expected Flow runtime. Flows process per record with element overhead; complex Flow logic at scale can exceed Apex by 2-5× in CPU time.

Measurement:
- Log Apex handler CPU time on a 200-record batch.
- In sandbox, run the equivalent Flow on the same 200-record fixture.
- If Flow is > 30% slower and the savings from Apex are material to user experience, KEEP Apex.

## Bulk safety

- Flow migration must preserve bulk semantics. A trigger handler that queries once and caches results must be replicated as Flow with Get Records outside loops.
- Order-of-execution changes: Before-Save Flow fires before Before-triggers in Apex. Verify no dependency inversion (e.g., Apex Before-trigger sets a value the Flow then reads).

## Error handling

- Every Flow branch needs a fault connector; triggers bubble Apex exceptions by default. Migration must preserve the error-surfacing behavior.
- Log to Integration_Log__c (see `skills/flow/flow-error-monitoring`) instead of relying on fault emails.

## Well-Architected mapping

- **Reliability** — a successful migration preserves behavior. A rushed migration introduces silent regressions. Side-by-side rollout + test parity is the safeguard.
- **Operational Excellence** — admin-maintainable automation is a real productivity gain at portfolio scale, but only if the migration doesn't cost more in fragile transitions than it saves in ongoing maintenance.
- **Performance** — Flow has per-element overhead; don't migrate hot-path triggers without benchmarking.

## Gotchas

See `references/gotchas.md`.

## Testing

The migration test strategy is **parity testing**:

1. Run the existing trigger test suite against the pre-migration org state; record outcomes.
2. Deactivate trigger, activate Flow.
3. Re-run the same test suite; every test must produce identical outcomes.
4. If any test fails, the migration introduced a regression — don't proceed.

Add NEW test cases that specifically exercise Flow-only concerns (fault paths, Before-Save semantics).

## Official Sources Used

- Salesforce Help — Decide Between Flow and Apex: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger.htm
- Salesforce Developer — Trigger Order of Execution: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Salesforce Architects — Automation Modernization Patterns: https://architect.salesforce.com/
- Salesforce Help — Flow Trigger Types: https://help.salesforce.com/s/articleView?id=sf.flow_ref_triggers.htm
