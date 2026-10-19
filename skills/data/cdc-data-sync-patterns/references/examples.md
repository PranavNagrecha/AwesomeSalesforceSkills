# Examples — CDC Data Sync Patterns

The Python below is illustrative pipeline code: `pubsub`, `bulk_api`, `rest_api`, `store`, and `replica` stand for your own client wrappers, not Salesforce libraries.

## Example 1: Day-0 Full Load Followed by Incremental CDC

**Context:** A data engineering team replicates Account and Opportunity into a warehouse. Both objects already hold millions of records, and change events only describe changes, not existing state.

**Problem:** Subscribing after the load misses changes made during the load; subscribing before it, without a saved position, has nowhere safe to resume from.

**Solution:**

```python
# Step 1: open a subscription at the tip and save a handoff position.
# An empty keepalive FetchResponse carries the latest replay_id.
handoff = pubsub.first_replay_id(topic="/data/ChangeEvents", replay_preset="LATEST")
store.save_bytes("cdc_handoff", handoff)

# Step 2: extract current state with Bulk API 2.0 query jobs.
for obj, soql in [("Account", "SELECT Id, Name, BillingCity, LastModifiedDate FROM Account"),
                  ("Opportunity", "SELECT Id, Name, StageName, LastModifiedDate FROM Opportunity")]:
    job = bulk_api.create_query_job(soql)
    for rows in bulk_api.iter_results(job):        # follows Sforce-Locator until the string "null"
        replica.upsert(obj, rows, key="Id")

# Step 3: resubscribe from the handoff so changes made during the load are applied after it.
pubsub.subscribe(topic="/data/ChangeEvents", replay_preset="CUSTOM",
                 replay_id=store.load_bytes("cdc_handoff"), handler=process_event)
```

**Why it works:** The handoff position is taken before the extract starts, so every change made during the extract is replayed afterwards. Upserts by record ID make the overlap harmless.

---

## Example 2: Gap Event Handling With a Dirty Flag

**Context:** A database-level cleanup job changed Account rows outside an application-server transaction, and the subscriber received `GAP_UPDATE` events for them.

**Problem:** The gap event's header has `recordIds` but the body has no field data. Writing the body to the replica would null out fields.

**Solution:**

```python
GAP_TYPES = {"GAP_CREATE", "GAP_UPDATE", "GAP_DELETE", "GAP_UNDELETE"}

def process_event(event):
    header = event["ChangeEventHeader"]
    change_type = header["changeType"]
    if change_type == "GAP_OVERFLOW":
        start_entity_resync(header["entityName"], event["replay_id"])   # see Gotcha 4
        return
    if change_type in GAP_TYPES:
        for record_id in header["recordIds"]:                            # merged gaps carry several IDs
            replica.mark_dirty(record_id, as_of=header["commitTimestamp"])
            reconcile_queue.put(record_id)
        return
    for record_id in header["recordIds"]:
        if replica.is_dirty(record_id):
            continue                                                     # wait for reconciliation
        buffer.add(header["transactionKey"], header["sequenceNumber"], record_id, event)

def reconcile(record_id):
    current = rest_api.get_record("Account", record_id)                  # REST sObject Rows GET
    replica.upsert("Account", [current], key="Id")
    replica.clear_dirty(record_id)
```

**Why it works:** It follows the CDC guide's gap procedure: mark dirty, skip later change events for the record until reconciled, retrieve the record, then clear the flag. Overflow events are routed away before any `recordIds` lookup, because their record ID is a dummy value.

---

## Example 3: Restart After a 4-Hour Outage, and After a 4-Day One

**Context:** The subscriber stores its position after each committed transaction, plus the time of the last processed event.

**Solution:**

```python
from datetime import datetime, timedelta, timezone

RETENTION = timedelta(days=3)

def on_transaction_committed(last_event):
    store.save_bytes("cdc_replay_id", last_event["replay_id"])              # opaque bytes
    store.save("cdc_last_commit_ms", last_event["ChangeEventHeader"]["commitTimestamp"])

def resume():
    last_ms = store.load("cdc_last_commit_ms")
    if last_ms is None:
        return run_day0_then_subscribe()                                     # Example 1
    last = datetime.fromtimestamp(last_ms / 1000, tz=timezone.utc)
    if datetime.now(timezone.utc) - last > RETENTION:
        return run_full_resync_then_subscribe()                              # outside retention
    pubsub.subscribe(topic="/data/ChangeEvents", replay_preset="CUSTOM",
                     replay_id=store.load_bytes("cdc_replay_id"), handler=process_event)
```

**Why it works:** The decision is based on elapsed time against the 3-day retention, which Salesforce documents, instead of an error the client library may or may not raise. After 4 hours the stored replay ID resumes the stream; after 4 days the pipeline re-syncs first.

---

## Anti-Pattern: Treating GAP_OVERFLOW Like Other Gap Events

**What practitioners do:** One branch handles every `changeType` starting with `GAP_` by looking up `recordIds`.

**What goes wrong:** An overflow event's only record ID is `000000000000000AAA`. The lookup returns nothing and the changes after the first 100,000 in that transaction never reach the replica.

**Correct approach:** Test for `GAP_OVERFLOW` first and re-sync the entity named in `entityName`, starting from the overflow event's replay ID; handle the other four `GAP_` types with the dirty-flag procedure.
