# LLM Anti-Patterns — Record Locking and Contention

Common mistakes AI coding assistants make when generating or advising on record locking and contention.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending FOR UPDATE as a Universal Fix for Lock Errors

**What the LLM generates:** "Add FOR UPDATE to your SOQL query to prevent UNABLE_TO_LOCK_ROW errors."

**Why it happens:** LLMs conflate "locking" with "lock prevention." FOR UPDATE acquires locks; it does not prevent contention. Training data from Java/SQL contexts reinforces SELECT FOR UPDATE as a concurrency solution without noting the Salesforce-specific consequences.

**Correct pattern:**

```
FOR UPDATE should only be used for read-modify-write consistency (e.g., decrementing a counter).
To prevent UNABLE_TO_LOCK_ROW, reduce contention through sorting, serial processing, or retry logic.
```

**Detection hint:** Look for FOR UPDATE recommended in the same paragraph as UNABLE_TO_LOCK_ROW without qualifying the use case.

---

## Anti-Pattern 2: Ignoring Parent-Child Lock Escalation Entirely

**What the LLM generates:** "The lock error is on Contact, so optimize your Contact DML. The Account is not involved."

**Why it happens:** LLMs reason about locks at the object level mentioned in the error message. They do not account for the platform behavior where child DML also locks the parent row.

**Correct pattern:**

```
When child records share a parent, DML on the child also locks the parent row.
Concurrent child operations against the same parent will contend on the parent lock.
Sort child records by parent ID and consider serial processing for skewed parents.
```

**Detection hint:** Advice that focuses exclusively on the child object without mentioning parent-row locking or data skew.

---

## Anti-Pattern 3: Suggesting Synchronous Retry Loops

**What the LLM generates:** "Wrap the DML in a while loop and retry up to 3 times when you catch UNABLE_TO_LOCK_ROW."

**Why it happens:** General-purpose retry patterns from non-Salesforce contexts (Java, Python) use synchronous retry with backoff. On Salesforce, synchronous retries consume CPU time against governor limits and still contend on the same lock because the competing transaction has not had time to commit.

**Correct pattern:**

```apex
// Use Queueable for async retry — each execution is a separate transaction
catch (DmlException e) {
    if (e.getDmlType(0) == StatusCode.UNABLE_TO_LOCK_ROW && retryCount < 3) {
        System.enqueueJob(new RetryHandler(records, retryCount + 1));
    }
}
```

**Detection hint:** `while` loop or `for` loop containing a try-catch for UNABLE_TO_LOCK_ROW in synchronous Apex.

---

## Anti-Pattern 4: Claiming the Lock Timeout Is Configurable

**What the LLM generates:** "You can increase the lock timeout by adjusting the database settings" or "Set the lock wait timeout to 30 seconds."

**Why it happens:** In MySQL, PostgreSQL, and Oracle, lock wait timeouts are configurable. LLMs generalize this to Salesforce, which uses a fixed 10-second timeout that cannot be changed through any setting or support request.

**Correct pattern:**

```
The Salesforce row-lock timeout is fixed at 10 seconds and is not configurable.
Design transactions to hold locks for less than 10 seconds.
If contention is unavoidable, use async retry rather than trying to extend the timeout.
```

**Detection hint:** Any mention of configuring, extending, or setting a lock timeout value in Salesforce.

---

## Anti-Pattern 5: Using FOR UPDATE in Batch Apex Start Method

**What the LLM generates:** "Lock the records in the start method to prevent other processes from modifying them during the batch."

**Why it happens:** LLMs apply the general FOR UPDATE pattern without knowing that FOR UPDATE is prohibited in `Database.getQueryLocator()` and will throw a runtime error.

**Correct pattern:**

```
FOR UPDATE cannot be used in batch start queries.
Use ORDER BY in the start query to group records by parent key.
Handle locking within execute() if a read-modify-write pattern is needed.
```

**Detection hint:** FOR UPDATE appearing inside a `start()` method or a `Database.getQueryLocator()` call.

---

## Anti-Pattern 6: Recommending Database.setSavepoint() to Handle Lock Errors

**What the LLM generates:** "Use Database.setSavepoint() before the DML so you can rollback and retry if a lock error occurs."

**Why it happens:** LLMs conflate savepoints (which handle partial rollback) with lock-error recovery. A savepoint does not help with UNABLE_TO_LOCK_ROW because the entire transaction is typically rolled back by the platform, and retrying within the same transaction still contends on the same lock.

**Correct pattern:**

```
Savepoints do not solve lock contention. The failing transaction must retry in a
separate transaction (via Queueable) so the competing transaction has time to commit
and release its lock.
```

**Detection hint:** `Database.setSavepoint()` recommended in the context of UNABLE_TO_LOCK_ROW recovery.
