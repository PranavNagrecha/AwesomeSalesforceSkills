# LLM Anti-Patterns — Salesforce Data Pipeline / ETL

Scope: extracting Salesforce data into a warehouse or lakehouse and keeping it correct
over time. The choice between extraction mechanisms is governed by
`standards/decision-trees/integration-pattern-selection.md` — cite the branch you took.
Warehouse-side modelling belongs to `data/etl-vs-api-data-patterns`; zero-copy federation
belongs to `integration/data-cloud-zero-copy-federation`.

## Anti-Pattern 1: A watermark on LastModifiedDate

The default incremental design an assistant produces, and it loses records. Two distinct
defects hide in it.

`LastModifiedDate` is user-settable under "Set Audit Fields", so it does not reliably
advance. `SystemModstamp` is maintained by the platform and is the correct watermark
field. That is the easy half.

The harder half is the window. A record modified while the extract query is running can
carry a timestamp inside the window you just read and still not appear in the result. If
the next run starts from `max(timestamp seen)`, that record is skipped permanently, and
nothing downstream ever signals it.

**Wrong** — user-settable field, and a window boundary that silently drops rows:

```sql
SELECT Id, Name, LastModifiedDate
FROM Account
WHERE LastModifiedDate > 2026-07-30T02:00:00Z
```

**Right** — platform-maintained field, closed window, and a deliberate overlap so the
boundary is re-read rather than trusted:

```sql
SELECT Id, Name, SystemModstamp
FROM Account
WHERE SystemModstamp >= 2026-07-30T01:55:00Z
  AND SystemModstamp <  2026-07-30T02:55:00Z
ORDER BY SystemModstamp
```

Advance the watermark to the window's upper bound, not to the maximum timestamp observed,
and overlap successive windows by more than your longest expected transaction. The
overlap produces duplicates, which is why the warehouse merge must be idempotent on Id —
duplicates are cheap to absorb and missing rows are not.

Source: SystemModstamp and audit fields —
https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/system_fields.htm

## Anti-Pattern 2: A watermark cannot see deletes

The most damaging silent defect in this domain. A deleted record stops appearing in query
results; it does not appear with a new timestamp. So a watermark pipeline never learns
about deletions, and the warehouse accumulates rows that no longer exist — indefinitely,
and with no error anywhere.

❌ Incremental extract on `SystemModstamp` and nothing else.
✅ Either move to Change Data Capture, which emits delete and undelete events explicitly,
or run a second pass over the Recycle Bin using `queryAll` with `IsDeleted = true` and
apply tombstones. The `queryAll` path only catches deletions still within the retention
window, so it must run at least as often as that window is long — and it misses hard
deletes entirely, which is the argument for CDC.

## Anti-Pattern 3: Expecting formula and roll-up fields to move the watermark

Assistants extract formula fields incrementally alongside stored fields. A formula is
evaluated at read time and stores nothing, so when its inputs change on a *related*
record, the formula's own record does not get a new `SystemModstamp`. The warehouse keeps
the stale computed value with no signal that it drifted.

❌ Include `Account.Total_Open_Opportunities__c` in an incremental extract and treat it as
current.
✅ Extract the inputs and compute in the warehouse, where the dependency is explicit and
recomputable. If a formula must be extracted, it needs a full refresh on its own schedule,
and that schedule is a correctness requirement rather than an optimisation. The same
applies to roll-up summary fields, which do update the parent's `SystemModstamp` when they
recalculate — but not on every path that changes the underlying children.

## Anti-Pattern 4: Ignoring gap and overflow events

CDC delivers ordinary change events and also emits gap events when the platform cannot
produce a full change payload — for example under heavy load or for certain bulk
operations. Generated subscribers switch on `CREATE`, `UPDATE`, `DELETE`, `UNDELETE` and
drop everything else. The gap event was the platform telling you it could not tell you,
and discarding it converts a recoverable signal into permanent divergence.

❌ `if (changeType === 'UPDATE') { ... } // else ignore`
✅ Treat any gap or overflow change type as an instruction to re-query the affected record
Ids and reconcile. Alert on it too — a rising gap rate is a real signal about org load.
Assume nothing about which types exist; enumerate them from the current Change Data
Capture Developer Guide and fail loudly on an unrecognised value rather than defaulting to
ignore.

## Anti-Pattern 5: Holding the replay id in memory

The subscriber restarts, resumes from the latest available position, and everything
between the last processed event and the restart is gone. The event bus retains change
events for a bounded window — check the current figure in the Change Data Capture
Developer Guide, as it has changed across releases — so an outage longer than that window
cannot be recovered by replay at all.

❌ `let replayId = -1;` reset on every process start.
✅ Persist the replay id durably after each successfully *processed* batch, never on
receipt. On restart, resume from the stored value. If the stored replay id is older than
the retention window the broker will reject it — treat that rejection as the trigger for
an automatic full re-snapshot rather than as a fatal error, because it is the one case
where replay genuinely cannot help.

## Anti-Pattern 6: Polling SOQL where the volume path belongs

Asked to "sync 40 million rows nightly", assistants generate a paged SOQL loop. It
consumes the org's API allocation, competes with every other integration, and is
dramatically slower than the API designed for the job.

❌ Paged REST query loops for the initial load or a full refresh.
✅ Bulk API 2.0 query jobs for volume extraction, and a streaming subscription for the
delta. Take the branch in
`standards/decision-trees/integration-pattern-selection.md` explicitly: the axis is record
volume against freshness requirement, and the answer for "bulk historical load plus
near-real-time delta" is both mechanisms, not one of them.

## Anti-Pattern 7: A pipeline with no divergence check

Snapshot plus delta is correct in theory and drifts in practice — a missed gap event, a
schema change, a silently failed run. Without an independent check, the first person to
notice is an analyst who does not trust the number, which is far too late.

❌ Trust the pipeline because it reports success.
✅ Reconcile on a schedule that is cheap enough to run often: compare record counts per
object per created-date bucket between source and warehouse, and checksum a sampled key
set. Alert on divergence rather than on job failure. A job that fails is visible; a job
that succeeds while dropping rows is what this check exists to find.
