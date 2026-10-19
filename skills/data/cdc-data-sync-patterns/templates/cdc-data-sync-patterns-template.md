# CDC Data Sync Patterns — Replication Design Template

Use this template when designing or reviewing a CDC-based data replication pipeline. Fill in each section before implementation begins.

---

## Scope

**Skill:** `cdc-data-sync-patterns`

**Request summary:** (describe what the requester needs — new pipeline, reconnect recovery, gap event fix, etc.)

**Objects to replicate:**

| Object API Name | Approximate Record Count | CDC Channel |
|---|---|---|
|  |  |  |
|  |  |  |

---

## Subscriber State Assessment

Answer these before choosing a replication strategy:

- **Is this a new pipeline or a reconnect?**
  - [ ] New pipeline — day-0 Bulk API load required
  - [ ] Reconnect within 3 days of the last processed event — resume with the stored replay ID (CUSTOM)
  - [ ] Last processed event more than 3 days old — full Bulk API re-sync required

- **Is a stored replayId available?** Yes / No
  - If yes: confirm the last processed commitTimestamp is within 3 days before using it.
  - If no: run the day-0 load from a saved handoff position (Pub/Sub LATEST / CometD -1).

- **Time the subscriber was offline (if reconnecting):** _______

---

## Day-0 Load Design (Complete Only for New Pipelines)

| Step | Action | Status |
|---|---|---|
| 1 | Subscribe with LATEST and save the replay_id from the first keepalive or event as the handoff, before starting the Bulk API job | [ ] |
| 2 | Create Bulk API 2.0 query job for each target object | [ ] |
| 3 | Download and load results into external datastore | [ ] |
| 4 | Confirm record count matches Salesforce object count | [ ] |
| 5 | Subscribe to CDC using the recorded tip replayId | [ ] |

**Tip replayId recorded at:** _______  (record before Bulk API job starts)

**Bulk API job IDs:**

| Object | Job ID | Status |
|---|---|---|
|  |  |  |

---

## ReplayId Persistence Design

- **Storage location:** (e.g., PostgreSQL table `cdc_checkpoints`, Redis key, flat file)
- **Write timing:** After each successfully committed event batch (not on shutdown only)
- **Write semantics:** Transactional with event data write (both succeed or both fail)
- **Read on reconnect:** Read stored replayId → validate → subscribe

**Persistence implementation notes:**

(describe the specific storage mechanism and write path)

---

## Gap Event Handling Design

- **Detection:** Check `ChangeEventHeader.changeType` for `GAP_` prefix before any field processing.
- **Fallback query:** REST API SOQL query using `recordIds` from `ChangeEventHeader`.
- **Staleness guard:** Use `commitTimestamp` from the gap event header to avoid overwriting newer non-gap data.
- **Batching:** Batch multiple `recordIds` from consecutive gap events into a single SOQL query where possible.

**Gap event handler location:** (file/class/function path)

**Expected gap and overflow sources:** (events over 1 MB, custom field type conversions, database-level jobs such as activity archiving, transactions over 100,000 changes such as large cascade deletes)

---

## Event Ordering and Deduplication Design

- **Intra-transaction ordering:** Sort by `sequenceNumber` within the same `transactionKey`.
- **Inter-transaction ordering:** Sort by `commitTimestamp` across different `transactionKey` values.
- **Idempotency key:** `transactionKey` + `sequenceNumber` (unique per change within a transaction).

**Idempotency implementation:** (describe how duplicate events are detected and safely skipped)

---

## Recovery Decision Tree

```
Subscriber connects
        |
        v
Is a stored replay ID available?
    NO ──> Save a handoff position (LATEST / -1, first keepalive or event)
           → day-0 Bulk API extract → resubscribe from the handoff (CUSTOM)
    YES
        |
        v
Is the last processed commitTimestamp within 3 days?
        |
        |── YES ──> Subscribe with the stored replay ID (CUSTOM)
        |
        └── NO ───> Full Bulk API re-sync of the replicated objects
                    → subscribe (EARLIEST, or a fresh handoff position)
                    → save the replay ID after the first committed transaction
```

---

## Review Checklist

Before marking the replication pipeline implementation complete:

- [ ] Day-0 Bulk API load is implemented and tested (new pipelines only).
- [ ] Tip replayId is recorded before the Bulk API load starts.
- [ ] replayId is persisted to durable external storage after every committed batch.
- [ ] Reconnect logic reads the stored replayId and passes it to the subscription call.
- [ ] A last processed commitTimestamp older than 3 days routes to a Bulk API re-sync (do not rely on a specific error).
- [ ] GAP_OVERFLOW triggers a per-entity re-sync; the four GAP_ record types use mark-dirty-and-retrieve.
- [ ] All events are checked for GAP_ prefix in changeType before field processing.
- [ ] Gap event fallback queries REST API using recordIds from ChangeEventHeader.
- [ ] commitTimestamp is used as a staleness guard in gap event upserts.
- [ ] Events within a transaction are applied in sequenceNumber order.
- [ ] transactionKey + sequenceNumber is used as the idempotency key.
- [ ] Recovery scenario (more than 3 days offline) has been tested or documented with a runbook.

---

## Notes and Deviations

(Record any decisions that deviate from the standard patterns in SKILL.md and explain why.)
