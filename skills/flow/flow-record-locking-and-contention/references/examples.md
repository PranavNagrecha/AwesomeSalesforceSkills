# Examples — Flow Record Locking And Contention

These examples walk a real production scenario from contention failure through to a refactored, decoupled design. The setup is a B2B sales org where Opportunities update frequently and a record-triggered flow on `Opportunity` updates `Account.LastActivityDate` after every save.

---

## Example 1: The Failing Flow — Synchronous Account Update From Opportunity After-Save

**Context:** A national-retailer Account (`001ABC`) has 8,000 Opportunities. Sales reps and integration users write to those Opportunities at a sustained rate of ~5 transactions/sec during business hours. A record-triggered after-save flow on Opportunity does the following:

```
Trigger: Opportunity (after-save, Updated)
        │
        ▼
[Decision: Stage changed?]
        │
        ├── Yes
        │     │
        │     ▼
        │   [Update Records: Opportunity — set Stage_Last_Changed__c = NOW()]
        │     │
        │     ▼
        │   [Get Records: Account WHERE Id = $Record.AccountId]
        │     │
        │     ▼
        │   [Update Records: Account — set LastActivityDate = TODAY(),
        │                     Pipeline_Recalc_Needed__c = true]
        │     │
        │     ▼
        │   [End]
        │
        └── No → [End]
```

**Problem:** Under load, the flow surfaces `UNABLE_TO_LOCK_ROW: unable to obtain exclusive access to this record or 1 records: 001ABC` in roughly 8% of executions. Fault emails arrive in waves, especially during stage-rollover hours when reps update Opportunities en masse.

The lock chain per execution:

1. `Update Opportunity` takes a write lock on the Opportunity row AND on the parent Account row (`001ABC`) AND on the Account's owner User row. Held for the full transaction.
2. `Get Account` does NOT take a lock (Get Records is read-only).
3. `Update Account` already had the Account locked from step 1, so this DML is "free" — but the lock continues to be held until commit.

With 5 concurrent transactions all touching `001ABC`, the second-through-fifth are queued waiting for the first transaction's Account lock. After ~10 seconds, Salesforce fires the 10-retry exponential backoff. After the 10th retry, the fault surfaces. Sometimes 10 retries is enough to slot in; sometimes not. The flow's automatic rollback then discards both the Opportunity update AND the Account update — net data loss.

**Why the legacy Process Builder hid this:** The previous Process Builder serialized via the legacy automation engine, so even on hot Accounts, transactions would queue but rarely surface UNABLE_TO_LOCK_ROW because the parent lock was held for milliseconds, not the full flow duration. Migrating to Flow exposed the latent contention.

**Solution (intermediate fix — collect-then-update for any bulk path):**

If the flow is also invoked from a bulk source (List View mass-edit, Data Loader), the loop-update shape is the first thing to fix:

```
[Trigger: Opportunity (after-save, Updated, bulk-safe)]
        │
        ▼
[Decision: Stage changed (per record)?]
        │
        ├── Yes — assignment: changedOpps.add($Record)
        │
        ▼
[After all records — Loop over changedOpps]
        │
        ├── [Assignment: opp.Stage_Last_Changed__c = NOW()]
        ├── [Assignment: oppCollectionToUpdate.add(opp)]
        │
        ▼
[After Loop — Update Records: oppCollectionToUpdate]   ← single bulk Update
        │
        ▼
[Get Records: Accounts WHERE Id IN :affectedAccountIds]
        │
        ▼
[Loop over affected Accounts]
        │
        ├── [Assignment: acct.LastActivityDate = TODAY()]
        ├── [Assignment: acct.Pipeline_Recalc_Needed__c = true]
        ├── [Assignment: acctCollectionToUpdate.add(acct)]
        │
        ▼
[After Loop — Update Records: acctCollectionToUpdate]   ← single bulk Update
```

**Why it works:** Even with 200 Opportunities in the batch, the parent Account is locked once (when the bulk Update Account fires). The lock is held briefly because Update Account is the last DML before commit.

This still doesn't fix the parallel-transactions case — two simultaneous batches both updating `001ABC` will still contend. For that, see Example 2.

---

## Example 2: The Real Fix — Decouple via Platform Event

**Context:** Same as Example 1. The collect-then-update fix from above helped bulk Data Loader runs but did not eliminate the UNABLE_TO_LOCK_ROW errors during normal interactive usage, because individual reps editing different Opportunities under the same Account `001ABC` still produce parallel single-row transactions that all queue on the Account lock.

**Solution: Decouple the Account update via a Platform Event.**

Step 1 — Define the Platform Event:

```
Object: Opportunity_Stage_Changed__e
Fields:
  - Opportunity_Id__c     (Text 18, required)
  - Account_Id__c          (Text 18, required)
  - New_Stage__c           (Text 80)
  - Changed_At__c          (DateTime, default = NOW())
  - User_Id__c             (Text 18)
Publish Behavior: Publish Immediately   ← critical, see gotchas
```

Step 2 — Refactor the publisher flow on Opportunity:

```
Trigger: Opportunity (after-save, Updated)
        │
        ▼
[Decision: Stage changed?]
        │
        ├── Yes
        │     │
        │     ▼
        │   [Update Records: Opportunity — Stage_Last_Changed__c = NOW()]   ← cheap, no parent recalc
        │     │
        │     ▼
        │   [Create Records: Opportunity_Stage_Changed__e]
        │       Opportunity_Id__c = $Record.Id
        │       Account_Id__c = $Record.AccountId
        │       New_Stage__c = $Record.StageName
        │     │
        │     ▼
        │   [End]   ← publisher transaction commits, Account lock NEVER taken
        │
        └── No → [End]
```

Step 3 — Build the subscriber flow:

```
Trigger: Platform Event — Opportunity_Stage_Changed__e
        │
        ▼
[Get Records: Account WHERE Id = $Record.Account_Id__c]
        │
        ▼
[Decision: Account found?]
        │
        ├── Yes
        │     │
        │     ▼
        │   [Update Records: Account]
        │       LastActivityDate = TODAY()
        │       Pipeline_Recalc_Needed__c = true
        │       │
        │       └── Fault Path → [Create Records: Integration_Log__c]
        │
        └── No → [Create Records: Integration_Log__c severity=WARNING]
```

**Why it works:**

- The Opportunity transaction never takes the Account lock. It writes to the Opportunity row, publishes the event (an in-memory + small DB write to the event bus, no parent-object lock), and ends. The Opportunity transaction now completes in <100ms regardless of Account contention.
- The subscriber flow runs in a separate transaction with its own retry budget. If two concurrent events hit the same Account, the subscriber's automatic 10-retry usually absorbs the contention because the subscriber is doing nothing else (no other DML, no other locks).
- Event subscribers naturally batch — Salesforce delivers events in batches of up to 2,000 per subscriber invocation. If 50 Opportunity events fire in the same second, the subscriber processes them as one batch with one Account update per affected Account. Bulk pattern emerges for free.
- Failure isolation: if the subscriber fault path fires, the Opportunity update has already committed. The user sees no error; the central log captures the issue for ops review. With the synchronous flow, both updates would have rolled back.

**Verification:**

```apex
// Anonymous Apex — load test
List<Opportunity> opps = [
    SELECT Id, StageName FROM Opportunity
    WHERE AccountId = '001ABC' AND StageName != 'Closed Won'
    LIMIT 20
];

// Fire 20 parallel @future updates to the same Account's Opportunities
for (Opportunity o : opps) {
    OppUpdateAsync.fireAsync(o.Id);  // each @future runs in its own transaction
}
```

After deploying the Platform Event refactor, this test produces zero UNABLE_TO_LOCK_ROW. Before the refactor, it consistently produced 4–8 faults out of 20.

---

## Example 3: The Wrong "Fix" — Adding `FOR UPDATE` Inside an Invocable Apex

**Context:** A practitioner reads about `FOR UPDATE` SOQL and builds an invocable Apex action that pre-locks the Account before the flow updates it.

```apex
public class LockAccountForUpdate {
    @InvocableMethod(label='Pre-lock Account')
    public static void preLock(List<Id> acctIds) {
        // BAD: this just makes contention worse.
        Account a = [SELECT Id FROM Account WHERE Id IN :acctIds FOR UPDATE LIMIT 1];
    }
}
```

The flow is wired to call this invocable before the `Update Account` step, on the theory that pre-locking will reduce contention.

**What goes wrong:**

- `FOR UPDATE` increases the lock-hold duration. The lock is now held from the SOQL query through the rest of the transaction, instead of just from the Update DML through commit. Hold time goes up; contention gets worse.
- `FOR UPDATE` does not eliminate UNABLE_TO_LOCK_ROW — it just shifts the wait from the Update to the SOQL. The same parallel transactions are still serialized, just with the bottleneck moved.
- The lock-acquisition wait now happens in the invocable Apex (which has fewer fault-handling options than the Flow's native Update fault path).

**Correct approach:** Use `FOR UPDATE` only when there is a true read-modify-write race condition — for example, incrementing a counter field where you must read the current value before computing the new one. For generic contention from parallel updates, the fix is decoupling (Pattern 2) or scheduling (Pattern 4), not pre-locking.

---

## Example 4: Mass Ownership Reassignment — The Hidden Group Lock

**Context:** A Sales Ops admin uses a screen flow to reassign 2,000 Leads from one queue (`Queue_Inbound_East`) to another (`Queue_Inbound_West`). The flow loops over Leads and calls Update inside the loop.

**Problem:** Every Update Lead with a new OwnerId acquires:

1. Lock on the Lead row.
2. Lock on the old queue's Group row (`Queue_Inbound_East`).
3. Lock on the new queue's Group row (`Queue_Inbound_West`).

With 2,000 sequential updates inside a loop, the same two Group rows are locked-released 2,000 times. The first iteration's commit releases the Group lock just in time for the second iteration to grab it — but only if no other transaction (sales rep working a Lead, integration job writing Leads) is also trying to acquire the same Group lock. Under any concurrent activity, UNABLE_TO_LOCK_ROW fires within the first few hundred iterations.

**Solution: Bulk update + schedule off-hours.**

```
[Get Records: Leads WHERE OwnerId = oldQueueId]   ← collection of 2000
        │
        ▼
[Loop over Leads]
        │
        ├── [Assignment: lead.OwnerId = newQueueId]
        ├── [Assignment: leadsToUpdate.add(lead)]
        │
        ▼
[After Loop — Update Records: leadsToUpdate]   ← single bulk Update
                                                  ← runs at 2am via scheduled flow
```

The single bulk Update locks each Group row exactly once for the duration of the bulk DML (a few seconds, not minutes). Scheduling at 2am eliminates concurrent-user contention entirely.

**Why it works:** Bulk DML acquires the implicit Group locks once per batch, not once per record. Even 2,000 Leads → 2 Group lock acquisitions total. Off-hours scheduling ensures no other transaction is competing for those Group rows.

---

## Anti-Pattern: Adding Custom Retry Logic Inside the Flow

**What practitioners do:** After seeing UNABLE_TO_LOCK_ROW faults, they add a fault-path loop in Flow that catches the error and retries the Update up to 5 times with a Wait element.

```
[Update Records: Account]
        │
        └── Fault Path
              │
              ▼
            [Decision: retry count < 5?]
              │
              ├── Yes
              │     ▼
              │   [Wait: 30 seconds]
              │     ▼
              │   [Update Records: Account]   ← same operation, retry
              │
              └── No → [End — give up]
```

**What goes wrong:**

- Salesforce **already retries** failed DML 10 times with exponential backoff. The flow-level retry is layered on top, so total attempts are now 50+ (10 platform retries × 5 flow retries). The contention window is extended dramatically.
- The Wait element does not pause the transaction — it ends the transaction and resumes in a new one. Each "retry" is a fresh transaction, which means re-acquiring locks from scratch. The Wait does not relieve contention; it just delays it.
- Flow Wait elements consume a `Pause` resource and are governed (limited per flow). High-volume retries can hit the Pause limit before the contention clears.
- The legitimate fix (decouple via Platform Event or Queueable) is now harder to spot because the retry logic masks the symptom.

**Correct approach:** Trust Salesforce's automatic retries. If they're not enough, the contention is severe and requires architectural decoupling, not more retries. Wire the fault path to an Integration_Log__c entry so the contention is visible, and route the work to a Queueable or Platform Event subscriber where it can run with its own independent retry budget.
