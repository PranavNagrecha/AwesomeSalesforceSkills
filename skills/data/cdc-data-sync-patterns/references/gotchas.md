# Gotchas — CDC Data Sync Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in CDC replication pipelines.

## Gotcha 1: Gap Events Have Record IDs but No Field Data

**What happens:** A subscriber reads fields from every event and writes nulls into the replica when a gap event arrives.

**When it occurs:** The CDC guide lists the causes: the change event would exceed the 1 MB maximum message size; some custom field type conversions; an internal error; and changes applied directly in the database outside an application-server transaction, such as archiving of activities or a database cleanup job. The change type is `GAP_CREATE`, `GAP_UPDATE`, `GAP_DELETE`, or `GAP_UNDELETE`, and the header holds `recordIds` but the body holds no record data.

**How to avoid:** Check `changeType` before reading fields. For gap events, follow the guide's approach: mark each record dirty as of the gap event, ignore later change events for it until reconciled (compare `commitTimestamp`, and the retrieved record's `LastModifiedDate`), retrieve the record through the API, save it, and clear the flag.

---

## Gotcha 2: Position Storage Is the Client's Job Unless ManagedSubscribe Is Used

**What happens:** A subscriber restarts without a saved position and either skips everything published while it was down (`LATEST`) or replays everything retained (`EARLIEST`).

**When it occurs:** With the Pub/Sub API `Subscribe` RPC, the client provides the position in its first `FetchRequest` (`replay_preset` plus `replay_id`). The `ManagedSubscribe` RPC (Beta) is the exception: it lets you commit the replay ID of the last processed event on the server, and a resubscribe resumes after it.

**How to avoid:** Save the replay ID after each transaction is committed to the replica, store it as bytes, and also save the `replay_id` from each empty keepalive `FetchResponse` so the stored position stays recent. If client-side storage is the problem, evaluate `ManagedSubscribe` with its Beta status in mind.

---

## Gotcha 3: Three Days Is the Only Retention You Can Count On

**What happens:** A subscriber that was down for four days resumes from its stored replay ID and assumes the stream is complete, or a team assumes events older than three days can never appear.

**When it occurs:** Change data capture events are retained for 3 days. The Streaming API guide adds that purging sometimes starts later, so older events can still be available, but Salesforce doesn't guarantee storage beyond 72 hours. The Pub/Sub API guide recommends `EARLIEST` after a client has been disconnected for more than 3 days and its last saved replay ID is no longer valid; events between the old position and the earliest retained event are not recoverable from the stream.

**How to avoid:** Decide by elapsed time, not by whether a replay happens to work: if the last processed event's `commitTimestamp` is more than 3 days old, run a full re-sync of the replicated objects, then subscribe. Test what your client library reports for an out-of-window replay ID rather than assuming a specific error.

---

## Gotcha 4: `GAP_OVERFLOW` Has No Real Record ID

**What happens:** Gap-handling code reads `recordIds` from an overflow event and looks up `000000000000000AAA`, finds nothing, and moves on, while tens of thousands of changes are missing from the replica.

**When it occurs:** When one transaction has more than 100,000 changes, the first 100,000 generate change events and the rest generate one overflow event per entity type. Each field changed in an update counts toward the threshold. The overflow event carries `entityName` but only a dummy record ID. The guide's examples include a recurring event with hundreds of occurrences and a cascade delete of accounts with many related records.

**How to avoid:** Handle `GAP_OVERFLOW` separately: stop processing, save the overflow event's replay ID, retrieve every record of that entity and overwrite the replica, reconcile deletes (records the sync did not touch, or `IsDeleted = true` rows still in the Recycle Bin), then resubscribe from the saved replay ID.

---

## Gotcha 5: Committing Per Event Leaves Half-Applied Transactions

**What happens:** A lead conversion (account, contact, opportunity, and lead changes in one transaction) is half-replicated when the subscriber stops between events.

**When it occurs:** The guide warns that without a transaction-based process, replicated data can be incomplete if the subscription stops mid-transaction, and recommends replicating all changes in one transaction as a single commit.

**How to avoid:** Buffer events in a map keyed by `transactionKey`; when the next event has a different key, commit the buffered transaction, then save its last replay ID.

---

## Gotcha 6: Sequence-Number Gaps Are Normal When Some Objects Aren't Enabled

**What happens:** A subscriber that checks `sequenceNumber` for continuity raises false alarms or stalls waiting for events that will never arrive.

**When it occurs:** `sequenceNumber` starts at 1 within each transaction. The guide: "If not all objects involved in a transaction are enabled for Change Data Capture, there will be a gap in the sequence numbers."

**How to avoid:** Use `sequenceNumber` to order changes inside a transaction, not to prove completeness. Use the transaction buffer and reconciliation for completeness.

---

## Gotcha 7: A Filtered Channel Silently Drops Changes

**What happens:** A replica subscribed to a custom channel is missing records that fall outside the channel's filter.

**When it occurs:** A `PlatformEventChannelMember` can carry a `filterExpression` (API 56.0+) that delivers only events matching the criteria. The replication steps in the CDC guide subscribe to the general `/data/ChangeEvents` channel.

**How to avoid:** Subscribe replication to an unfiltered channel, and review channel member metadata in every release that touches it.

---

## Gotcha 8: Merged Events Carry Several Record IDs

**What happens:** A subscriber applies an update to `recordIds[0]` only, and the other records in the event never change in the replica.

**When it occurs:** When the same change is made to several records of one object in a transaction within one second (the same field to the same value, deletes, or a picklist value rename), Salesforce sends one change event whose `recordIds` holds all affected IDs. Gap events can be merged the same way.

**How to avoid:** Apply every change event and every gap event to each ID in `recordIds`.
