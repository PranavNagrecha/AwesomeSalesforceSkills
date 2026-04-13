# LLM Anti-Patterns — CDC Data Sync Patterns

Common mistakes AI coding assistants make when generating or advising on CDC data replication pipelines. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Ignoring the GAP_ Prefix and Processing Gap Events as Normal Change Events

**What the LLM generates:** A CDC event handler that reads field values from every event without checking `changeType` first. The generated code does something like `record.Name = event.payload.Name` unconditionally, or uses a generic `apply_event(event)` function with no gap event branch.

**Why it happens:** Most CDC tutorial examples show happy-path normal events. Gap events are underrepresented in training data and documentation examples. LLMs generalize from the normal-event pattern and omit the exception path.

**Correct pattern:**

```python
change_type = event["ChangeEventHeader"]["changeType"]
if change_type.startswith("GAP_"):
    # No field data available. Fall back to REST API query.
    record_ids = event["ChangeEventHeader"]["recordIds"]
    current_records = rest_api.query_by_ids(object_name, record_ids)
    datastore.upsert(current_records)
else:
    # Safe to process field data from the event body.
    apply_delta(event)
```

**Detection hint:** Search generated code for CDC event processing logic that lacks any reference to `GAP_`, `startswith("GAP_")`, or equivalent gap-event check. Any CDC handler that processes `changeType` values without a `GAP_` branch is incomplete.

---

## Anti-Pattern 2: Assuming Salesforce Tracks Subscriber Position (Not Implementing External replayId Persistence)

**What the LLM generates:** Code that subscribes to CDC with `-2` (full catch-up) on every connection, or code that subscribes at `-1` (tip) on every restart, with no mechanism to store or retrieve a `replayId` between sessions. Sometimes the LLM generates code that reads `replayId` from the event but never writes it to durable storage.

**Why it happens:** LLMs trained on general event streaming concepts (Kafka, RabbitMQ) may assume the broker tracks consumer offsets. Salesforce's Pub/Sub API and CometD do not — the subscriber owns its position entirely.

**Correct pattern:**

```python
# On startup: read stored replayId from durable storage.
replay_id = persistent_store.get("last_replay_id") or -1

subscriber.connect(topic=TOPIC, replay_id=replay_id)

# After each successfully committed batch: persist the new replayId.
def on_batch_committed(events):
    last_id = events[-1]["replayId"]
    persistent_store.set("last_replay_id", last_id)
```

**Detection hint:** Search for CDC subscriber code that does not include a read from and write to an external store for `replayId` (or `replay_id`). Any CDC subscription call that always passes `-1` or `-2` as a literal constant is missing durable position tracking.

---

## Anti-Pattern 3: Not Handling the >72-Hour Offline Scenario — Assuming Replay Is Always Possible

**What the LLM generates:** Reconnection logic that always resumes from the stored `replayId` with no check for whether that ID is still within the retention window. The code catches the replay-expired error and either swallows it silently or crashes the subscriber, with no fallback to a Bulk API re-sync.

**Why it happens:** The 72-hour retention limit is a Salesforce-specific constraint. General event streaming systems often have configurable or very long retention windows. LLMs that do not specifically know this limit assume replay is always available from any stored position.

**Correct pattern:**

```python
try:
    subscriber.connect(topic=TOPIC, replay_id=stored_replay_id)
except ReplayIdExpiredError:
    logger.warning(
        "Stored replayId is outside the 72-hour retention window. "
        "Initiating full Bulk API re-sync before resuming CDC."
    )
    run_bulk_api_resync(affected_objects)
    subscriber.connect(topic=TOPIC, replay_id=-1)
```

**Detection hint:** Search CDC reconnection code for handling of replay-expired errors (Pub/Sub API error code, Streaming API `400` invalid replayId, etc.). Code that does not have this error branch is missing the recovery path for long outages.

---

## Anti-Pattern 4: Using Timestamps Instead of transactionKey + sequenceNumber for Event Ordering

**What the LLM generates:** Event ordering logic that sorts CDC events by `commitTimestamp` alone, or by the time the event was received at the subscriber. The generated code applies events in timestamp order without considering that multiple events in the same transaction share the same `commitTimestamp`.

**Why it happens:** Timestamp-based ordering is the default mental model for event sequencing. The `transactionKey` + `sequenceNumber` combination is specific to Salesforce CDC and is not present in most general-purpose event streaming systems.

**Correct pattern:**

```python
# Group events by transactionKey, then sort by sequenceNumber within each group.
from itertools import groupby

events_sorted = sorted(events, key=lambda e: (
    e["ChangeEventHeader"]["commitTimestamp"],
    e["ChangeEventHeader"]["transactionKey"],
    e["ChangeEventHeader"]["sequenceNumber"]
))

for (ts, tx_key), group in groupby(events_sorted, key=lambda e: (
    e["ChangeEventHeader"]["commitTimestamp"],
    e["ChangeEventHeader"]["transactionKey"]
)):
    for event in group:
        apply_delta(event)
```

**Detection hint:** Search ordering logic for use of `transactionKey` and `sequenceNumber`. Code that sorts by `commitTimestamp` or event arrival time alone, without referencing `sequenceNumber`, is applying the wrong ordering key for intra-transaction events.

---

## Anti-Pattern 5: Conflating CDC Admin Setup with Replication Lifecycle Patterns

**What the LLM generates:** Advice that mixes entity selection, channel configuration, and edition limits (admin concerns) with replay ID management, gap event handling, and day-0 load design (replication lifecycle concerns). For example: generating code that "enables CDC" and then immediately subscribes, without acknowledging that day-0 load and replay strategy are separate lifecycle steps.

**Why it happens:** Most CDC documentation and examples treat setup and subscription as a single integrated flow. LLMs absorb this framing and conflate the two concerns, leading to incomplete implementations that skip the replication lifecycle steps.

**Correct pattern:** Treat CDC setup (admin) and CDC replication lifecycle (data engineering) as distinct concerns handled by different skills and different implementation phases. Admin questions about entity selection, channels, and limits → `integration/change-data-capture-integration`. Replication lifecycle questions about day-0 load, replay, gap events, ordering → this skill (`data/cdc-data-sync-patterns`).

**Detection hint:** Generated guidance that includes both "go to Setup > Change Data Capture" and "subscribe with replayId = -2" in the same code flow without a day-0 Bulk API load step is conflating setup and replication lifecycle.

---

## Anti-Pattern 6: Not Implementing REST Fallback for GAP Events — Silently Missing Field Data

**What the LLM generates:** GAP event detection code that logs the event and skips it without querying current record state. The code correctly identifies the gap event but takes no action to retrieve the data that the gap event was supposed to convey.

**Why it happens:** LLMs may recognize that gap events are "special" and generate a skip/ignore branch, without understanding that the gap event represents a real data change that must be recovered via REST API. The logging-and-skipping pattern feels like correct error handling.

**Correct pattern:**

```python
if change_type.startswith("GAP_"):
    # Do NOT simply log and skip. The gap represents a real change.
    # Query current record state from REST API.
    record_ids = header["recordIds"]
    records = rest_api.query(
        f"SELECT Id, Name, ... FROM Account WHERE Id IN {record_ids}"
    )
    datastore.upsert(records)
    # Do not return here without updating the datastore.
```

**Detection hint:** Search gap event handling code for REST API calls (`query`, `GET /services/data`, SOQL) following the GAP detection branch. Code that has a `if GAP_` branch containing only `logger.info(...)` or `continue` (without a subsequent REST query) is silently dropping data changes.
