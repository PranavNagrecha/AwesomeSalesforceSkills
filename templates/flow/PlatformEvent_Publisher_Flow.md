# Platform Event Publisher Flow — Canonical Skeleton

Use this template when a record-triggered flow (or autolaunched flow) needs to publish a Platform Event. The skeleton wires publish-after-commit semantics, idempotency, and a fault-path for publish failures.

---

## When to use

- A record save should notify one or more independent subscribers (another flow, Apex, external Pub/Sub API).
- The publisher should NOT block the save; subscribers run in their own transactions.
- You need durability: the event survives if the subscriber fails, and the publisher is not responsible for retries.

Do NOT use this template if:
- You need synchronous response from the subscriber (use invocable Apex via `skills/flow/flow-invocable-from-apex`).
- The subscriber needs the PUBLISHER's transaction limits (use inline after-save DML).
- The event must NOT fire on rollback (this template addresses that via publish-after-commit; verify on your event definition).

---

## Metadata shape

### 1. Define the event object

`Case_Status_Changed__e`:
- `caseId__c` — Text(18) — external id, indexed.
- `oldStatus__c` — Text(40).
- `newStatus__c` — Text(40).
- `changedAt__c` — DateTime.
- `eventId__c` — Text(64), external id, unique — used by subscribers for idempotency.

Check the event object's Publish Behavior:
- **Publish After Commit** (safer default for record-change events) — event delivered only if the triggering DML commits.
- **Publish Immediately** — event delivered as soon as the Create Records element runs; fires even on rollback.

### 2. Publisher flow (record-triggered, after-save)

```
Start
  Object: Case
  Trigger: A record is created or updated
  Run Flow: After the record is saved
  Entry Criteria: ISCHANGED({!$Record.Status})

├── Assignment: build eventId
│     eventId = {!$Record.Id} & '-' & TEXT({!$Record.LastModifiedDate})

├── Create Records: Case_Status_Changed__e
│     caseId__c    = {!$Record.Id}
│     oldStatus__c = {!$Record__Prior.Status}
│     newStatus__c = {!$Record.Status}
│     changedAt__c = {!$Flow.CurrentDateTime}
│     eventId__c   = {!eventId}
│   ├── Success path: End
│   └── Fault path:   Create Records → Integration_Log__c
│                       (ApplicationLogger.logError for flow)
└── End
```

### 3. Fault path detail

A publish failure is unusual (event-bus rate exceeded, validation on the event object, field-level-security violation). The fault path:

- Writes an `Integration_Log__c` record with severity=ERROR, source='CaseStatusChangePublisher', eventId, caseId.
- Does NOT retry — the admin team handles publish-failure volumes through the log.

---

## Key design decisions

### Idempotency via `eventId__c`

Subscribers check `eventId__c` against an external-id field on a processed-events object before acting. This prevents double-writes on at-least-once delivery.

Publisher responsibility: generate a deterministic eventId from the record state (Id + LastModifiedDate). Subscriber responsibility: check-then-act.

### Publish-After-Commit semantics

Default for record-change events. Prevents phantom events when the transaction rolls back.

### Why "after-save", not "before-save"

Before-save flows cannot do DML — including Create Records on an event object. Publishing must be after-save.

### When to split the publisher into a scheduled path

If the publisher needs a callout BEFORE publishing (e.g., enrich the event payload with vendor data), inline callouts from after-save are blocked. Route through a Scheduled Path with +0 minutes; the path runs in a new transaction where callouts are allowed.

---

## Subscriber template

A Platform-Event-Triggered flow subscribing to this event:

```
Start
  Platform Event: Case_Status_Changed__e

├── Get Records: Check Processed_Event__c where eventId__c = {!$Record.eventId__c}
│
├── Decision: Already processed?
│   ├── Yes → End
│   └── No →
│     ├── Get Records: Case (by {!$Record.caseId__c})
│     ├── (business logic — create Task, update related records, etc.)
│     ├── Create Records: Processed_Event__c (eventId__c = {!$Record.eventId__c})
│     └── End
```

Subscribers run as Automated Process user by default; override to a named user if record-level access matters.

---

## Testing

```apex
@IsTest
static void testPublishOnStatusChange() {
    Case c = new Case(Status='New');
    insert c;

    Test.startTest();
    c.Status = 'Working';
    update c;
    Test.stopTest();

    // Test.stopTest() flushes the event bus in tests.
    // Verify subscriber side-effects:
    List<Task> tasks = [SELECT Id FROM Task WHERE WhatId = :c.Id];
    System.assertEquals(1, tasks.size(), 'Subscriber should have created a task');
}
```

Notes:
- `Test.stopTest()` is what synchronously flushes the event bus in tests.
- If the event is defined as Publish After Commit, the event is NOT published if the test rolls back (e.g., via an exception before `stopTest`).
- For High-Volume events, `Test.getEventBus().deliver()` can be called explicitly to control delivery timing.

---

## References

- `skills/flow/flow-platform-events-integration` — the full skill backing this template.
- `skills/flow/flow-transactional-boundaries` — why after-save is mandatory for publishing.
- `skills/integration/platform-events-architecture` — cross-system pub/sub architecture.
- `standards/decision-trees/integration-pattern-selection.md` — when Platform Events are the right integration pattern.
