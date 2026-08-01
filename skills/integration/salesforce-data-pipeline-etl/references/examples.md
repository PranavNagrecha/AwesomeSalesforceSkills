# Examples — Salesforce Data Pipeline / ETL

## Example 1: Snapshot plus delta into a warehouse

**Context:** finance analytics needs Account, Opportunity and OpportunityLineItem in the
warehouse with under an hour of lag. The existing nightly job pages SOQL on
`LastModifiedDate`.

**Problem:** three defects, in increasing order of how long they take to notice.

1. `LastModifiedDate` is user-settable when Set Audit Fields is enabled, so the watermark
   does not reliably advance.
2. The window is open-ended and advances to the maximum timestamp observed, so a record
   committed during the query is skipped permanently.
3. Deletions never appear at all, because a deleted record stops being returned rather
   than being returned with a new timestamp. The warehouse had been accumulating dead
   Opportunities for two years.

**Solution — take the decision-tree branch explicitly.**
`standards/decision-trees/integration-pattern-selection.md` splits on record volume
against freshness: high volume with a historical baseline goes to Bulk API 2.0, and
sub-hour freshness on an ongoing delta goes to a streaming subscription. This requirement
sits on both branches, so the answer is both mechanisms with a defined handover.

**Phase 1 — baseline via a Bulk API 2.0 query job:**

```bash
curl -s -X POST "$SF_INSTANCE/services/data/v64.0/jobs/query" \
  -H "Authorization: Bearer $SF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
        "operation": "queryAll",
        "query": "SELECT Id, AccountId, Amount, StageName, CloseDate, IsDeleted, SystemModstamp FROM Opportunity"
      }'
```

`queryAll` rather than `query` is deliberate: it returns soft-deleted rows with
`IsDeleted = true`, so the baseline starts with tombstones already represented instead of
silently omitting them. Record the job's completion time — that timestamp is the handover
point for phase 2.

**Phase 2 — delta via a durable subscription:**

```python
def handle(event):
    header = event["ChangeEventHeader"]
    change_type = header["changeType"]          # CREATE | UPDATE | DELETE | UNDELETE | gap types

    if change_type in ("CREATE", "UPDATE"):
        warehouse.merge_on_id(header["recordIds"], event)
    elif change_type == "DELETE":
        warehouse.tombstone(header["recordIds"])
    elif change_type == "UNDELETE":
        warehouse.untombstone(header["recordIds"])
    elif change_type.startswith("GAP"):
        # The platform is saying it could not produce a full payload. Dropping this
        # converts a recoverable signal into permanent, unannounced divergence.
        metrics.increment("cdc.gap", tags={"entity": header["entityName"]})
        warehouse.requeue_for_requery(header["recordIds"])
    else:
        # Never default to ignore. An unrecognised type is a new platform behaviour.
        raise UnknownChangeType(change_type)

    # Checkpoint AFTER the work succeeded, never on receipt.
    checkpoint_store.put(header["entityName"], event["replayId"])
```

**Why it works:** the baseline establishes every row including tombstones, and the
subscription carries deletes as first-class events, which is the defect a watermark
design cannot fix at any level of effort. Checkpointing the replay id after processing
rather than on receipt means a crash mid-batch replays that batch rather than skipping it,
and the merge is idempotent on Id so replay is safe. Raising on an unknown change type is
the opposite of the usual instinct and is correct here: a silent `else: pass` is precisely
how gap events get discarded.

---

## Example 2: Recovering when replay is no longer possible

**Context:** the subscriber was down over a long holiday weekend. On restart the broker
rejects the stored replay id.

**Problem:** the event bus retains change events for a bounded window — confirm the
current figure in the Change Data Capture Developer Guide, as it has changed across
releases. Past that point the events are gone, and a rejected replay id is not a transient
error to retry. Generated handlers treat it as one, and the pipeline sits in a retry loop
diverging further with every hour.

**Solution:** classify the rejection and escalate to a re-snapshot automatically.

```python
MAX_GAP_RATE = 0.001          # gap events per received event, over a rolling hour

def start_subscriber(entity):
    replay_id = checkpoint_store.get(entity)
    try:
        subscribe(entity, replay_id=replay_id)
    except ReplayIdTooOld:
        # Not retryable: the window has passed. Re-snapshot is the only correct path.
        alert.page("cdc_replay_expired", entity=entity, replay_id=replay_id)
        run_bulk_snapshot(entity)                  # queryAll, as in Example 1
        checkpoint_store.put(entity, LATEST)       # resume from the live edge
        subscribe(entity, replay_id=LATEST)
```

**And the check that finds the failures nobody signalled:**

```sql
-- Reconciliation. Cheap enough to run hourly; bucket by created date so a
-- divergence is localised to a period rather than reported as one number.
SELECT bucket, source_count, warehouse_count, source_count - warehouse_count AS drift
FROM (
  SELECT DATE_TRUNC('day', created_date) AS bucket, COUNT(*) AS warehouse_count
  FROM wh.opportunity WHERE is_deleted = FALSE GROUP BY 1
) w
FULL OUTER JOIN sf_counts s USING (bucket)
WHERE ABS(COALESCE(source_count,0) - COALESCE(warehouse_count,0)) > 0
ORDER BY bucket DESC
```

**Why it works:** the two failure modes need opposite responses and both look like errors.
An expired replay id is unrecoverable by retry and recoverable by re-snapshot, so
automating that escalation converts a multi-day silent divergence into a few minutes of
extra load. The reconciliation query catches the class of failure that raises no error at
all — a run that succeeded while dropping rows — which is why it alerts on drift rather
than on job status. Bucketing by created date localises the damage: a single number tells
you something is wrong, a bucketed one tells you when it started.
