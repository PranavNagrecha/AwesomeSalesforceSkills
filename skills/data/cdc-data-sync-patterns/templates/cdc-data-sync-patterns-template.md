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
  - [ ] Reconnect after < 72-hour outage — use stored replayId
  - [ ] Reconnect after > 72-hour outage — full Bulk API re-sync required

- **Is a stored replayId available?** Yes / No
  - If yes: confirm it is within the 72-hour retention window before using it.
  - If no: determine which of -1 (tip) or -2 (full catch-up) is appropriate.

- **Time the subscriber was offline (if reconnecting):** _______

---

## Day-0 Load Design (Complete Only for New Pipelines)

| Step | Action | Status |
|---|---|---|
| 1 | Record tip replayId from Pub/Sub API GetTopic before starting Bulk API job | [ ] |
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

**Estimated gap event frequency:** (estimate based on Bulk API usage patterns in the org)

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
Is stored replayId available?
    NO ──────────────────────────────> Is this a new pipeline?
                                            YES → Run day-0 Bulk API load,
                                                  then subscribe at tip (-1)
                                            NO  → Subscribe at -2 (full catch-up)
                                                  or tip (-1) as appropriate
    YES
        |
        v
Validate replayId against retention window
        |
        |── VALID (within 72 hours) ──> Subscribe with stored replayId
        |
        └── EXPIRED (> 72 hours) ────> Full Bulk API re-sync
                                       → Subscribe at tip (-1)
                                       → Persist new replayId on first event
```

---

## Review Checklist

Before marking the replication pipeline implementation complete:

- [ ] Day-0 Bulk API load is implemented and tested (new pipelines only).
- [ ] Tip replayId is recorded before the Bulk API load starts.
- [ ] replayId is persisted to durable external storage after every committed batch.
- [ ] Reconnect logic reads the stored replayId and passes it to the subscription call.
- [ ] Replay-expired error is handled explicitly and routes to Bulk API re-sync.
- [ ] All events are checked for GAP_ prefix in changeType before field processing.
- [ ] Gap event fallback queries REST API using recordIds from ChangeEventHeader.
- [ ] commitTimestamp is used as a staleness guard in gap event upserts.
- [ ] Events within a transaction are applied in sequenceNumber order.
- [ ] transactionKey + sequenceNumber is used as the idempotency key.
- [ ] Recovery scenario (> 72 hours offline) has been tested or documented with a runbook.

---

## Notes and Deviations

(Record any decisions that deviate from the standard patterns in SKILL.md and explain why.)
