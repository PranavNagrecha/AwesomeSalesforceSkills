# LLM Anti-Patterns — Flow Record Locking And Contention

Common mistakes AI coding assistants make when generating or advising on Flow record locking and contention.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Generating an After-Save Flow That Loops Over Children and Updates Each One

**What the LLM generates:** A record-triggered after-save flow on Opportunity that uses a Get Records to fetch related Tasks, then loops over them, calling Update Records inside the loop to set a `Last_Synced_With_Opp__c` flag on each Task.

```
[Get Records: Tasks WHERE WhatId = $Record.Id]
        │
        ▼
[Loop over Tasks]
        │
        ├── [Assignment: task.Last_Synced_With_Opp__c = true]
        ├── [Update Records: task]   ← BAD — inside the loop
        │
        ▼
[End]
```

**Why it happens:** The LLM defaults to imperative "for each X, update X" thinking from procedural programming languages. Bulk-collection-then-DML is non-obvious if you're translating Java/Python loops directly into Flow.

**Correct pattern:**

```
[Get Records: Tasks WHERE WhatId = $Record.Id]
        │
        ▼
[Loop over Tasks]
        │
        ├── [Assignment: task.Last_Synced_With_Opp__c = true]
        ├── [Assignment: tasksToUpdate.add(task)]   ← collect, do not Update
        │
        ▼
[After Loop — Update Records: tasksToUpdate]   ← single bulk Update
```

This locks each Task's parent (the Opportunity, in this case via the WhatId polymorphic lookup) once per bulk transaction, not once per Task. Critically, every Task Update locks the parent Opportunity (the very record that just fired the trigger), so the loop-update shape would lock-and-release the Opportunity N times within its own after-save transaction — a recipe for self-induced contention.

**Detection hint:** Search the flow XML for `<actionType>recordUpdate</actionType>` whose parent element is `<loops>` or whose `connector.targetReference` is reachable from inside a `<loops>` block. Any Update inside a Loop is suspect.

---

## Anti-Pattern 2: Synchronous Update Account From a Quote-Trigger Flow Without Considering the Opportunity → Account Lock Chain

**What the LLM generates:** A record-triggered flow on Quote (after-save, when status changes to "Approved") that updates the parent Opportunity AND the parent Account directly, both synchronously in the same transaction.

```
[Trigger: Quote (after-save, Status = 'Approved')]
        │
        ▼
[Get Records: Opportunity]
        │
        ▼
[Update Records: Opportunity — set Has_Approved_Quote__c = true]
        │
        ▼
[Get Records: Account]
        │
        ▼
[Update Records: Account — set Last_Quote_Approved__c = NOW()]
        │
        ▼
[End]
```

**Why it happens:** The LLM does not internalize the implicit lock chain. From the LLM's perspective, "Update Account" is one DML against one record. In reality, the Quote update has already locked the parent Opportunity AND the parent Account; the explicit Update Opportunity then re-locks the Opportunity AND the Account; the explicit Update Account is locking an already-locked row. The transaction holds three significant locks for its full duration.

**Correct pattern:** Recognize the chain and decouple the Account update via a Platform Event:

```
[Trigger: Quote (after-save, Status = 'Approved')]
        │
        ▼
[Update Records: Opportunity — set Has_Approved_Quote__c = true]   ← parent of Quote, lock unavoidable
        │
        ▼
[Create Records: Account_Quote_Approved__e Platform Event]
        │       Account_Id__c = $Record.Opportunity.AccountId
        │
        ▼
[End]   ← Account lock NEVER taken in this transaction

Subscriber flow on Account_Quote_Approved__e:
        │
        ▼
[Update Records: Account — set Last_Quote_Approved__c = NOW()]   ← isolated transaction
```

The Account update happens in the subscriber's transaction with its own retry budget and naturally batches across many Quote approvals.

**Detection hint:** A flow that updates more than one object in the same after-save transaction, where the objects are linked by a parent-child chain (Quote → Opportunity → Account, OpportunityLineItem → Opportunity → Account, Case → Account), is at risk. Audit the lock chain explicitly.

---

## Anti-Pattern 3: Missing the Implicit User-Row Lock When a Flow Changes Ownership

**What the LLM generates:** A screen flow that allows a sales manager to reassign 500 Leads from Rep A to Rep B by looping over the selected Leads and calling Update inside the loop.

```
[Loop over selectedLeadIds]
        │
        ├── [Get Records: Lead WHERE Id = current loop item]
        ├── [Assignment: lead.OwnerId = newOwnerId]
        ├── [Update Records: lead]   ← locks Lead + old User + new User
        │
        ▼
[End]
```

**Why it happens:** Owner change is treated as "just another field update" by the LLM. The implicit User-row lock (and Group lock for queues) is invisible in the flow XML — there's no element labeled "Lock User row." The LLM has no surface signal that ownership changes are heavier than other updates.

**Correct pattern:**

```
[Get Records: Leads WHERE Id IN selectedLeadIds]
        │
        ▼
[Loop over Leads]
        │
        ├── [Assignment: lead.OwnerId = newOwnerId]
        ├── [Assignment: leadsToUpdate.add(lead)]
        │
        ▼
[After Loop — Update Records: leadsToUpdate]   ← single bulk Update, locks each User row once
```

For very large reassignments (>1000 records), even bulk DML can contend with concurrent user activity on the old/new owner User rows. Schedule off-hours via a Scheduled Path or a Queueable batch.

**Detection hint:** Any flow that writes to `OwnerId` is an ownership-change flow. Audit it specifically for bulk shape AND for scheduling. Mass owner changes during business hours are nearly always a contention bug waiting to happen.

---

## Anti-Pattern 4: Suggesting `FOR UPDATE` as a Fix When the Issue Is Bulk Shape

**What the LLM generates:** When a user reports UNABLE_TO_LOCK_ROW from a flow, the LLM suggests creating an invocable Apex action that uses `SELECT ... FOR UPDATE` to "pre-lock the record before the flow updates it."

```apex
@InvocableMethod
public static void preLockAccount(List<Id> acctIds) {
    Account a = [SELECT Id FROM Account WHERE Id IN :acctIds FOR UPDATE LIMIT 1];
}
```

**Why it happens:** The LLM has read about `FOR UPDATE` in the Apex docs and pattern-matches "lock issue → use locking statement." It does not distinguish between read-modify-write race conditions (the legitimate use case) and parallel-transaction contention (the actual issue 95% of the time).

**Correct pattern:** Diagnose first. If the contention is from bulk shape (Loop + DML), fix the bulk shape (collect-then-update). If the contention is from parallel transactions on a hot parent, decouple via Platform Event. `FOR UPDATE` is correct ONLY when:

- The flow does Get → calculate-from-Get → Update on the same record, AND
- The calculated value depends on the current value (e.g., counter increment), AND
- A concurrent transaction modifying between Get and Update would cause a logically wrong result (lost update).

For all other contention scenarios, `FOR UPDATE` extends the lock-hold duration and makes the problem worse.

**Detection hint:** If the LLM proposes `FOR UPDATE` without first asking "is this a read-modify-write race or just parallel updates?", the recommendation is wrong. Push back and demand the diagnosis.

---

## Anti-Pattern 5: Recommending Retries Inside the Flow When Salesforce Already Retries 10 Times

**What the LLM generates:** A fault-path branch that catches UNABLE_TO_LOCK_ROW and retries the same Update up to 5 times with a Wait element between attempts.

```
[Update Records: Account]
        │
        └── Fault Path
              │
              ▼
            [Decision: retryCount < 5]
              │
              ├── Yes → [Wait: 30 seconds] → [Update Records: Account] (re-attempt)
              └── No → [Send Email Alert]
```

**Why it happens:** The LLM applies a generic "transient failure → retry with backoff" pattern from distributed-systems training data. It does not know that Salesforce already does this transparently for DML lock failures. The LLM also does not know that Flow Wait elements end the transaction and resume in a new one — so each "retry" is a fresh transaction acquiring locks from scratch, not a reattempt within the same lock-acquisition window.

**Correct pattern:** Trust Salesforce's automatic retries (10 attempts with exponential backoff). When they're not enough, the contention is severe and requires architectural decoupling, not more retries. Wire the fault path to a central log entry so the contention is visible:

```
[Update Records: Account]
        │
        └── Fault Path
              │
              ▼
            [Create Records: Integration_Log__c]
              Severity__c = 'ERROR'
              Source__c = 'Account_Update_From_Quote_Flow'
              Message__c = $Flow.FaultMessage
              Record_Id__c = $Record.AccountId
              │
              ▼
            [End]   ← the original transaction will rollback per Flow default behavior
```

Then refactor the flow itself to decouple via Platform Event or Queueable so contention doesn't recur.

**Detection hint:** Any flow that contains a Wait element followed by a re-attempt of the failed DML is doing manual retry layered on top of platform retry. Audit and remove. Replace with a fault-log entry plus an architectural fix.

---

## Anti-Pattern 6: Treating Get Records As If It Locks the Row

**What the LLM generates:** Code or flow design that assumes `Get Records: Account WHERE Id = X` followed by some computation followed by `Update Records: Account` is atomic — that no concurrent transaction can modify the Account between the Get and the Update.

For example, an LLM might generate this counter-increment pattern:

```
[Get Records: Account]
        │
        ▼
[Assignment: account.Open_Cases__c = account.Open_Cases__c + 1]
        │
        ▼
[Update Records: account]   ← LOST UPDATE if two flows run in parallel
```

**Why it happens:** Confusion with traditional database read-with-lock patterns from imperative languages. The LLM assumes Salesforce's Get Records is equivalent to `SELECT ... FOR UPDATE` in PostgreSQL or MySQL. It is not.

**Correct pattern:** For counter increments and other read-modify-write patterns, EITHER:

- Use a Roll-Up Summary field (computed by the platform, no race possible), OR
- Use invocable Apex with explicit `SELECT ... FOR UPDATE`:

```apex
@InvocableMethod
public static void incrementOpenCases(List<Id> acctIds) {
    List<Account> accts = [SELECT Id, Open_Cases__c FROM Account WHERE Id IN :acctIds FOR UPDATE];
    for (Account a : accts) {
        a.Open_Cases__c = (a.Open_Cases__c == null ? 0 : a.Open_Cases__c) + 1;
    }
    update accts;
}
```

The `FOR UPDATE` clause is the only way in Apex to prevent the lost-update race. Flow alone cannot achieve it.

**Detection hint:** Search for any pattern of `Get Records X` → `Assignment X.field = X.field + ...` → `Update Records X`. Counter increments, balance adjustments, sequence number generation are the canonical examples. Flag every one for FOR UPDATE refactor or Roll-Up Summary replacement.
