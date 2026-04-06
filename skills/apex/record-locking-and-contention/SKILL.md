---
name: record-locking-and-contention
description: "Use when diagnosing or preventing UNABLE_TO_LOCK_ROW errors, record lock contention in Apex or Bulk API loads, FOR UPDATE locking, parent-child lock escalation, and deadlock scenarios. Triggers: 'UNABLE_TO_LOCK_ROW', 'record lock contention', 'FOR UPDATE SOQL', 'deadlock', 'lock timeout'. NOT for approval-process record locking (admin/approval-processes) or optimistic concurrency via timestamps."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Performance
triggers:
  - "how to prevent UNABLE_TO_LOCK_ROW errors"
  - "record locking contention in Bulk API"
  - "FOR UPDATE in SOQL causing lock timeout"
  - "child record inserts locking parent row"
  - "deadlock between concurrent Apex transactions"
  - "data skew causing lock failures"
tags:
  - record-locking
  - contention
  - FOR-UPDATE
  - UNABLE_TO_LOCK_ROW
  - data-skew
  - deadlock
inputs:
  - "object relationships and data volumes involved"
  - "whether contention comes from Bulk API parallelism, concurrent Apex, or parent-child lock escalation"
  - "error logs showing UNABLE_TO_LOCK_ROW or lock timeout patterns"
outputs:
  - "root cause analysis of lock contention"
  - "lock ordering and data-skew mitigation recommendations"
  - "retry strategy for transient lock failures"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Record Locking and Contention

Use this skill when transactions fail with UNABLE_TO_LOCK_ROW or when high-concurrency workloads contend on the same rows. The objective is to identify the locking mechanism involved, eliminate unnecessary contention, and add resilient retry logic where contention is unavoidable.

---

## Before Starting

Gather this context before working on anything in this domain:

- What error is surfacing: UNABLE_TO_LOCK_ROW, lock timeout, or silent transaction rollback?
- Is contention driven by Bulk API parallel batches, concurrent user actions, scheduled jobs, or platform events?
- Does the data model have parent-child skew where a single parent record has thousands of children?

---

## Core Concepts

### Exclusive Row Locks and the 10-Second Timeout

Every DML statement in Salesforce acquires an exclusive row lock on the affected records for the duration of the transaction. If a second transaction attempts to lock the same row, it waits up to 10 seconds. After that timeout, the platform throws `UNABLE_TO_LOCK_ROW` and the waiting transaction fails. This is not configurable.

### FOR UPDATE Acquires Explicit Locks in SOQL

Adding `FOR UPDATE` to a SOQL query acquires exclusive locks on the returned rows immediately, before any DML occurs. This is useful for read-modify-write patterns where you need to guarantee no other transaction changes the row between your read and your write. However, FOR UPDATE locks persist for the entire transaction, so long-running logic after the query extends the lock window and increases contention risk.

### Parent-Child Lock Escalation

When you insert, update, or delete a child record, Salesforce also locks the parent record to maintain rollup summaries, sharing calculations, and relationship integrity. This means concurrent child-record operations against the same parent contend on the parent row even though no two transactions touch the same child. This is the primary cause of lock contention in orgs with data skew.

### Deadlocks from Inconsistent Lock Ordering

When two transactions lock the same set of rows in different orders, a deadlock can occur. Transaction A holds Row 1 and waits for Row 2; Transaction B holds Row 2 and waits for Row 1. The platform detects this and fails one transaction with UNABLE_TO_LOCK_ROW. Consistent lock ordering by a deterministic key (such as record ID) prevents this.

---

## Common Patterns

### Sort-Before-DML to Prevent Deadlocks

**When to use:** Any batch or bulk operation that processes records from multiple parent groups or touches rows that other concurrent transactions may also touch.

**How it works:** Sort the records by a deterministic key (parent ID, or record ID) before performing DML. This guarantees all concurrent transactions acquire locks in the same order, eliminating deadlock risk.

```apex
// Sort by AccountId before update to prevent deadlock
List<Contact> contacts = [SELECT Id, AccountId, LastName FROM Contact WHERE ...];
contacts.sort(); // Custom comparator on AccountId
update contacts;
```

**Why not the alternative:** Processing records in arbitrary order is the root cause of most deadlocks in parallel batch operations.

### Retry via Queueable for Transient Lock Failures

**When to use:** When lock contention is occasional and unavoidable, such as high-volume integrations writing to shared parent records.

**How it works:** Catch `UNABLE_TO_LOCK_ROW` in a try-catch block and enqueue a Queueable to retry the failed subset of records after a short delay.

```apex
public class RetryableUpdate implements Queueable {
    private List<SObject> records;
    private Integer retryCount;

    public RetryableUpdate(List<SObject> records, Integer retryCount) {
        this.records = records;
        this.retryCount = retryCount;
    }

    public void execute(QueueableContext ctx) {
        try {
            update records;
        } catch (DmlException e) {
            if (e.getMessage().contains('UNABLE_TO_LOCK_ROW') && retryCount < 3) {
                System.enqueueJob(new RetryableUpdate(records, retryCount + 1));
            } else {
                throw e; // Exhausted retries or different error
            }
        }
    }
}
```

**Why not the alternative:** Retrying synchronously in a loop wastes governor limits and still contends on the same lock window. Queueable retry introduces a natural delay.

### Bulk API Serial Mode for Skewed Data

**When to use:** Bulk API loads that target child objects with high parent-record skew (such as loading Contacts where many share the same Account).

**How it works:** Sort the CSV by parent ID and set the Bulk API job to serial mode. Serial mode processes one batch at a time, so no two batches contend on the same parent row simultaneously.

**Why not the alternative:** Parallel mode is faster but creates multiple batches that can lock the same parent row concurrently, causing widespread UNABLE_TO_LOCK_ROW failures.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Bulk API loads failing on child objects with shared parents | Sort CSV by parent ID and use serial mode | Eliminates parallel contention on parent rows |
| Apex batch job with intermittent lock errors | Sort scope records by parent key before DML | Prevents deadlock from inconsistent ordering |
| High-frequency integrations writing to shared records | Catch UNABLE_TO_LOCK_ROW and retry via Queueable | Transient contention resolves with a short delay |
| Extreme data skew (10,000+ children per parent) | Request Granular Locking from Salesforce Support | Prevents child DML from escalating to parent lock |
| Read-modify-write requiring consistency | Use FOR UPDATE but minimize post-query logic | Reduces the lock-hold window |
| Multiple objects updated in one transaction | Lock rows in consistent ID order across all transactions | Prevents deadlocks |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Identify the contention source — examine error logs for UNABLE_TO_LOCK_ROW, note which object and operation triggers it, and determine whether the cause is parallel batches, parent-child escalation, or concurrent user actions.
2. Map the data model — identify parent-child relationships involved and check for data skew (a single parent with thousands of children).
3. Check lock ordering — review Apex code and batch logic to confirm records are processed in a deterministic, consistent order across all concurrent transactions.
4. Apply the appropriate pattern — sort-before-DML for deadlocks, serial mode for Bulk API skew, Queueable retry for transient failures, or Granular Locking for extreme skew.
5. Validate — run the checker script against the codebase, load-test with concurrent transactions, and confirm UNABLE_TO_LOCK_ROW errors no longer appear in the target scenario.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The specific lock contention source is identified (parent-child, parallel batch, concurrent DML, FOR UPDATE).
- [ ] Records are sorted by a deterministic key before DML in batch and bulk operations.
- [ ] FOR UPDATE queries are followed by minimal logic to reduce the lock-hold window.
- [ ] Retry logic exists for scenarios where transient lock contention is unavoidable.
- [ ] Bulk API jobs targeting skewed data use serial mode with sorted input.
- [ ] Data skew is assessed and Granular Locking is considered for extreme cases.
- [ ] No code acquires locks in inconsistent order across concurrent execution paths.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Child DML locks the parent row** — inserting or updating a child record also acquires an exclusive lock on the parent. This is invisible in code but is the leading cause of contention in skewed data models.
2. **FOR UPDATE locks persist for the entire transaction** — if you run expensive logic after a FOR UPDATE query, you hold locks far longer than necessary, creating a wide contention window for other transactions.
3. **The 10-second lock timeout is not configurable** — you cannot extend or shorten it. If your transaction holds a lock for more than 10 seconds, any concurrent transaction waiting on the same row will fail.
4. **Aggregate SOQL on locked rows also blocks** — a SOQL query with GROUP BY or aggregate functions on rows that another transaction has locked will wait and potentially time out, even though no DML is involved.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Lock contention root cause analysis | Identifies the locking mechanism, contention source, and data-skew factors |
| Lock ordering recommendation | Deterministic sort strategy for DML operations to prevent deadlocks |
| Retry strategy | Queueable-based retry pattern for transient UNABLE_TO_LOCK_ROW errors |
| Bulk API configuration guidance | Serial-mode and CSV-sorting recommendations for skewed data loads |

---

## Related Skills

- `apex/batch-apex-patterns` — use when lock contention arises from batch Apex scope processing and requires batch-level mitigations.
- `apex/apex-queueable-patterns` — use when implementing retry logic via Queueable chaining for lock-failure recovery.
- `data/bulk-api-and-large-data-loads` — use when lock contention is driven by Bulk API job configuration rather than Apex code.
- `admin/data-skew-and-sharing-performance` — use when the root cause is data-model skew rather than code-level locking patterns.
