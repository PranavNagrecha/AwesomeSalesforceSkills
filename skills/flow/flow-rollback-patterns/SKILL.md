---
name: flow-rollback-patterns
description: "Use the Flow Rollback Records element to undo DML inside the current transaction. Covers when rollback is appropriate vs catastrophic, how to combine with fault paths, partial-commit pitfalls, and the interaction with publish-after-commit. NOT for external-system rollback (use compensation patterns) — use apex/apex-savepoint-and-rollback."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Flow Rollback Patterns

## Core concept — rollback is transaction-scoped

The Flow **Rollback Records** element (`FlowRecordRollback`) "Rolls back the current transaction and cancels its pending record changes" and is "Available only in screen flows" (api_meta 264 L73986-73987; API 52.0 and later, L73988). In a record-triggered flow the declarative rollback is the Custom Error element, which "roll[s] back a change that triggered a flow" (`FlowCustomError`, api_meta 264 L72593); see `flow/fault-handling`. The element has a single `connector` field and no fault connector (api_meta 264 L73990-73992). It undoes DML that happened in the CURRENT transaction. It does not:
- Undo DML from previous transactions (records created by a Scheduled Path yesterday are safe).
- Undo DML from a different top-level caller (if this flow was called by another flow, rollback only scopes the current flow's work in some cases; behavior varies). UNVERIFIED (2026-10-20): the subflow and caller scope is not in the corpus.
- Undo DML that a prior transaction committed: an invocable action with `flowTransactionModel` `NewTransaction` "Creates a transaction before the invocable action is executed", and `Automatic` creates one "if the invocable action supports it and there's pending DML" (api_meta 264 L71022-71029), so DML before that action sits outside a later rollback.
- Undo external API calls already made.
- Stop Platform Events published with "Publish Immediately" semantics: "You can't roll back published event messages" (platform_events 264 L276-277), and an event configured to publish immediately is published "regardless of whether the transaction succeeds" (api_meta 264 L44519-44520); the default is `PublishImmediately` (L44513).

### What gets rolled back

- Create Records within this transaction.
- Update Records within this transaction.
- Delete Records within this transaction.
- Record saves propagated through triggers fired from this flow. UNVERIFIED (2026-10-20): trigger propagation is not described for the rollback element.

### What does NOT get rolled back

- HTTP callouts (already completed at the vendor). Apex forbids a callout "when there are pending operations in the same transaction", and allows one before DML (apexdev 264 L36340-36342).
- Platform Events published with Publish Immediately.
- File uploads already committed to ContentVersion. UNVERIFIED (2026-10-20): not in the corpus.
- Sharing rule applications for those records (they're computed async). UNVERIFIED (2026-10-20): not in the corpus.

### Email is the opposite case

The earlier text listed email under "does NOT get rolled back". The order of execution lists "Sending email" among post-commit logic that runs "After the changes are committed to the database" (apexdev 264 L15682, L15690), and Apex `Database.rollback` states that "Any emails submitted since the last savepoint are also rolled back and not sent" (apexref 262 L209230). UNVERIFIED (2026-10-20): that a flow's Send Email action follows the same rule is not stated for the Flow element. Treat email as a notification that a rollback can suppress, not one it cannot recall.

## Recommended Workflow

1. **Map the DML sequence.** List every Create / Update / Delete in the flow, in order.
2. **Identify failure modes** that should trigger all-or-nothing rollback. Not every failure wants rollback — a logging failure shouldn't roll back the business work.
3. **Place Rollback Records in the fault path** of the element where the critical-failure could occur. Don't rollback preemptively.
4. **Combine with logging that survives.** Rollback Records "cancels its pending record changes" (api_meta 264 L73986), and a log record created before the rollback is one of them. Write the evidence to a Publish Immediately platform event, which "can't be rolled back" (platform_events 264 L276-277, L660-661), or accept that a Create Records log before the rollback is erased. UNVERIFIED (2026-10-20): whether a Create Records log placed after the rollback persists is not in the corpus. The earlier text said to log to `Integration_Log__c` before the rollback.
5. **Audit publish behavior.** If the flow publishes Platform Events with Publish Immediately, rollback doesn't retract them. Switch to Publish After Commit (published "only after a transaction commits successfully", api_meta 264 L44517-44518) or accept the phantom-event risk.
6. **Test the rollback path.** Force a fault in test and verify records are absent.

## Questions to Ask Before Configuring

Ask these before placing a rollback. Each one maps to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which flow type is this?" | Rollback Records is screen-flow only (api_meta 264 L73987); record-triggered flows use Custom Error (L72593) | The element the flow type allows |
| "Does the flow publish a platform event, and with which publish behavior?" | Publish Immediately cannot be rolled back (platform_events 264 L276-277) (gotcha 1) | The behavior on the event definition, and a compensating event if it is immediate |
| "Where does the failure evidence go?" | A Create Records log before the rollback is cancelled with it (api_meta 264 L73986) (gotcha 3) | A Publish Immediately event, or an accepted loss |
| "Does anything call out or send email before the rollback?" | Callouts are not undone; email is post-commit (apexdev 264 L15690) (gotchas 2, 5) | The order of callout, DML and email, written down |
| "Is there a subflow or an invocable action in the DML path?" | An action with `NewTransaction` starts its own transaction (api_meta 264 L71022-71029) (gotcha 4) | The `flowTransactionModel` value per action |
| "Which failures should NOT roll back?" | A logging or notification failure should not erase business work (Pattern 4) | A list of non-critical elements that end silently |
| "Are files, approvals or sharing involved?" | Their rollback behavior is UNVERIFIED in the corpus (gotchas 6, 7) | A manual cleanup step or a documented residual risk |

A proper configuration adds a flow-type-correct rollback element, evidence that outlives it and a stated scope per transaction, none of which "just adding Rollback Records" provides.

## Key patterns

### Pattern 1 — Create + Create + rollback-on-second-failure

```
[Get Account]
     │
     ▼
[Create Opportunity]    ────── fault path ──────►  [Rollback Records] → [End]
     │
     ▼
[Create OpportunityLineItem]  ─── fault path ────►  [Log: Publish Immediately event]
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
- On second-element fault: publish the evidence first as a Publish Immediately platform event (it survives the rollback, platform_events 264 L276-277), THEN rollback, THEN notify. A Create Records log written here would be cancelled by the rollback (api_meta 264 L73986).
- This diagram is a screen flow: Rollback Records is screen-flow only (api_meta 264 L73987). UNVERIFIED (2026-10-20): that the admin email still arrives; email is post-commit logic (apexdev 264 L15690).

### Pattern 2 — Screen flow cancel

```
Screen 1: Gather inputs
Screen 2: [Create Records — Case]  ──►  session.caseId = {!Case.Id}
Screen 3: [Create Records — Task]   ──►  session.taskId = {!Task.Id}
Screen 4: "Confirm submit?"  ──►  [Yes] → End
                                   [No]  → [Rollback Records] → [End]
```

If the user hits "No" at the confirm step, both created records get undone. UNVERIFIED (2026-10-20): whether DML before a screen is still pending at a later screen is not in the corpus; the guide says only that the element rolls back "the current transaction" (api_meta 264 L73986). This is superior to "Delete Records" because it handles compound writes atomically — deletes would need separate DML statements with their own failure modes.

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

- Rollback Records cancels the pending record changes of the current transaction, not just one record (api_meta 264 L73986). It exists only in screen flows (L73987).
- In a record-triggered flow processing 200 records, a fault in record #150 rolls back ALL 200 by default. UNVERIFIED (2026-10-20): the batch rollback behavior is not described in the corpus (Apex code may be invoked for 1 to 200 records, apexdev 264 L40790). If you need per-record rollback, use Apex (SavePoint) — Flow can't do per-record scope within a batch.
- Rollback counts against the transaction limits (the undo operations still use DML slots). UNVERIFIED (2026-10-20): not in the corpus.

## Error handling

- **Rollback itself succeeds almost always.** It's a platform primitive with minimal failure modes. UNVERIFIED (2026-10-20): not in the corpus.
- **A Create Records log before the rollback is cancelled with it** (api_meta 264 L73986); use a Publish Immediately platform event for evidence that must survive (platform_events 264 L276-277). The earlier text said to log BEFORE rolling back, which contradicted the cancelled-changes behavior.
- **The Rollback Records element has no fault connector** (only `connector`, api_meta 264 L73990-73992), so there is no fault path to wire on it. The earlier text said to put a fault path on the element after the rollback to catch rollback failures; the next element's own fault connector covers that element only.

## Well-Architected mapping

- **Reliability** — rollback is the only way to get all-or-nothing semantics in Flow (UNVERIFIED (2026-10-20): "the only way" is not a corpus claim). Without it, partial commits accumulate garbage data that requires manual cleanup.
- **Security** — incomplete records may violate business rules (a Case without Account) that bypass validation. Rollback restores the invariant. UNVERIFIED (2026-10-20): advice, not a corpus claim.

## Gotchas

See `references/gotchas.md`.

## Testing

`Flow.Interview.start()` works only for autolaunched and user provisioning flows (apexref 262 L158169-158177), so Apex cannot start a screen flow, the only type with a Rollback Records element; test a screen flow in Flow Builder debug. For a record-triggered flow that rolls back with Custom Error (api_meta 264 L72593), perform the DML that triggers it:

```apex
@IsTest
static void testRollbackOnSecondDMLFailure() {
    // Setup: trigger a condition that makes the 2nd DML fail.
    Account a = new Account(Name='Test');
    insert a;
    // Pre-create a record that will collide with the flow's 2nd DML.
    ...

    Test.startTest();
    // Perform the DML that triggers the record-triggered flow; its Custom Error
    // element (or an unhandled fault) fails the save. Flow.Interview.start() cannot
    // run a screen flow (apexref 262 L158169-158177), so no Rollback Records here.
    Boolean failed = false;
    try {
        insert new Opportunity(Name = 'T', AccountId = a.Id,
            StageName = 'Prospecting', CloseDate = Date.today());
    } catch (DmlException e) {
        failed = true;
    }
    Test.stopTest();
    System.assert(failed, 'Expected the flow to fail the save.');

    // Assert no Opportunity was created.
    System.assertEquals(0, [SELECT COUNT() FROM Opportunity WHERE AccountId = :a.Id]);
}
```

## Official Sources Used

- Salesforce Help — Flow Rollback Records Element: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_rollback.htm
- Salesforce Help — Flow Fault Connector Paths: https://help.salesforce.com/s/articleView?id=sf.flow_ref_faults.htm
- Salesforce Developer — Transaction Control in Flow and Apex: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_control.htm
- Salesforce Developer — Platform Events Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/
