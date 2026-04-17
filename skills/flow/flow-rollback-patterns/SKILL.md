---
name: flow-rollback-patterns
description: "Use the Flow Rollback Records element to undo DML inside the current transaction. Covers when rollback is appropriate vs catastrophic, how to combine with fault paths, partial-commit pitfalls, and the interaction with publish-after-commit Platform Events. NOT for external-system rollback (use compensation patterns). NOT for Database.SavePoint in Apex (use apex-transaction-control)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
tags:
  - flow
  - rollback
  - transaction-control
  - fault-handling
  - dml
  - compensation
triggers:
  - "flow rollback records element"
  - "undo dml in flow fault path"
  - "flow partial commit rollback"
  - "rollback platform event publish"
  - "flow transaction safepoint"
inputs:
  - Flow scope (record-triggered, autolaunched, screen, orchestration)
  - DML sequence (create / update / delete elements in order)
  - Failure modes that should trigger rollback
outputs:
  - Rollback topology (where Rollback Records fires in the flow graph)
  - Fault-path wiring with rollback + logging
  - Interaction analysis with Platform Events and external callouts
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Flow Rollback Patterns

## When to use this skill

Activate when:

- A flow performs multiple DML operations and you need all-or-nothing semantics.
- A fault path should undo work done earlier in the same flow run.
- You're debugging a "half-completed" record state where some inserts succeeded and others failed.
- You're combining Platform Event publishing with DML and need to know how rollback affects event delivery.
- A screen flow needs to undo changes if the user clicks "Cancel" on a late screen.

Do NOT use this skill for:
- Undoing work in an external system (use compensation patterns, not rollback).
- Database.SavePoint in Apex (use `skills/apex/apex-transaction-control` if it exists).
- Rolling back approved approvals or completed orchestration stages — those live in their own transactions.

## Core concept — rollback is transaction-scoped

The Flow **Rollback Records** element undoes DML that happened in the CURRENT transaction. It does not:
- Undo DML from previous transactions (records created by a Scheduled Path yesterday are safe).
- Undo DML from a different top-level caller (if this flow was called by another flow, rollback only scopes the current flow's work in some cases; behavior varies).
- Undo external API calls already made.
- Stop Platform Events published with "Publish Immediately" semantics.

### What gets rolled back

- Create Records within this transaction.
- Update Records within this transaction.
- Delete Records within this transaction.
- Record saves propagated through triggers fired from this flow.

### What does NOT get rolled back

- Email sends (already queued at Send Email element time).
- HTTP callouts (already completed at the vendor).
- Platform Events published with Publish Immediately.
- File uploads already committed to ContentVersion.
- Sharing rule applications for those records (they're computed async).

## Recommended Workflow

1. **Map the DML sequence.** List every Create / Update / Delete in the flow, in order.
2. **Identify failure modes** that should trigger all-or-nothing rollback. Not every failure wants rollback — a logging failure shouldn't roll back the business work.
3. **Place Rollback Records in the fault path** of the element where the critical-failure could occur. Don't rollback preemptively.
4. **Combine with logging.** Rollback erases the records but not the audit trail — log to `Integration_Log__c` or similar BEFORE the rollback so you can forensically reconstruct what happened.
5. **Audit publish-after-commit events.** If the flow publishes Platform Events with Publish Immediately, rollback doesn't retract them. Switch to Publish After Commit or accept the phantom-event risk.
6. **Test the rollback path.** Force a fault in test and verify records are absent.

## Key patterns

### Pattern 1 — Create + Create + rollback-on-second-failure

```
[Get Account]
     │
     ▼
[Create Opportunity]    ────── fault path ──────►  [Rollback Records] → [End]
     │
     ▼
[Create OpportunityLineItem]  ─── fault path ────►  [Log to Integration_Log__c]
                                                          │
                                                          ▼
                                                    [Rollback Records]
                                                          │
                                                          ▼
                                                    [Send Email Alert]
                                                          │
                                                          ▼
                                                          [End]
     │
     ▼
[End] (success — both commits)
```

Design notes:
- On first-element fault: roll back and end (nothing to preserve, log not required for platform save failure).
- On second-element fault: log first (to capture the Opportunity Id that got created), THEN rollback, THEN notify.
- The admin gets an email with the log link; records never persist.

### Pattern 2 — Screen flow cancel

```
Screen 1: Gather inputs
Screen 2: [Create Records — Case]  ──►  session.caseId = {!Case.Id}
Screen 3: [Create Records — Task]   ──►  session.taskId = {!Task.Id}
Screen 4: "Confirm submit?"  ──►  [Yes] → End
                                   [No]  → [Rollback Records] → [End]
```

If the user hits "No" at the confirm step, both created records get undone. This is superior to "Delete Records" because it handles compound writes atomically — deletes would need separate DML statements with their own failure modes.

### Pattern 3 — Rollback with compensating Platform Event

When a Platform Event is published Publish Immediately and downstream subscribers have already acted, rolling back the local DML creates an inconsistency.

```
[Create Order]
     │
     ▼
[Publish Order_Created__e: Publish Immediately]  ◄── external billing system already charged
     │
     ▼
[Update Account — fault]
     │
     fault path
     ▼
[Rollback Records]      ◄── undoes Order + Account
[Publish Order_Cancelled__e] ◄── tell subscribers to undo their side
```

Publish-After-Commit would be better, but sometimes business constraints prevent the change. A compensating event is the recovery pattern.

### Pattern 4 — Don't rollback on logging failure

```
[Business DML: Create + Update] ─── success ─►
     │
     ▼
[Log success to Integration_Log__c]  ─── fault path ─►  [Silent End]
```

A logging failure should NOT trigger rollback of the business work. The Silent End on the fault path is deliberate — the business work committed, the log failed, an admin can reconstruct from system logs later.

## Bulk safety

- Rollback Records undoes all DML in the transaction, not just one record. Bulk is handled automatically.
- In a record-triggered flow processing 200 records, a fault in record #150 rolls back ALL 200 by default. If you need per-record rollback, use Apex (SavePoint) — Flow can't do per-record scope within a batch.
- Rollback counts against the transaction limits (the undo operations still use DML slots).

## Error handling

- **Rollback itself succeeds almost always.** It's a platform primitive with minimal failure modes.
- **Log BEFORE rolling back,** not after — the log record would itself be rolled back.
- **Fault path on the element AFTER rollback** should capture rollback failures (rare, but possible if the session is corrupt).

## Well-Architected mapping

- **Reliability** — rollback is the only way to get all-or-nothing semantics in Flow. Without it, partial commits accumulate garbage data that requires manual cleanup.
- **Security** — incomplete records may violate business rules (a Case without Account) that bypass validation. Rollback restores the invariant.

## Gotchas

See `references/gotchas.md`.

## Testing

In Apex test classes that invoke the flow:

```apex
@IsTest
static void testRollbackOnSecondDMLFailure() {
    // Setup: trigger a condition that makes the 2nd DML fail.
    Account a = new Account(Name='Test');
    insert a;
    // Pre-create a record that will collide with the flow's 2nd DML.
    ...

    Test.startTest();
    // Invoke flow; expect the whole transaction to rollback.
    try {
        Flow.Interview.MyFlow flow =
            new Flow.Interview.MyFlow(new Map<String, Object>{'accountId' => a.Id});
        flow.start();
    } catch (Exception e) {
        // Expected.
    }
    Test.stopTest();

    // Assert no Opportunity was created.
    System.assertEquals(0, [SELECT COUNT() FROM Opportunity WHERE AccountId = :a.Id]);
}
```

## Official Sources Used

- Salesforce Help — Flow Rollback Records Element: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_rollback.htm
- Salesforce Help — Flow Fault Connector Paths: https://help.salesforce.com/s/articleView?id=sf.flow_ref_faults.htm
- Salesforce Developer — Transaction Control in Flow and Apex: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_control.htm
- Salesforce Developer — Platform Events Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/
