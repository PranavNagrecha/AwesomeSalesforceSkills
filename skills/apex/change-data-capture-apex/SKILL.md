---
name: change-data-capture-apex
description: "Use this skill when writing or reviewing Apex change event triggers: trigger syntax on ChangeEvent objects, reading ChangeEventHeader fields (changeType, changedFields, recordIds, commitUser), handling CREATE/UPDATE/DELETE/UNDELETE and GAP events in Apex, and configuring entity tracking. NOT for platform events published by application code (use apex/platform-events-apex). NOT for external CDC subscribers via CometD or Pub/Sub API (use integration/change-data-capture-integration). Keywords: AccountChangeEvent, MyObject__ChangeEvent, transactionKey, sequenceNumber, nulledFields, diffFields, changeOrigin, GAP_OVERFLOW, PlatformEventChannelMember, enrichedFields, PlatformEventSubscriberConfig, Test.enableChangeDataCapture, idempotent change event subscriber."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "how do I write a CDC trigger in Apex"
  - "handle change data capture events in Apex trigger"
  - "read ChangeEventHeader changedFields in Apex"
  - "detect which fields changed in CDC trigger"
  - "configure entity tracking for change data capture"
  - "handle GAP events in Apex CDC trigger"
  - "deduplicate change events with transactionKey and sequenceNumber"
  - "enable Change Data Capture for an object as deployable metadata"
  - "test a change event trigger with Test.enableChangeDataCapture"
  - "CDC trigger deployed but no debug log appears anywhere"
  - "changedFields always contains LastModifiedDate on every update"
  - "recordIds contains a 001 wildcard instead of a record Id"
  - "add enriched fields to a PlatformEventChannelMember"
  - "one change event carries multiple record IDs"
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
  - Idempotency key and dedupe store keyed on transactionKey + sequenceNumber
  - PlatformEventChannelMember XML that enables CDC for the object as deployable metadata
  - changedFields-based field filtering pattern
  - GAP event detection and recovery logic
  - Entity tracking configuration guidance
  - PlatformEventSubscriberConfig guidance when running user or batch size override is needed
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Change Data Capture Apex

Use this skill when implementing or reviewing Apex logic that subscribes to Salesforce record change events via CDC triggers. CDC triggers fire asynchronously after DML commits and provide rich header metadata (changeType, changedFields, recordIds, commitUser) for precise, efficient processing. This skill covers the complete Apex-side CDC pattern: trigger declaration, header field access, change-type routing, gap event handling, field-level filtering, and entity configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Is the object enabled for CDC?** The object must be selected on the Change Data Capture page in Setup — or, equivalently and repeatably, shipped as a `PlatformEventChannelMember` on the `ChangeEvents` channel (`api_meta` L95842–95844, L96098–96108). The trigger compiles but fires no events if the object is not tracked.
- **Is this a platform event?** If the event is manually published by application code (e.g., `EventBus.publish()`), use `apex/platform-events-apex` instead. CDC events are system-generated; they cannot be manually published.
- **What operations need handling?** CDC triggers fire for CREATE, UPDATE, DELETE, and UNDELETE. Confirm which change types the business logic must react to — GAP events also require handling in production.
- **Is synchronous callout needed?** CDC triggers run asynchronously under the Automated Process entity. Synchronous callouts from a CDC trigger are not supported. Use a queueable or @future(callout=true) dispatched from the trigger if callouts are required.
- **Batch size:** 2,000 event messages per trigger invocation (`apexdev` L19862), against 6 MB of heap (`apexdev` L19577). Override with `PlatformEventSubscriberConfig` (`batchSize` 1–2,000; never 1 — `api_meta` L96416–96424).
- **Does redelivery matter?** Nothing in Apex deduplicates change events. If the downstream effect is not naturally idempotent, the dedupe key is `transactionKey` + `sequenceNumber` (`apexrefguide` L157420–157441) and it needs a store — `references/code-examples.md` Artifact 5.
- **Is the field you want to watch a formula field?** If so, it will never appear in `changedFields` (`object_reference` L5157–5163). Watch its stored inputs instead.

---

## Questions to Ask Before Configuring

Ask these before writing the trigger. Each one changes a branch in the handler or a line in the
metadata, and each maps to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is the worst thing that happens if this event is delivered twice?" | Decides whether an idempotency store is required. Nothing in Apex deduplicates for you, and `transactionKey` alone is not a unique key — a lead conversion emits four numbered events under one key (`apexrefguide` L157429–157436) | A dedupe key of `transactionKey` + `sequenceNumber` and a unique External Id field to hold it, instead of a handler that double-posts on redelivery (Artifact 5 in `references/code-examples.md`) |
| "Which specific field changing is the reason this subscriber exists?" | Decides the `changedFields` test. `changedFields` always contains `LastModifiedDate` on an update (`apexrefguide` L157231–157232), so "did anything change" is never a useful filter | A named field the handler asks for, plus the `nulledFields` companion check so clearing the field still counts (`apexrefguide` L157381–157385) |
| "Is that field a formula, a roll-up, or a stored field?" | Change events exclude fields "whose value isn't on the record and is derived from another record or from a formula… except roll-up summary fields, which are included" (`object_reference` L5158–5163) | Either a stored field to watch, or the discovery — before build, not after — that a formula field will never appear in `changedFields` at all |
| "When the platform cannot generate a full event, what should happen?" | Decides the `GAP_*` / `GAP_OVERFLOW` branch (`apexrefguide` L157298–157304). A subscriber with no gap branch drifts silently | A named resync action and something that counts it, rather than a `changeType` chain that falls through to nothing |
| "Can the downstream effect of this handler itself change the same object?" | Decides whether `changeOrigin` must be read. It is "only populated for changes done by API apps or from Lightning Experience" and exists to "detect whether your app initiated the change to not process the change again and potentially avoid a deep cycle of changes" (`apexrefguide` L157197–157200) | A loop-breaker chosen deliberately — `changeOrigin`, a control flag, or `apex/recursive-trigger-prevention` — instead of a cycle discovered by a runaway event count |
| "Who owns the records this handler creates, and does it ever send email?" | The subscriber runs as the Automated Process entity by default, which cannot send email, and Automated Process users "can't perform Object and FLS checks in custom code unless appropriate permission sets are explicitly applied" (`api_meta` L96453–96465, `apexdev` L11921–11922) | A `PlatformEventSubscriberConfig` with a real `user`, or a written decision that Automated Process is correct plus the permission sets it needs |
| "How many events will one invocation actually carry, and what will they weigh?" | The batch is 2,000, not 200 (`apexdev` L19862), against 100 SOQL / 150 DML / 6 MB heap (`apexdev` L19542, L19553, L19577) | A deliberate `batchSize` — never 1 (`api_meta` L96419–96424) — and a handler that hydrates only the fields it consumes |

What a proper configuration adds over just writing the trigger: CDC enablement ships as metadata
instead of a Setup click that nobody repeats in the next org, redelivery cannot duplicate downstream
work, a gap becomes a counted resync rather than silent drift, the subscriber's identity and
permissions are a decision rather than a default, and the batch size is sized against heap rather
than inherited at 2,000.

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
- Execute **asynchronously** after the originating database transaction commits. They run outside the originating Apex transaction. UNVERIFIED (2026-09-05): stated in the Change Data Capture Developer Guide; the Apex Developer Guide, Apex Reference Guide and Object Reference do not state the delivery timing of a change event trigger.
- Run under the **Automated Process** entity, not the user who performed the DML — `api_meta` L96461–96462 ("By default, the platform event trigger runs as the Automated Process entity"). Debug logs must be configured for the Automated Process entity; setting a `user` in `PlatformEventSubscriberConfig` moves them, because "debug logs for the trigger execution are created by this user" (`api_meta` L96464).
- Are subject to **synchronous Apex governor limits** despite running asynchronously: 100 SOQL, 150 DML, 6 MB heap, 10,000 ms CPU (`apexdev` L19542, L19553, L19577, L19579). UNVERIFIED (2026-09-05): that a *change event trigger* falls in the synchronous column rather than the asynchronous one is stated in the Change Data Capture Developer Guide, not in the Apex guides. Do not infer it from the word "asynchronous" — see `references/llm-anti-patterns.md` Anti-Pattern 7.
- Have a maximum batch size of **2,000 event messages** per execution — "The Apex trigger batch size for platform events and Change Data Capture events is 2,000" (`apexdev` L19862). Multiple batches fire if more events are queued.
- Can be configured with `PlatformEventSubscriberConfig` (Metadata API, `batchSize` 1–2,000 and `user`; `api_meta` L96385–96480) to override the running user identity and default batch size. UNVERIFIED (2026-09-05): `api_meta` L96385–96386 scopes this type to "a platform event Apex trigger"; that change event triggers are in scope is a Change Data Capture Developer Guide claim.
- Cannot enqueue one Queueable per event: `System.enqueueJob` allows 50 calls in a synchronous context and **1** in an asynchronous one (`apexdev` L19571). Enqueue once per invocation, after the loop.

### ChangeEventHeader and Header Fields

Every event in `Trigger.new` exposes a `ChangeEventHeader` field (type `EventBus.ChangeEventHeader`) that carries all change metadata. Access it via the event's `.ChangeEventHeader` property.

Key header fields for Apex:

Every property below is from `EventBus.ChangeEventHeader` (`apexrefguide` L157183–157447). There are
twelve; a subscriber that reads only the first four is leaving its idempotency and its failure modes
on the table.

| Field | Type | Description | Line |
|---|---|---|---|
| `changeType` | String | `CREATE`, `UPDATE`, `DELETE`, `UNDELETE`, `SNAPSHOT` (reserved for future use), `GAP_CREATE`/`GAP_UPDATE`/`GAP_DELETE`/`GAP_UNDELETE`, and `GAP_OVERFLOW` for overflow events | L157286–157304 |
| `changedFields` | List\<String\> | Fields changed in an update, **including the `LastModifiedDate` system field**; empty for other operations including record creation. API 47.0+ | L157231–157236 |
| `nulledFields` | List\<String\> | Fields whose values were changed to null in an update. This is how you tell "set to null" apart from "unchanged" | L157381–157385 |
| `diffFields` | List\<String\> | Fields whose values are sent as a **unified diff** because they contain large text values | L157353–157360 |
| `recordIds` | List\<String\> | One or more record IDs. Salesforce merges notifications when the same change hits multiple records of one object type within one second in one transaction. Can also be a **wildcard** (`001*`) for a custom field type conversion that loses data | L157393–157417 |
| `entityName` | String | API name of the changed object — `Account`, `MyObject__c` | L157371–157377 |
| `changeOrigin` | String | `com/salesforce/api/<API_Name>/<API_Version>;client=<Client_ID>`. Only populated for changes made by API apps or from Lightning Experience. Exists so an app can detect its own changes "to not process the change again and potentially avoid a deep cycle of changes" | L157245–157275 |
| `commitUser` | String | ID of the user that ran the change operation | L157333–157339 |
| `commitTimestamp` | Long | Milliseconds since 1970-01-01 00:00:00 GMT. A `Long`, not a `Datetime` | L157321–157330 |
| `commitNumber` | Long | System change number, sequential — **but "not guaranteed to be unique in Salesforce… unique only in a single database instance"** and possibly non-sequential after an instance migration. Diagnostics only | L157306–157318 |
| `sequenceNumber` | Integer | The change's sequence within the transaction, starting at 1. A lead conversion produces four | L157420–157436 |
| `transactionKey` | String | Uniquely identifies each Salesforce transaction; groups all changes made in the same transaction | L157438–157447 |

The idempotency key is `transactionKey` + `sequenceNumber`, not `transactionKey` alone and never
`commitNumber`. See `references/code-examples.md` Artifact 4.

UNVERIFIED (2026-09-05): the claim that `changedFields` and `nulledFields` are available in Apex
triggers and Pub/Sub API only, and absent in CometD subscribers, is a Change Data Capture Developer
Guide claim; the Apex Reference Guide documents the properties without stating which subscriber
transports carry them.

UNVERIFIED (2026-09-05): `recordIds` is documented as a **property** — `public List<String> recordids {get; set;}`
(`apexrefguide` L157400) — not as a `getRecordIds()` method. The getter form used elsewhere in this
package comes from the Change Data Capture Developer Guide; the only getter the Apex Developer Guide
shows is `getChangeType()`, in the External Change Data Capture sample at `apexdev` L29639. New code
in `references/code-examples.md` uses the property form.

### Change Event Body Fields in Apex

**Unchanged fields are null in the event message.** That is the whole reason `nulledFields` exists —
its documented purpose is "to determine if a field was changed to null in an update and isn't an
unchanged field" (`apexrefguide` L157381–157385). Do not read a field off the event and assume its
value is current; use `changedFields` to decide what changed, then query the record for full state.

The event object is also **not** a full copy of the record. Change event fields correspond to the
parent object's fields with these exclusions (`object_reference` L5157–5163):

- the `IsDeleted` system field;
- the `SystemModStamp` system field;
- any field whose value is derived from another record or from a formula — formula fields,
  `LastActivityDate`, `PhotoUrl` — **except roll-up summary fields, which are included**.

So a formula field can never appear in `changedFields`, and a subscriber designed to watch one will
never fire. Watch the stored fields the formula reads instead.

Change events also exist for only a subset of standard objects, plus all custom objects; the list is
in `object_reference` L5211+. Change events for custom settings "aren't supported in Apex triggers
but are supported in other types of subscribers" (`object_reference` L5140–5143).

### Entity Tracking and GAP Events

CDC must be explicitly enabled per object. The Setup page is one face of it: "the default standard
channel corresponds to the entity selection in the Change Data Capture page in Setup" (`api_meta`
L95842–95844). The other face is deployable — a `PlatformEventChannelMember` naming
`AccountChangeEvent` on the `ChangeEvents` channel (`api_meta` L96098–96108). Ship the metadata; do
not leave a Setup click as an undocumented prerequisite in every downstream org. `references/code-examples.md`
Artifact 1 is the file.

UNVERIFIED (2026-09-05): the **5-entity** default and the CDC add-on that lifts it are Change Data
Capture allocation numbers. The App Limits cheat sheet in the grounding corpus only points at the
"Change Data Capture Allocations" section (L1249–1251) without reproducing the values.

Gap events carry a `changeType` prefixed by `GAP_` — `GAP_CREATE`, `GAP_UPDATE`, `GAP_DELETE`,
`GAP_UNDELETE` — and overflow events use `GAP_OVERFLOW` (`apexrefguide` L157298–157304). A
`changeType.startsWith('GAP_')` test catches all five.

UNVERIFIED (2026-09-05): the *causes* of gap events (event over 1 MB, a bulk operation bypassing the
application server, an internal error) and the claim that gap events carry `recordIds` but no field
values are Change Data Capture Developer Guide statements. The Apex Reference Guide names the
`changeType` values without describing the payload.

UNVERIFIED (2026-09-05): the `ALL_CHANGE_EVENTS` channel, the `AllChangeEvents` event type and the
`ReceiveAllChangeEvents` permission return zero hits across `api_meta`, `object_reference`, `apexdev`,
`apexrefguide` and the App Limits cheat sheet. Treat as unconfirmed until read in the CDC guide.

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
| Enable CDC for an object in a repeatable way | Deploy `PlatformEventChannelMember` on the `ChangeEvents` channel | The Setup page selection *is* this metadata (`api_meta` L95842–95844, L96098–96108) |
| Subscriber needs a field that did not change on this event | Custom channel + `enrichedFields` on the member | "A non-empty enriched field is added to an update or delete change event even when not changed" (`api_meta` L96047–96050) |
| Subscriber should never see most of the events | `filterExpression` on the channel member (API 56.0+) | Filtering in the platform costs no Apex limits; filtering in the trigger costs a full 2,000-event batch (`api_meta` L96057–96066) |
| Redelivery must not double-apply the downstream effect | Dedupe on `transactionKey` + `sequenceNumber` | One transaction emits several numbered events — a lead conversion emits four (`apexrefguide` L157429–157436) |
| Need to order or key on a monotonic number | Do **not** use `commitNumber` | "Not guaranteed to be unique in Salesforce — it is unique only in a single database instance" (`apexrefguide` L157306–157310) |
| Want to react to a formula or roll-up field changing | Watch the stored fields the formula reads; roll-ups are fine | Formula and derived fields are excluded from change events; roll-up summary fields are included (`object_reference` L5157–5163) |
| Handler's own DML could re-trigger this subscriber | Read `changeOrigin`, or apply `apex/recursive-trigger-prevention` | `changeOrigin` exists to "detect whether your app initiated the change… avoid a deep cycle of changes" (`apexrefguide` L157197–157200) |
| Need to track > 5 objects | Purchase CDC add-on or reassess scope | UNVERIFIED (2026-09-05): the 5-entity default and the add-on are CDC allocation numbers not reproduced in the App Limits cheat sheet (L1249–1251) |
| Debugging a CDC trigger — no logs visible | Set trace flag on Automated Process entity | CDC trigger runs under Automated Process, not the current user |
| Need to change the running user or batch size | Deploy `PlatformEventSubscriberConfig` via Metadata API | Controls trigger user context and invocation batch size |

---

## Recommended Workflow

1. **Answer the seven questions above first.** The idempotency answer decides whether Artifact 5
   (`Change_Event_Receipt__c`) ships; the watched-field answer decides whether that field is even
   capable of appearing in `changedFields` (formula fields are not — `object_reference` L5157–5163).
   Both are cheaper to settle now than after the handler exists.

2. **Confirm the change event name and check it against the siblings.** `<Object>ChangeEvent` for
   standard objects, `<Object>__ChangeEvent` for custom (`object_reference` L5148–5156). If the
   subscriber is external, stop here and use `integration/change-data-capture-integration`. If the
   event is published by your own code rather than by a DML commit, use `apex/platform-events-apex`.

3. **Ship CDC enablement as metadata, not a Setup click.** Write
   `ChangeEvents_<Object>ChangeEvent.platformEventChannelMember-meta.xml`
   (`references/code-examples.md` Artifact 1). Use a custom channel with `enrichedFields` or a
   `filterExpression` (Artifact 2) only when the subscriber needs a field that did not change, or
   needs the platform to drop events before Apex sees them.

4. **Write a one-line trigger and put everything in the handler** — Artifacts 3 and 4. The handler
   makes four passes: decode headers with no SOQL or DML; query the receipt store once to drop units
   already processed; issue one hydration query; insert receipts with `allOrNone = false`. Route on
   `changeType` with a real `else` branch, guard `recordIds` against the `001*` wildcard before
   casting to `Id`, and log through `templates/apex/ApplicationLogger.cls`.

5. **Decide the subscriber's identity before deploying, not after a permissions failure.** Ship
   `PlatformEventSubscriberConfig` (Artifact 6) with a real `user` if the handler creates owned
   records or sends email; otherwise grant the Automated Process user the object and field
   permissions the handler needs (`apexdev` L11921–11922).

6. **Run the checker over the source tree.** Its seven rules map one-to-one to gotchas in
   `references/gotchas.md`:
   `python3 skills/apex/change-data-capture-apex/scripts/check_change_data_capture_apex.py --manifest-dir force-app/main/default`
   Add `--strict` in CI to promote WARN findings to failures.

7. **Test with `Test.enableChangeDataCapture()` and an explicit `deliver()`** — Artifact 7. Call
   `enableChangeDataCapture()` at the top, before any DML (`apexrefguide` L240421–240423). Drain the
   CREATE event before asserting on an UPDATE. Remember that the method fires triggers "regardless of
   the entities selected in Setup" (`apexrefguide` L240433–240435), so a green test is not evidence
   the entity is enabled — verify that separately (`references/code-examples.md`, Verification).

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
- [ ] Unit tests cover all change-type branches including GAP, using `Test.enableChangeDataCapture()` at the top and an explicit `Test.getEventBus().deliver()` per delivery phase.
- [ ] CDC enablement ships as a `PlatformEventChannelMember` file, not as a Setup instruction in a runbook.
- [ ] The handler is idempotent on `transactionKey` + `sequenceNumber` — not `transactionKey` alone, and not `commitNumber`.
- [ ] `recordIds` entries are checked for the `001*` wildcard form before being cast to `Id`.
- [ ] The `changeType` chain has an `else` branch; `SNAPSHOT` and any future value are logged, not dropped.
- [ ] The watched field is a stored field, not a formula or other derived field.
- [ ] `System.enqueueJob` is called at most once per invocation, outside the event loop.
- [ ] The subscriber's running identity is a decision: either a `PlatformEventSubscriberConfig` `user`, or documented permission sets on the Automated Process user.
- [ ] `python3 skills/apex/change-data-capture-apex/scripts/check_change_data_capture_apex.py --manifest-dir <src>` exits 0.

---

## Salesforce-Specific Gotchas

1. **CDC triggers run under Automated Process — not the current user** — Debug logs created by the trigger execution are attributed to the Automated Process entity, not the DML-performing user. Logs will not appear in the Developer Console log tab unless a trace flag is set for Automated Process in Setup > Debug Logs. Developers who look in the wrong place will conclude the trigger is not firing when it is.

2. **Unchanged fields are null in UPDATE event body** — For an UPDATE change event in Apex, fields that were not changed in the triggering DML are null on the event object. Reading `event.BillingCity` when `BillingCity` was not updated returns null — it does not return the current field value. Only `changedFields` reliably identifies what changed. Always query the record for full state rather than reading fields directly from UPDATE event bodies.

3. **Apex CDC triggers cannot subscribe to multi-entity channels** — An Apex trigger is bound to exactly one change event type. There is no way to write a single Apex trigger that handles `AccountChangeEvent` and `ContactChangeEvent`. Unlike external subscribers that can subscribe to `/data/ChangeEvents`, Apex triggers require one trigger file per tracked entity. Architects expecting a "catch-all" Apex subscriber will need one trigger per object.

4. **GAP events carry no field values** — A gap event fires when the full change event cannot be generated (event too large, bulk bypass, internal error). The event body is empty; only `recordIds` and the GAP-prefixed `changeType` are available. Apex code that skips the GAP check and falls through to field access will read null fields and silently skip the change. Production CDC subscribers must include explicit GAP handling that queues a record re-fetch.

5. **CDC triggers are subject to synchronous governor limits** — Despite running asynchronously, CDC triggers consume Apex **synchronous** limits (100 SOQL, 150 DML operations, **6 MB heap**) per batch invocation. Read that heap number carefully: it is the synchronous 6 MB, *not* the 12 MB an asynchronous context would suggest — the "runs asynchronously" framing is exactly what misleads people into budgeting double. A batch of 2,000 events that naively issues one SOQL per event will hit the 100-SOQL limit; 2,000 events plus their queried parent records against 6 MB is a real heap constraint, not a theoretical one. Always collect IDs across the full `Trigger.new` loop and issue bulk SOQL outside the loop, and keep only the fields you need.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CDC Apex trigger | Correctly declared `after insert` trigger on the change event type with header access and change-type routing |
| changedFields filter logic | Field-selective UPDATE filter using `header.changedFields.contains()` |
| GAP event handler | Branch detecting `GAP_`-prefixed changeType and dispatching to re-fetch logic |
| Entity tracking metadata | `PlatformEventChannelMember` XML that enables the object for CDC on the `ChangeEvents` channel, or a custom channel plus member with `enrichedFields` / `filterExpression` |
| Idempotency store | `Change_Event_Receipt__c` with a unique External Id keyed on `transactionKey` + `sequenceNumber`, and the partial-success insert that claims a unit |
| PlatformEventSubscriberConfig | Metadata snippet to override running user or batch size when defaults are insufficient |
| Apex unit test pattern | Test class using `Test.enableChangeDataCapture()` plus explicit `Test.getEventBus().deliver()` calls, asserting the handler's effect for CREATE and UPDATE |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are building the slice — channel-member XML, custom channel with enriched fields, trigger, idempotent handler, receipt object, subscriber config, test class, `package.xml`, deploy order, verification |
| `references/gotchas.md` | The subscriber is behaving in a way the code does not explain: a field that never appears in `changedFields`, a cast that throws, a receipt that duplicates, logs that are nowhere |
| `references/examples.md` | You want worked scenarios: SLA-field filtering, a full change-type router with gap recovery, and the raw event payload with the dedupe key derived from it |
| `references/llm-anti-patterns.md` | You are reviewing generated CDC Apex — seven failure modes with detection hints, including the heap number assistants invent |
| `references/well-architected.md` | You are tagging findings by pillar, or you need the exact source and line range behind a claim in this package |

## Related Skills

- `integration/change-data-capture-integration` — Use when the CDC subscriber is an external system (MuleSoft, Kafka, custom gRPC client) connecting via CometD or Pub/Sub API. Owns the external-subscriber and replay-id design; this skill does not.
- `apex/platform-events-apex` — Owns `__e` publish/subscribe mechanics: `EventBus.publish` results, `EventPublishFailureCallback`, `RetryableException`, `setResumeCheckpoint`, and reading `EventBusSubscriber` health. A CDC subscriber inherits all of it; read that skill rather than re-deriving it here.
- `apex/apex-event-bus-subscriber` — Use for the subscriber runtime itself: retry budgets, resume behaviour, and what a stalled subscription looks like.
- `apex/recursive-trigger-prevention` — Use when the handler's own DML can produce the change event it subscribes to. `changeOrigin` is the CDC-specific signal; the loop-breaking patterns live there.
- `data/cdc-data-sync-patterns` — Use for the downstream reconciliation design: what a resync actually does after a `GAP_*` event, and how to prove the two systems agree.
- `architect/platform-selection-guidance` — Use when deciding between CDC, Platform Events, outbound messaging, and polling for an integration or automation pattern.
- `standards/decision-trees/integration-pattern-selection.md` — Read before choosing CDC at all. The branch that lands here is "one-way, SF → external / audit or replication target → Change Data Capture" (L110, L124); the same tree sends custom event shapes to Platform Events instead (L143).
