# Examples — CDC Data Sync Patterns

## Example 1: Day-0 Full Load Followed by Incremental CDC

**Context:** A data engineering team is building a near-real-time replication pipeline to sync Salesforce Account and Opportunity records into a data warehouse. The objects have millions of existing records. CDC only publishes events for changes that occur after the subscription is established — it does not backfill pre-existing records.

**Problem:** If the team subscribes to CDC first and then runs the initial load, they miss all events published during the load window. If they run the load first and then subscribe at tip (`-1`), they miss events published during the load.

**Solution:**

```python
# Step 1: Record the current tip replayId BEFORE starting the Bulk API load.
# Use Pub/Sub API GetTopic to fetch the latest replayId for the topic.
tip_replay_id = pub_sub_client.get_topic("/data/AccountChangeEvent").latest_replay_id

# Step 2: Execute Bulk API 2.0 query job to extract all existing Account records.
job_id = bulk_api.create_query_job(
    object="Account",
    query="SELECT Id, Name, BillingCity, LastModifiedDate FROM Account"
)
bulk_api.wait_for_job(job_id)
records = bulk_api.get_results(job_id)
warehouse.upsert("account_dim", records, key="Id")

# Step 3: Subscribe to CDC starting at the recorded tip replayId.
# Any events published between step 1 and step 3 are captured.
cdc_subscriber.subscribe(
    topic="/data/AccountChangeEvent",
    replay_id=tip_replay_id
)
```

**Why it works:** Recording the tip `replayId` before the Bulk API load creates a safe handoff point. Events published while the Bulk API job was running are captured when CDC subscription resumes from that position. The warehouse ends up with a consistent view that combines the full initial load with all incremental changes.

---

## Example 2: Gap Event Detection and REST Fallback

**Context:** A CDC pipeline processes Account record changes and writes deltas to a downstream CRM. The pipeline encounters a `GAP_UPDATE` event after a large batch update ran directly via the Bulk API in Salesforce, which bypassed the application server and triggered a gap event instead of a full change event.

**Problem:** The gap event has `changeType = GAP_UPDATE` and a `recordIds` list in the header but no field values in the event body. Processing the event body as a normal update writes null or empty values to the downstream CRM, corrupting the record.

**Solution:**

```python
def process_cdc_event(event):
    header = event["ChangeEventHeader"]
    change_type = header["changeType"]

    # Always check for GAP_ prefix before touching any field data.
    if change_type.startswith("GAP_"):
        handle_gap_event(header)
        return

    # Safe to process field data for non-gap events.
    apply_delta_to_datastore(event)


def handle_gap_event(header):
    record_ids = header["recordIds"]
    commit_timestamp = header["commitTimestamp"]

    # Query current record state from REST API using the record IDs.
    for record_id in record_ids:
        current_record = rest_api.query_one(
            f"SELECT Id, Name, BillingCity, LastModifiedDate "
            f"FROM Account WHERE Id = '{record_id}'"
        )
        if current_record:
            # Guard: only overwrite if the REST response is newer than
            # what we last applied, using commitTimestamp as the fence.
            datastore.upsert_if_newer(
                record=current_record,
                fence_timestamp=commit_timestamp
            )
```

**Why it works:** The `GAP_` prefix check is the gate that prevents field-less gap events from being processed as normal events. The REST fallback query retrieves the authoritative current state directly from Salesforce. The `commitTimestamp` guard prevents the gap recovery from overwriting a more recent non-gap event that was already applied.

---

## Example 3: ReplayId Persistence and Reconnect Recovery

**Context:** A CDC subscriber service restarts after a 4-hour infrastructure outage. It needs to resume processing from exactly where it stopped without replaying the entire 72-hour event window.

**Problem:** Without external `replayId` persistence, the subscriber has no record of its last position. Using `-2` (full catch-up) replays up to 72 hours of events for a large org — potentially millions of events — causing excessive processing time and downstream load.

**Solution:**

```python
REPLAY_ID_KEY = "cdc_account_replay_id"

def on_event_batch_committed(events):
    """Called after a batch of events is successfully written to the datastore."""
    last_replay_id = events[-1]["replayId"]
    # Persist to durable external storage (Redis, database, etc.).
    store.set(REPLAY_ID_KEY, last_replay_id)


def get_subscription_replay_id():
    """Determine the replayId to use when (re)connecting."""
    stored_id = store.get(REPLAY_ID_KEY)

    if stored_id is None:
        # First-ever connection: no stored position.
        # For a new pipeline after day-0 load, use -1 (tip).
        return -1

    # Verify the stored replayId is still within the retention window.
    try:
        pub_sub_client.validate_replay_id(stored_id)
        return stored_id
    except ReplayIdExpiredError:
        # Stored replayId is outside the 72-hour window.
        # Signal that a full Bulk API re-sync is required.
        raise BulkReSyncRequired(
            f"Stored replayId {stored_id} is outside the 72-hour retention window. "
            "A full Bulk API re-sync is required before resuming CDC."
        )
```

**Why it works:** Persisting the `replayId` after each committed batch provides a durable checkpoint. Validating the stored ID on reconnect catches the expired-window case explicitly and routes to the Bulk API re-sync path rather than silently starting at tip and producing a data gap.

---

## Anti-Pattern: Processing GAP_ Events as Normal Change Events

**What practitioners do:** Subscribe to CDC events and process all events in a single path without checking `changeType` for the `GAP_` prefix. The code reads field values from the event body regardless of event type.

**What goes wrong:** Gap events have no field data in their body. Processing them as normal events writes empty or null field values to the external datastore. Because there is no error thrown — the field is simply absent — this produces silent data drift that can take days or weeks to detect.

**Correct approach:** Always branch on `changeType` before touching any field data. If `changeType.startswith("GAP_")`, skip field processing entirely and execute the REST API fallback query using `recordIds` from `ChangeEventHeader`.
