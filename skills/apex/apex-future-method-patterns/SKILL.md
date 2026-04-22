---
name: apex-future-method-patterns
description: "@future methods: primitive-only parameters, callout=true, no chaining, 50 per transaction, error handling. When to prefer Queueable/Batch instead per async-selection decision tree. NOT for Queueable patterns (use apex-queueable-patterns). NOT for Batch Apex (use apex-batch-patterns)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
tags:
  - apex
  - future-method
  - async
  - callouts
  - governor-limits
triggers:
  - "@future method primitive parameter restriction workaround"
  - "future method callout=true http from trigger"
  - "can a future method call another future method chaining"
  - "future method monitoring and error handling"
  - "50 future method limit per transaction hit"
  - "when to use future vs queueable apex"
inputs:
  - Current sync code needing async offload
  - Operation type (callout, DML, computation)
  - Parameter shape (primitives vs SObjects)
  - Retry requirements
outputs:
  - "@future vs Queueable decision"
  - Parameter-shape transformation (ids/json strings)
  - Callout configuration
  - Monitoring plan
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Apex Future Method Patterns

Activate when `@future` is the proposed async mechanism — or when reviewing existing `@future` methods for modernization. `@future` is the oldest async tool on the platform and has hard restrictions (primitive parameters only, no chaining, limited visibility) that make Queueable the better choice for most new work. Consult `standards/decision-trees/async-selection.md` before committing.

## Before Starting

- **Check the async decision tree.** For new work, Queueable is usually better.
- **Collect the primitive parameter shape.** `@future` accepts only primitive types, lists/sets/maps of primitives. Pass `Set<Id>` or JSON-serialized SObject blobs.
- **Mark `callout=true` if making HTTP callouts.** Without it, callouts throw `CalloutException: Callout from scheduled Apex or trigger cannot be performed`.

## Core Concepts

### Parameter restrictions

Only primitives (Id, String, Integer, etc.) and collections of primitives. No SObjects, no Apex objects. Workaround: pass `Set<Id>` and re-query; or `JSON.serialize(records)` + `JSON.deserialize` inside.

### `callout=true`

Annotation: `@future(callout=true)`. Required for any HTTP callout. The method becomes a "future callout" and is counted separately in limits.

### No chaining

A `@future` cannot call another `@future` or a Queueable. Queueable can chain Queueable (up to 5 depth); `@future` cannot. This is the main modernization driver.

### Governor limits

Max 50 `@future` calls per transaction. Max 250k methods per 24h per license. Failures retry up to 5 times with exponential backoff (platform-managed).

### Static method only

`@future` must be on a `public static void` method. Cannot be on instance methods.

## Common Patterns

### Pattern: Future from trigger for callout

```
public class CalloutService {
    @future(callout=true)
    public static void pushChanges(Set<Id> accountIds) {
        for (Account a : [SELECT Id, Name FROM Account WHERE Id IN :accountIds]) {
            // HTTP callout
        }
    }
}
```

### Pattern: Avoid future — use Queueable instead

When new code needs async DML without callouts, prefer Queueable: supports chaining, richer parameters, better monitoring.

### Pattern: Future → Queueable conversion during refactor

When modernizing, wrap the old `@future` body inside a Queueable `execute(...)` method; change callers to `System.enqueueJob(new X(...))`.

## Decision Guidance

| Situation | Mechanism |
|---|---|
| Callout from trigger (quick win) | @future(callout=true) |
| Async DML, might chain | Queueable |
| >50 async starts per transaction | Batch Apex |
| Need to pass SObjects as-is | Queueable (SObjects allowed) |
| Existing @future working fine | Keep (don't modernize for modernization's sake) |

## Recommended Workflow

1. Consult `standards/decision-trees/async-selection.md` to confirm `@future` is right.
2. Shape parameters as primitives or collections of primitives (Set<Id> preferred).
3. Add `callout=true` if making HTTP calls.
4. Handle exceptions inside the future — uncaught throws still count against retries.
5. Monitor via Apex Jobs (Setup → Apex Jobs); failures surface with "Future" type.
6. Bulk-safe: if caller might issue >50 futures, batch Ids into chunks or switch to Batch Apex.
7. Document why `@future` was chosen over Queueable.

## Review Checklist

- [ ] Parameters are primitives only
- [ ] `callout=true` present if HTTP callouts made
- [ ] Method is `public static void`
- [ ] Caller respects 50-future-per-transaction limit
- [ ] No chained `@future` calls (not possible)
- [ ] Exception handling inside future method
- [ ] Apex Jobs monitoring covered in runbook
- [ ] Decision to use `@future` documented per async decision tree

## Salesforce-Specific Gotchas

1. **Cannot call `@future` from another `@future` or batch/scheduled Apex.** Throws `AsyncException`.
2. **Calls from test methods don't execute unless wrapped in `Test.startTest()` / `Test.stopTest()`.**
3. **Test.isRunningTest() inside future returns true but the database state is test-isolated.** Real callouts still need mocking.

## Output Artifacts

| Artifact | Description |
|---|---|
| Decision record | @future vs Queueable, rationale |
| Future method template | Primitive-param + re-query pattern |
| Monitoring runbook | Apex Jobs + error-log flow |

## Related Skills

- `apex/apex-queueable-patterns` — modern async
- `apex/apex-batch-patterns` — high-volume async
- `standards/decision-trees/async-selection` — choosing async mechanism
