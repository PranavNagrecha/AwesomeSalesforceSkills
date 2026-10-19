---
name: cdc-data-sync-patterns
description: "Use this skill for the replication lifecycle of CDC-based data synchronization: day-0 full load, incremental delta processing, replay ID management, gap event fallback, and ordering/deduplication using transactionKey and sequenceNumber. NOT for CDC entity selection, channel config, or edition limits — use integration/change-data-capture-integration. NOT for checking whether the two systems actually match — use data/data-reconciliation-patterns."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - change-data-capture
  - CDC
  - replication
  - replay-id
  - gap-events
  - bulk-api
  - data-sync
  - incremental-load
  - transactionKey
  - sequenceNumber
triggers:
  - "How do I implement incremental CDC replication without data drift"
  - "CDC subscriber went offline for 3 days — how to re-sync"
  - "Handling GAP_CREATE events in my CDC pipeline"
  - "replicate Salesforce accounts to a warehouse with an initial load and then change events"
  - "handle a GAP_OVERFLOW event after a cascade delete in my change data capture subscriber"
  - "store the replay id so my Pub/Sub API subscriber resumes where it stopped"
inputs:
  - Target objects being replicated and their approximate record volume
  - External datastore type (data warehouse, database, data lake)
  - Acceptable replication lag (near-real-time vs batch tolerance)
  - "Current subscriber state: new deployment vs reconnect vs post-outage recovery"
  - Time the subscriber was offline (if recovering from an outage)
outputs:
  - Day-0 load strategy (Bulk API query job design)
  - Incremental CDC replication design with replay ID persistence plan
  - Gap event fallback query logic
  - Ordering and deduplication design using transactionKey and sequenceNumber
  - Offline recovery decision tree (replay vs full re-sync)
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# CDC Data Sync Patterns

Use this skill when designing or debugging a replication pipeline built on Change Data Capture: the day-0 load, transaction-based processing of change events, replay ID storage, gap and overflow handling, and recovery after an outage. CDC setup itself (entity selection, channels, allocations) belongs to `integration/change-data-capture-integration`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **New or reconnecting subscriber?** A new pipeline needs a day-0 load; a reconnecting one needs its last saved replay ID and the time of its last processed event.
- **How long was it offline?** Change events are retained for 3 days (72 hours). Past that, Salesforce doesn't guarantee the events, so a re-sync is needed.
- **Which API?** Pub/Sub API uses replay presets `LATEST`, `EARLIEST`, and `CUSTOM` with a `replay_id`; Streaming API (CometD) uses `-1`, `-2`, or a replay ID.
- **Which channel?** A replica needs every change; a channel member with a `filterExpression` delivers only matching events.
- **Who stores the position?** With `Subscribe`, the client stores the replay ID. The `ManagedSubscribe` RPC (Beta) can commit it on the server instead.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Where is the replay ID stored, and is it written only after the transaction's changes are committed downstream?" | A position saved before the commit loses changes on restart; one saved long after replays duplicates (Gotcha 2) | A store written in the same unit of work as the replica commit |
| "How will the subscriber know it was offline longer than 3 days?" | Retention is 3 days and storage past that isn't guaranteed (Gotcha 3) | A rule based on the time of the last processed event that triggers a re-sync |
| "What does the subscriber do with GAP_CREATE, GAP_UPDATE, GAP_DELETE, and GAP_UNDELETE?" | Gap events carry the record ID but no field data (Gotcha 1) | A mark-dirty-then-retrieve path per record |
| "And with GAP_OVERFLOW?" | Overflow events carry no real record ID, only an entity name (Gotcha 4) | A per-entity re-sync from the overflow event's replay ID |
| "Does the replica commit per transaction or per event?" | Committing part of a transaction leaves the replica inconsistent if the stream stops (Gotcha 5) | A buffer keyed by `transactionKey`, committed when the key changes |
| "Is every object in the transaction enabled for CDC?" | Objects that aren't enabled leave gaps in `sequenceNumber` (Gotcha 6) | A sequence check that does not treat those gaps as lost events |
| "Is the subscription channel filtered?" | A `filterExpression` on the channel member drops non-matching changes (Gotcha 7) | An unfiltered channel for replication |

A proper replication design adds a stored position, gap and overflow paths, and transaction-level commits; "just subscribing" produces a replica that drifts silently after the first restart or bulk change.

---

## Core Concepts

### Retention and replay options

Change events are retained for 3 days. The Streaming API guide notes that purging sometimes starts later and older events can still be available, but Salesforce doesn't guarantee storage beyond 72 hours, so design as if anything older is gone.

| Pub/Sub API `replay_preset` | Streaming API (CometD) | Behaviour |
|---|---|---|
| `LATEST` (default) | `-1` (default) | Only events published after subscribing |
| `EARLIEST` | `-2` | Everything retained, then new events; use sparingly |
| `CUSTOM` + `replay_id` | the replay ID | Events after the given event |

Replay IDs are opaque: store them as bytes, don't compute new ones from a stored one, and don't assume they are contiguous (Streaming API guide L349-353). With Pub/Sub API, an empty `FetchResponse` (keepalive) carries the latest `replay_id`; saving it keeps the stored position recent. UNVERIFIED (2026-10-19): the Pub/Sub API column, the keepalive `replay_id`, and `ManagedSubscribe` come from the Pub/Sub API reference, which is not in the local PDF corpus; the CometD options and 72-hour retention are confirmed (Streaming API guide L324-334, L460-480).

### Event types in the stream

| `changeType` | Content | Subscriber action |
|---|---|---|
| `CREATE`, `UPDATE`, `DELETE`, `UNDELETE` | Header plus changed fields | Buffer by `transactionKey`, commit per transaction |
| `GAP_CREATE`, `GAP_UPDATE`, `GAP_DELETE`, `GAP_UNDELETE` | Header with `recordIds`, no field data | Mark the records dirty, retrieve them, clear the flag |
| `GAP_OVERFLOW` | Header only; dummy record ID `000000000000000AAA` | Re-sync the whole entity named in `entityName` |

Gap events come from: events over the 1 MB message size, some custom field type conversions, internal errors, and changes applied directly in the database outside an application-server transaction (for example, archiving of activities). Overflow events follow the first 100,000 changes in a single transaction, one per entity type. UNVERIFIED (2026-10-19): the gap causes, the four `GAP_` types, the 100,000-change overflow threshold, the dummy record ID, and record-ID merging come from Change Data Capture Developer Guide pages that are not in the local PDF corpus; the header fields `transactionKey`, `sequenceNumber`, `commitTimestamp`, and `recordIds` appear in the Streaming API guide's change event sample (L398-410).

### Header fields that drive ordering

`transactionKey` uniquely identifies the transaction; `sequenceNumber` is the position of the change within it, starting at 1; `commitTimestamp` is when the change occurred (milliseconds since the epoch); `recordIds` can hold several IDs when Salesforce merges identical changes made to records of the same object in one transaction within one second.

### The channel member a replica depends on

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- platformEventChannelMembers/ChangeEvents_AccountChangeEvent.platformEventChannelMember
     Selects Account for the standard ChangeEvents channel. No filterExpression: a replica needs every change. -->
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
    <eventChannel>ChangeEvents</eventChannel>
    <selectedEntity>AccountChangeEvent</selectedEntity>
</PlatformEventChannelMember>
```

---

## Common Patterns

### Pattern 1: Day-0 load, then change events

1. Subscribe with `LATEST` (or `-1`) and save the `replay_id` from the first keepalive or event; that is the handoff point.
2. Run a Bulk API 2.0 query job for each object and load the results.
3. Resubscribe with `CUSTOM` and the saved replay ID so changes made during the load are applied after it.
4. Apply events through the transaction buffer; because some changes during the load are also in the extract, writes must be idempotent upserts keyed by record ID.

### Pattern 2: Transaction-based processing

Buffer events in a map keyed by `transactionKey`. When the key changes, commit the previous transaction's changes in one unit and then save the replay ID of its last event. On a gap event, mark each record in `recordIds` dirty as of the event, ignore later change events for those records until they are reconciled (compare `commitTimestamp`, and `LastModifiedDate` on the retrieved record), retrieve the records, save them, and clear the flag.

### Pattern 3: Overflow or long outage recovery

On `GAP_OVERFLOW`, stop processing, save the overflow event's replay ID, retrieve all records of the entity and overwrite the replica, reconcile deletes (records the sync did not touch, or `IsDeleted = true` rows from the Recycle Bin), then resubscribe from the saved replay ID. After an outage longer than 3 days, run the same full re-sync per object, then subscribe with `EARLIEST` or from a fresh handoff point.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| New pipeline, existing records | Handoff replay ID, Bulk API 2.0 extract, resubscribe from the handoff | CDC sends changes, not existing state |
| Restart within 3 days | `CUSTOM` with the stored replay ID | Resumes after the last processed event |
| Offline more than 3 days | Full re-sync, then subscribe | Older events aren't guaranteed |
| Gap event | Mark dirty, retrieve by `recordIds`, then clear | No field data in the event |
| `GAP_OVERFLOW` | Re-sync the entity from the overflow replay ID | No usable record IDs |
| Client-side position storage is a burden | Evaluate `ManagedSubscribe` (Beta) | Commits the replay ID on the server |
| Filtered custom channel exists | Subscribe the replica to an unfiltered channel | Filters drop changes |

---

## Recommended Workflow

1. Fill `templates/cdc-data-sync-patterns-template.md`: objects, channel (and whether it is filtered), API (Pub/Sub or CometD), position store, and the outage rule (last processed `commitTimestamp` older than 3 days means re-sync).
2. Confirm each object's `PlatformEventChannelMember` on the channel the pipeline uses, with no `filterExpression`.
3. Build the subscriber with the transaction buffer, gap path, and overflow path from Patterns 2 and 3; `references/worked-example.md` traces one stream through all three.
4. Run `python3 skills/data/cdc-data-sync-patterns/scripts/check_cdc_data_sync_patterns.py --manifest-dir <subscriber source>` and fix every ERROR.
5. Test in a sandbox: restart mid-transaction, a gap (exceed 1 MB or convert a custom field type), an overflow (one transaction with more than 100,000 changes, such as a large cascade delete), and a simulated 4-day outage.
6. Reconcile counts against Salesforce after each test with `data/data-reconciliation-patterns`.

---

## Review Checklist

- [ ] The day-0 load starts after a handoff replay ID is saved, and the stream resumes from it
- [ ] The replay ID is saved after each transaction commits downstream, as bytes
- [ ] All four `GAP_` change types go through mark-dirty-and-retrieve
- [ ] `GAP_OVERFLOW` triggers a per-entity re-sync, not a record lookup
- [ ] Changes are committed per `transactionKey`, ordered by `sequenceNumber`
- [ ] A last-processed time older than 3 days routes to a full re-sync
- [ ] The subscribed channel has no `filterExpression` for replicated objects
- [ ] The checker reports no ERROR lines

---

## Salesforce-Specific Gotchas

Full write-ups are in `references/gotchas.md`:

| # | Gotcha |
|---|---|
| 1 | Gap events have record IDs but no field data |
| 2 | Position storage is the client's job unless ManagedSubscribe is used |
| 3 | Three days is the only retention you can count on |
| 4 | `GAP_OVERFLOW` has no real record ID |
| 5 | Committing per event leaves half-applied transactions |
| 6 | Sequence-number gaps are normal when some objects aren't enabled |
| 7 | A filtered channel silently drops changes |
| 8 | Merged events carry several record IDs |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Day-0 load design | Handoff replay ID, Bulk API 2.0 extract, resubscribe point |
| Subscriber design | Transaction buffer, gap path, overflow path, position store |
| Recovery runbook | Restart within 3 days versus full re-sync |
| Channel member metadata | `PlatformEventChannelMember` for each replicated object |
| Filled template | `templates/cdc-data-sync-patterns-template.md` |

---

## Related Skills

- `integration/change-data-capture-integration` — entity selection, channels, allocations, and subscriber technology
- `integration/pub-sub-api-patterns` — Pub/Sub API client mechanics (flow control, schemas)
- `apex/change-data-capture-apex` — when the subscriber is an Apex trigger
- `data/data-reconciliation-patterns` — checking that the replica and Salesforce match
- `data/bulk-api-patterns` — the Bulk API 2.0 query job used for day-0 and re-sync loads
