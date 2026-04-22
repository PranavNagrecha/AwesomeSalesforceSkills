---
name: apex-savepoint-and-rollback
description: "Database.Savepoint / Database.rollback for partial-transaction undo: placement rules, ID reset, limit counters, nested savepoints, rollback after callout. NOT for Database.allOrNone=false partial success semantics (use apex-partial-dml). NOT for Queueable chained rollback (use apex-queueable-patterns)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
tags:
  - apex
  - savepoint
  - rollback
  - transaction
  - dml
triggers:
  - "database.savepoint rollback apex transaction undo"
  - "how to roll back only some dml operations in apex"
  - "apex ids stay populated after rollback"
  - "savepoint limit counter reset behavior"
  - "rollback after http callout restriction"
  - "nested savepoint apex dml semantics"
inputs:
  - Transaction boundary where partial rollback needed
  - DML operations to potentially undo
  - Presence of callouts in the transaction
  - Error-handling strategy
outputs:
  - Savepoint/rollback placement pattern
  - Error-handling block with deterministic cleanup
  - Governor-limit impact analysis
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Apex Savepoint and Rollback

Activate when multi-step DML needs a safety net: if a later step fails, earlier steps should be undone. `Database.Savepoint` + `Database.rollback(sp)` is Salesforce's mechanism. The semantics are subtle: IDs on in-memory records are NOT reset, governor limits are not fully reset, and rollback after a callout is forbidden.

## Before Starting

- **Place the savepoint BEFORE the first DML** you might want to undo.
- **Never call `Database.rollback` after an HTTP callout in the same transaction.** Platform prevents it.
- **Clear Id fields manually after rollback** on in-memory records you intend to re-insert.

## Core Concepts

### The savepoint lifecycle

```
Savepoint sp = Database.setSavepoint();
try {
    insert accounts;
    insert contacts;
    insert opportunities;
} catch (Exception e) {
    Database.rollback(sp);
    // handle
}
```

`setSavepoint()` snapshots the transaction; `rollback(sp)` undoes DML after the savepoint.

### What rollback undoes

- DML (insert/update/delete/upsert) after the savepoint
- Change to records' database state

### What rollback does NOT undo

- IDs populated on in-memory `SObject` instances (you must null them if re-inserting)
- Emails sent via `Messaging.sendEmail`
- HTTP callouts (and you can't even call rollback post-callout)
- Static variable state
- Governor limit counters are partially reset (DML rows yes; SOQL queries no)

### Nested savepoints

Valid; each call to `setSavepoint()` creates a new savepoint. Rolling back an outer savepoint invalidates inner ones.

### Limits

`Database.setSavepoint` counts against the 150 DML-statement limit. `Database.rollback` also counts. Avoid savepoint-per-record loops.

## Common Patterns

### Pattern: All-or-nothing multi-DML

```
Savepoint sp = Database.setSavepoint();
try {
    insert parents;
    insert children;  // if this fails, parents rolled back too
} catch (DmlException e) {
    Database.rollback(sp);
    throw new MyException('Operation aborted', e);
}
```

### Pattern: Rollback-then-rethrow with clean IDs

```
Savepoint sp = Database.setSavepoint();
try {
    insert accs;
    insert opps;
} catch (Exception e) {
    Database.rollback(sp);
    for (Account a : accs) a.Id = null;  // so retries can re-insert
    throw e;
}
```

### Pattern: Pre-callout DML with deferred rollback decision

Rollback must happen before any callout. If you need conditional rollback based on callout response, do DML AFTER the callout, or don't use savepoints at all — use a compensating action.

## Decision Guidance

| Situation | Approach |
|---|---|
| Multi-step DML, all or nothing | Savepoint + try/catch + rollback |
| Partial success acceptable | Database.insert(records, false) |
| DML + callout + conditional rollback | Callout first, then DML (no savepoint needed) |
| Nested service-layer rollback | Caller sets savepoint; callees rely on it |

## Recommended Workflow

1. Identify the transaction boundary — where savepoint belongs.
2. Place `Database.setSavepoint()` before the first reversible DML.
3. Wrap remaining DML in try/catch; rollback in catch.
4. Null out IDs on in-memory records if retry is planned.
5. Verify NO callouts occur between savepoint and rollback.
6. Count savepoint + rollback against DML limit (each costs 1).
7. Test failure paths with forced exceptions to confirm rollback works.

## Review Checklist

- [ ] Savepoint placed before reversible DML
- [ ] No HTTP callouts between savepoint and rollback
- [ ] Rollback inside catch block, not in fall-through
- [ ] IDs nulled on in-memory records when retry expected
- [ ] No savepoint inside a loop
- [ ] Nested savepoints used sparingly and understood
- [ ] Test class with forced exception proves rollback
- [ ] Limits considered (savepoint + rollback = 2 DML statements)

## Salesforce-Specific Gotchas

1. **Rollback after callout throws `CalloutException`.** Order matters: DML-savepoint-DML-rollback OR callout-then-DML, never mix.
2. **IDs persist on in-memory records after rollback.** Database state is undone; Apex objects still carry IDs — re-inserting throws "Id already exists" if you don't null them.
3. **SOQL query count is NOT reset by rollback.** Only DML row counts partially reset. A rollback loop can still blow the SOQL-101 limit.

## Output Artifacts

| Artifact | Description |
|---|---|
| Transaction-boundary design | Where savepoints live in the service layer |
| Rollback helper | Utility that rolls back + nulls IDs |
| Test coverage | Force-fail case proving rollback |

## Related Skills

- `apex/apex-partial-dml` — all-or-none and partial DML options
- `apex/apex-exception-handling` — structured error handling
- `apex/apex-transaction-boundaries` — service-layer transaction design
