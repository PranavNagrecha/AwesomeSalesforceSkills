# Worked Example — One Stream Through the Transaction Buffer, a Gap, and an Overflow

A subscriber replicates Account, Contact, and Opportunity from `/data/ChangeEvents` into a warehouse. Below is the order in which events arrive, and what the subscriber does with each. Replay IDs are shown as short labels; real ones are opaque bytes.

| # | Replay | changeType | Entity | transactionKey | seq | recordIds | Subscriber action |
|---|---|---|---|---|---|---|---|
| 1 | r1 | CREATE | Account | T1 | 1 | 001A | Buffer under T1 |
| 2 | r2 | CREATE | Contact | T1 | 2 | 003A | Buffer under T1 |
| 3 | r3 | CREATE | Opportunity | T1 | 3 | 006A | Buffer under T1 |
| 4 | r4 | UPDATE | Account | T2 | 2 | 001B, 001C | New key: commit T1 (3 rows), save r3. Buffer T2 (seq starts at 2 because the object changed at seq 1 isn't CDC-enabled; that gap is normal) |
| 5 | r5 | GAP_UPDATE | Account | T3 | 1 | 001D | New key: commit T2 (update both 001B and 001C), save r4. Mark 001D dirty as of its commitTimestamp; queue retrieval |
| 6 | r6 | UPDATE | Account | T4 | 1 | 001D | 001D is dirty and this change is after the gap: skip it |
| 7 | — | — | — | — | — | — | Reconciler retrieves 001D through the REST API, upserts it, clears the flag. Its `LastModifiedDate` is after event 6's change, so nothing is lost |
| 8 | r8 | DELETE | Contact | T5 | 1 | 003B…(100,000 changes in T5) | Buffer under T5 |
| 9 | r9 | GAP_OVERFLOW | Opportunity | T5 | … | 000000000000000AAA | Stop. Save r9. Re-sync Opportunity (all records, then deletes). Resubscribe from r9 |

## Why each step is right

- **Events 1–4.** The CDC guide recommends replicating each transaction as a single commit, buffering by `transactionKey` and committing when the key changes. A lead conversion is the guide's example of one transaction producing several changes in sequence.
- **Event 4's two IDs.** Identical changes to several records of one object in one transaction within one second are merged into one event; every ID in `recordIds` gets the update.
- **Events 5–7.** Gap events carry the record ID but no data. The guide's procedure is: mark the record dirty as of the gap, ignore new change events for it until reconciled (compare `commitTimestamp`, and `LastModifiedDate` on the retrieved record), retrieve it, then clear the flag.
- **Events 8–9.** When one transaction passes 100,000 changes, the rest produce one overflow event per entity type. The overflow event has only a dummy record ID, so the subscriber re-syncs the entity and then resumes after the saved replay ID to catch changes made during the re-sync.

## Position bookkeeping

| After | Saved replay ID | Saved last `commitTimestamp` |
|---|---|---|
| Commit of T1 | r3 | T1's |
| Commit of T2 | r4 | T2's |
| Overflow re-sync start | r9 | T5's |
| Keepalive with no events | the keepalive `replay_id` | unchanged |

If the subscriber is restarted, it resumes with `CUSTOM` and the saved replay ID, unless the saved `commitTimestamp` is more than 3 days old, in which case it re-syncs first.
