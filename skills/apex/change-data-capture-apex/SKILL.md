---
name: change-data-capture-apex
description: "Use this skill when writing or reviewing Apex change event triggers: trigger syntax on ChangeEvent objects, reading ChangeEventHeader fields (changeType, changedFields, recordIds, commitUser), handling CREATE/UPDATE/DELETE/UNDELETE and GAP events in Apex, and configuring entity tracking. NOT for platform events published by application code (use apex/platform-events-apex). NOT for external CDC subscribers via CometD or Pub/Sub API (use integration/change-data-capture-integration)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - how do I write a CDC trigger in Apex
  - handle change data capture events in Apex trigger
  - read ChangeEventHeader changedFields in Apex
  - detect which fields changed in CDC trigger
  - configure entity tracking for change data capture
  - handle GAP events in Apex CDC trigger
tags:
  - change-data-capture
  - CDC
  - apex-trigger
  - ChangeEventHeader
  - change-event
  - async-apex
inputs:
  - Object(s) to track via CDC (standard or custom)
  - Business logic that must react to CREATE, UPDATE, DELETE, or UNDELETE
  - Whether only specific field changes should trigger action (field-level filtering)
  - Whether downstream logic can tolerate async execution (it must — CDC triggers always run async)
outputs:
  - Apex CDC trigger with correct syntax and header field access
  - changedFields-based field filtering pattern
  - GAP event detection and recovery logic
  - Entity tracking configuration guidance
  - PlatformEventSubscriberConfig guidance when running user or batch size override is needed
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Change Data Capture Apex

Use this skill when implementing or reviewing Apex logic that subscribes to Salesforce record change events via CDC triggers. CDC triggers fire asynchronously after DML commits and provide rich header metadata (changeType, changedFields, recordIds, commitUser) for precise, efficient processing. This skill covers the complete Apex-side CDC pattern: trigger declaration, header field access, change-type routing, gap event handling, field-level filtering, and entity configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Is the object enabled for CDC?** Go to Setup > Integrations > Change Data Capture. The object must be selected there — the trigger compiles but fires no events if the object is not tracked.
- **Is this a platform event?** If the event is manually published by application code (e.g., `EventBus.publish()`), use `apex/platform-events-apex` instead. CDC events are system-generated; they cannot be manually published.
- **What operations need handling?** CDC triggers fire for CREATE, UPDATE, DELETE, and UNDELETE. Confirm which change types the business logic must react to — GAP events also require handling in production.
- **Is synchronous callout needed?** CDC triggers run asynchronously under the Automated Process entity. Synchronous callouts from a CDC trigger are not supported. Use a queueable or @future(callout=true) dispatched from the trigger if callouts are required.
- **Batch size:** Default maximum is 2,000 event messages per trigger invocation. Override with `PlatformEventSubscriberConfig` if needed.

---

## Core Concepts

### CDC Trigger Syntax and Execution Model

A CDC trigger is always an `after insert` trigger on the change event object — not on the base sObject. The change event type name follows the pattern `<ObjectApiName>ChangeEvent` for standard objects and `<ObjectApiName>__ChangeEvent` for custom objects.

```apex
trigger AccountChangeEventTrigger on AccountChangeEvent (after insert) {
    // Trigger.new contains up to 2,000 AccountChangeEvent records per batch
}
```

CDC triggers:
- Execute **asynchronously** after the originating database transaction commits. They run outside the originating Apex transaction.
- Run under the **Automated Process** entity, not the user who performed the DML. Debug logs must be configured for the Automated Process entity — they do not appear in the Developer Console log tab by default.
- Are subject to **synchronous Apex governor limits** despite running asynchronously. SOQL, DML, CPU, and heap limits apply per invocation just as in synchronous Apex.
- Have a maximum batch size of **2,000 event messages** per execution. Multiple batches fire if more events are queued.
- Can be configured with `PlatformEventSubscriberConfig` (Tooling API or Metadata API) to override the running user identity and default batch size.

### ChangeEventHeader and Header Fields

Every event in `Trigger.new` exposes a `ChangeEventHeader` field (type `EventBus.ChangeEventHeader`) that carries all change metadata. Access it via the event's `.ChangeEventHeader` property.

Key header fields for Apex:

| Field | Type | Description |
|---|---|---|
| `changeType` | String | `CREATE`, `UPDATE`, `DELETE`, `UNDELETE`, or `GAP_*` prefixed variants |
| `changedFields` | List\<String\> | Field API names changed in an UPDATE; empty for CREATE/DELETE/UNDELETE |
| `nulledFields` | List\<String\> | Fields explicitly set to null in an UPDATE |
| `recordIds` | List\<String\> | All record IDs covered by this event (may be multiple when events are merged) |
| `entityName` | String | API name of the changed object (e.g., `Account`) |
| `commitUser` | String | ID of the user who performed the change |
| `transactionKey` | String | Unique transaction identifier; use to correlate or deduplicate |
| `commitTimestamp` | Long | Epoch milliseconds of the commit |

`changedFields` and `nulledFields` are available in **Apex triggers and Pub/Sub API only** — they are absent in CometD subscribers. This is the primary reason to prefer Apex triggers when the subscriber must perform field-level filtering.

Access record IDs via the method `header.getRecordIds()` which returns a `List<String>`.

### Change Event Body Fields in Apex

In an Apex CDC trigger, all record fields are present on the event object whether or not they changed. **Unchanged fields are null in the event message.** This is different from external CDC consumers where the full record is returned for a CREATE but only changed fields are populated for UPDATE. Do not read an unchanged field and assume its value is current — use `changedFields` to determine which fields actually changed, then query the record for full state if needed.

### Entity Tracking and GAP Events

CDC must be explicitly enabled per object. For standard channels, enable in **Setup > Integrations > Change Data Capture**. The default limit is **5 entities** across all channels and editions without the CDC add-on. Custom objects count toward this limit.

When Salesforce cannot generate a full change event (event exceeds 1 MB, large bulk operation bypasses the application server, internal error), it generates a **gap event** with a `changeType` prefixed by `GAP_`: `GAP_CREATE`, `GAP_UPDATE`, `GAP_DELETE`, `GAP_UNDELETE`, or `GAP_OVERFLOW`. Gap events carry `recordIds` but **no field values**. Apex code that does not check for gap events will attempt to process null field bodies and silently miss changes.

The `ALL_CHANGE_EVENTS` channel and `AllChangeEvents` event type require the `ReceiveAllChangeEvents` org permission and are typically restricted to system integration use.

Note: CDC triggers cannot subscribe to multi-entity channels. An Apex trigger is always bound to a single change event type (e.g., `AccountChangeEvent`). There is no equivalent of subscribing to `/data/ChangeEvents` in Apex.

---

## Common Patterns

### Pattern 1: Field-Selective UPDATE Processing

**When to use:** The trigger should only react when specific fields change (e.g., `Status__c`, `OwnerId`) rather than on any update.

**How it works:**

```apex
trigger CaseChangeEventTrigger on CaseChangeEvent (after insert) {
    List<Id> casesWithStatusChange = new List<Id>();

    for (CaseChangeEvent event : Trigger.new) {
        EventBus.ChangeEventHeader header = event.ChangeEventHeader;

        // Skip non-UPDATE events
        if (header.changeType != 'UPDATE') {
            continue;
        }

        // Only act when Status field is in changedFields
        if (header.changedFields.contains('Status')) {
            casesWithStatusChange.addAll((List<Id>) header.getRecordIds());
        }
    }

    if (!casesWithStatusChange.isEmpty()) {
        // Query for full current state — do not rely on event field values for UPDATE
        List<Case> cases = [SELECT Id, Status, OwnerId FROM Case WHERE Id IN :casesWithStatusChange];
        CaseStatusHandler.process(cases);
    }
}
```

**Why not just read the field from the event:** For UPDATE events, unchanged fields are null in the event body. Reading `event.Status` when Status did not change returns null, not the current value. Always use `changedFields` to filter, then query the record for current state.

### Pattern 2: Change-Type Routing with GAP Handling

**When to use:** The trigger must handle all four operation types (CREATE, UPDATE, DELETE, UNDELETE) with distinct logic per type, and must be resilient to gap events.

**How it works:**

```apex
trigger AccountChangeEventTrigger on AccountChangeEvent (after insert) {
    List<Id> createdIds    = new List<Id>();
    List<Id> updatedIds    = new List<Id>();
    List<Id> deletedIds    = new List<Id>();
    List<Id> undeletedIds  = new List<Id>();
    List<Id> gapIds        = new List<Id>();

    for (AccountChangeEvent event : Trigger.new) {
        EventBus.ChangeEventHeader header = event.ChangeEventHeader;
        List<String> ids = header.getRecordIds();

        if (header.changeType == 'CREATE') {
            createdIds.addAll((List<Id>) ids);
        } else if (header.changeType == 'UPDATE') {
            updatedIds.addAll((List<Id>) ids);
        } else if (header.changeType == 'DELETE') {
            deletedIds.addAll((List<Id>) ids);
        } else if (header.changeType == 'UNDELETE') {
            undeletedIds.addAll((List<Id>) ids);
        } else if (header.changeType.startsWith('GAP_')) {
            // Gap event: no field values available — mark dirty for re-sync
            gapIds.addAll((List<Id>) ids);
        }
    }

    // Dispatch to handlers
    if (!createdIds.isEmpty())   AccountSyncHandler.handleCreate(createdIds);
    if (!updatedIds.isEmpty())   AccountSyncHandler.handleUpdate(updatedIds);
    if (!deletedIds.isEmpty())   AccountSyncHandler.handleDelete(deletedIds);
    if (!undeletedIds.isEmpty()) AccountSyncHandler.handleUndelete(undeletedIds);
    if (!gapIds.isEmpty())       AccountSyncHandler.handleGap(gapIds);
}
```

**Why not just check for UPDATE:** Failing to handle GAP events means silent data drift when events cannot be generated at full fidelity. Always check `changeType.startsWith('GAP_')` as a catch-all.

### Pattern 3: Multi-Record Batch Processing with getRecordIds

**When to use:** A single change event can contain multiple record IDs when Salesforce merges identical changes (e.g., a bulk update of the same field on many records). Always iterate `getRecordIds()` rather than assuming a 1:1 event-to-record relationship.

**How it works:**

```apex
trigger ContactChangeEventTrigger on ContactChangeEvent (after insert) {
    Set<Id> affectedContacts = new Set<Id>();

    for (ContactChangeEvent event : Trigger.new) {
        EventBus.ChangeEventHeader header = event.ChangeEventHeader;
        // getRecordIds() returns List<String>; cast to Id after collecting
        affectedContacts.addAll((List<Id>) header.getRecordIds());
    }

    // Single SOQL for the entire batch
    if (!affectedContacts.isEmpty()) {
        List<Contact> contacts = [
            SELECT Id, AccountId, Email, Status__c
            FROM Contact
            WHERE Id IN :affectedContacts
        ];
        ContactIntegrationHandler.process(contacts);
    }
}
```

**Why not iterate Trigger.new directly:** Each `Trigger.new` record is an event, but one event can represent changes to multiple records. Iterating events without collecting all `recordIds` will process the batch incorrectly. Pattern: collect all IDs across the batch, then issue a single SOQL.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Subscribe to record changes inside Salesforce with Apex logic | CDC trigger on `<Object>ChangeEvent` | Native async subscriber; full header field access |
| Need to act only when specific fields change | Check `header.changedFields` before processing | CDC exposes field-level delta; avoid unnecessary SOQL |
| Need to fire a synchronous callout from CDC handler | Dispatch to `@future(callout=true)` or `Queueable` | CDC triggers cannot perform synchronous callouts |
| Must handle DELETE | Add `changeType == 'DELETE'` branch; do not query deleted record | Deleted records are unavailable via SOQL without `ALL ROWS` |
| Event is manually published (not system DML) | Use `apex/platform-events-apex` instead | CDC events are system-generated only; cannot be published manually |
| External system (MuleSoft, Kafka) needs CDC events | Use `integration/change-data-capture-integration` | CometD/Pub/Sub API is the correct path for external subscribers |
| Need to track > 5 objects | Purchase CDC add-on or reassess scope | Default entity limit is 5; add-on removes cap |
| Debugging a CDC trigger — no logs visible | Set trace flag on Automated Process entity | CDC trigger runs under Automated Process, not the current user |
| Need to change the running user or batch size | Deploy `PlatformEventSubscriberConfig` via Metadata API | Controls trigger user context and invocation batch size |

---

## Recommended Workflow

1. **Confirm entity tracking** — Verify the target object is enabled in Setup > Integrations > Change Data Capture. Confirm the 5-entity limit is not exceeded without the add-on. For custom objects, confirm the correct change event API name (`<ObjectName>__ChangeEvent`).

2. **Define which change types require handling** — Identify whether CREATE, UPDATE, DELETE, UNDELETE, and/or GAP events each need distinct logic. If the use case is UPDATE-only with field filtering, identify the specific fields whose changes should trigger action.

3. **Write the trigger skeleton** — Use `trigger <Name> on <ChangeEventType> (after insert)`. Never use `before insert` or any other trigger event — CDC triggers only support `after insert`.

4. **Implement header access and change-type routing** — Access `event.ChangeEventHeader` for each event. Use `changeType` to route to per-operation handlers. Always include a `GAP_` branch that marks records dirty or queues a re-fetch.

5. **Implement field-level filtering for UPDATE events** — For UPDATE branches, check `header.changedFields` before processing. Query the record for full current state — do not read field values directly from the event body for UPDATE events, as unchanged fields are null.

6. **Collect all record IDs using `getRecordIds()`** — Accumulate IDs across all events in the batch using a `Set<Id>`. Issue a single bulk SOQL query outside the loop to retrieve current record state.

7. **Set up debug logging and test** — Configure a trace flag for the Automated Process entity. Write unit tests using `Test.getEventBus().deliver()` to verify all change-type branches, changedFields filtering, and GAP event handling.

---

## Review Checklist

- [ ] Trigger is declared as `after insert` on the change event type (not the base sObject).
- [ ] Object is enabled in Setup > Change Data Capture before deploying trigger.
- [ ] All relevant `changeType` values are handled: CREATE, UPDATE, DELETE, UNDELETE, and GAP events.
- [ ] `changedFields` is checked before processing UPDATE events to avoid reacting to unrelated field changes.
- [ ] Record IDs are collected via `header.getRecordIds()` — not assumed to be one record per event.
- [ ] Record state is retrieved via SOQL query for UPDATE processing — event field values are not used directly for changed fields (unchanged fields are null).
- [ ] No synchronous callouts in the trigger body; callouts dispatched to `@future(callout=true)` or `Queueable`.
- [ ] Batch-safe SOQL and DML: all queries and DML operate on collected Sets/Lists, not inside the event loop.
- [ ] Debug logs configured for the Automated Process entity.
- [ ] Unit tests cover all change-type branches including GAP, using `Test.getEventBus().deliver()`.

---

## Salesforce-Specific Gotchas

1. **CDC triggers run under Automated Process — not the current user** — Debug logs created by the trigger execution are attributed to the Automated Process entity, not the DML-performing user. Logs will not appear in the Developer Console log tab unless a trace flag is set for Automated Process in Setup > Debug Logs. Developers who look in the wrong place will conclude the trigger is not firing when it is.

2. **Unchanged fields are null in UPDATE event body** — For an UPDATE change event in Apex, fields that were not changed in the triggering DML are null on the event object. Reading `event.BillingCity` when `BillingCity` was not updated returns null — it does not return the current field value. Only `changedFields` reliably identifies what changed. Always query the record for full state rather than reading fields directly from UPDATE event bodies.

3. **Apex CDC triggers cannot subscribe to multi-entity channels** — An Apex trigger is bound to exactly one change event type. There is no way to write a single Apex trigger that handles `AccountChangeEvent` and `ContactChangeEvent`. Unlike external subscribers that can subscribe to `/data/ChangeEvents`, Apex triggers require one trigger file per tracked entity. Architects expecting a "catch-all" Apex subscriber will need one trigger per object.

4. **GAP events carry no field values** — A gap event fires when the full change event cannot be generated (event too large, bulk bypass, internal error). The event body is empty; only `recordIds` and the GAP-prefixed `changeType` are available. Apex code that skips the GAP check and falls through to field access will read null fields and silently skip the change. Production CDC subscribers must include explicit GAP handling that queues a record re-fetch.

5. **CDC triggers are subject to synchronous governor limits** — Despite running asynchronously, CDC triggers consume Apex synchronous limits (100 SOQL, 150 DML operations, 10 MB heap) per batch invocation. A batch of 2,000 events that naively issues one SOQL per event will hit the 100-SOQL limit. Always collect IDs across the full `Trigger.new` loop and issue bulk SOQL outside the loop.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CDC Apex trigger | Correctly declared `after insert` trigger on the change event type with header access and change-type routing |
| changedFields filter logic | Field-selective UPDATE filter using `header.changedFields.contains()` |
| GAP event handler | Branch detecting `GAP_`-prefixed changeType and dispatching to re-fetch logic |
| Entity tracking configuration | Setup guidance for enabling the object in Change Data Capture and confirming API name |
| PlatformEventSubscriberConfig | Metadata snippet to override running user or batch size when defaults are insufficient |
| Apex unit test pattern | Test class using `Test.getEventBus().deliver()` to exercise all change-type branches |

---

## Related Skills

- `integration/change-data-capture-integration` — Use when the CDC subscriber is an external system (MuleSoft, Kafka, custom gRPC client) connecting via CometD or Pub/Sub API.
- `apex/platform-events-apex` — Use when publishing or subscribing to custom Platform Events from Apex; also covers `EventBus.publish()` patterns.
- `architect/platform-selection-guidance` — Use when deciding between CDC, Platform Events, outbound messaging, and polling for an integration or automation pattern.
