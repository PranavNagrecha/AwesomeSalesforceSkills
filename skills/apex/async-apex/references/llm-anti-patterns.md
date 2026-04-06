# LLM Anti-Patterns — Async Apex

Common mistakes AI coding assistants make when generating or advising on async Apex mechanism selection and design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending @future when Queueable is the better fit

**What the LLM generates:**

```apex
@future(callout=true)
public static void syncAccount(Id accountId) {
    Account a = [SELECT Id, Name FROM Account WHERE Id = :accountId];
    HttpRequest req = new HttpRequest();
    // ... make callout
}
```

**Why it happens:** `@future` is deeply embedded in older training data and Trailhead examples. LLMs default to it even though Queueable offers complex parameter passing (not just primitives), job chaining, monitoring via `AsyncApexJob`, and the Finalizer interface. `@future` methods only accept primitive parameters and cannot be chained or monitored by ID.

**Correct pattern:**

```apex
public class AccountSyncJob implements Queueable, Database.AllowsCallouts {
    private Id accountId;

    public AccountSyncJob(Id accountId) {
        this.accountId = accountId;
    }

    public void execute(QueueableContext ctx) {
        Account a = [SELECT Id, Name FROM Account WHERE Id = :accountId];
        // ... make callout with full error handling
    }
}

// Enqueue:
System.enqueueJob(new AccountSyncJob(accountId));
```

**Detection hint:** `@future` annotation in newly generated code — it should be `Queueable` unless there is an explicit reason (e.g., mixed DML workaround).

---

## Anti-Pattern 2: Using Batch Apex for small record volumes that fit in a single transaction

**What the LLM generates:**

```apex
public class UpdateFiveRecordsBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id FROM Account WHERE Type = \'Target\' LIMIT 5');
    }
    public void execute(Database.BatchableContext bc, List<Account> scope) {
        for (Account a : scope) { a.Status__c = 'Updated'; }
        update scope;
    }
    public void finish(Database.BatchableContext bc) {}
}
```

**Why it happens:** LLMs pattern-match on "needs to run asynchronously" and reach for Batch Apex. For 5-50 records, Batch Apex is overkill — it introduces a full lifecycle (start/execute/finish), queuing delays in the flex queue, and extra complexity. A Queueable or even synchronous processing is simpler.

**Correct pattern:**

```apex
// For small volumes, use Queueable
public class UpdateTargetAccountsJob implements Queueable {
    public void execute(QueueableContext ctx) {
        List<Account> accounts = [SELECT Id FROM Account WHERE Type = 'Target' LIMIT 50];
        for (Account a : accounts) { a.Status__c = 'Updated'; }
        update accounts;
    }
}
```

**Detection hint:** `Database.Batchable` class where the `start` query includes `LIMIT` under 200 or where the expected record count is documented as small.

---

## Anti-Pattern 3: Calling a future method from a Batch or Queueable context

**What the LLM generates:**

```apex
public void execute(Database.BatchableContext bc, List<Account> scope) {
    for (Account a : scope) {
        ExternalSyncService.syncAccountFuture(a.Id); // @future from batch
    }
}
```

**Why it happens:** LLMs generate `@future` calls without checking the calling context. You cannot call a `@future` method from another `@future` method, a Batch Apex `execute`, or a Queueable `execute`. The platform throws `System.AsyncException: Future method cannot be called from a future or batch method`.

**Correct pattern:**

```apex
public void execute(Database.BatchableContext bc, List<Account> scope) {
    // Make callouts directly if batch implements Database.AllowsCallouts
    // Or collect IDs and enqueue a Queueable (1 per execute)
    List<Id> ids = new List<Id>();
    for (Account a : scope) { ids.add(a.Id); }
    if (!ids.isEmpty()) {
        System.enqueueJob(new ExternalSyncJob(ids));
    }
}
```

**Detection hint:** `@future` method calls inside classes that implement `Database.Batchable` or `Queueable`.

---

## Anti-Pattern 4: Enqueuing multiple queueable jobs from a synchronous trigger

**What the LLM generates:**

```apex
trigger AccountTrigger on Account (after update) {
    for (Account a : Trigger.new) {
        if (a.NeedsSync__c) {
            System.enqueueJob(new SyncJob(a.Id)); // Limit: 1 per sync transaction
        }
    }
}
```

**Why it happens:** LLMs generate per-record async dispatch. In a synchronous Apex transaction (trigger, controller), you can only enqueue 1 Queueable job. Enqueuing 2 or more throws `System.LimitException`.

**Correct pattern:**

```apex
trigger AccountTrigger on Account (after update) {
    List<Id> syncIds = new List<Id>();
    for (Account a : Trigger.new) {
        if (a.NeedsSync__c) {
            syncIds.add(a.Id);
        }
    }
    if (!syncIds.isEmpty()) {
        System.enqueueJob(new SyncJob(syncIds)); // Single job, all IDs
    }
}
```

**Detection hint:** `System\.enqueueJob` inside a `for` loop in trigger context.

---

## Anti-Pattern 5: Not handling the flex queue when submitting batch jobs at scale

**What the LLM generates:**

```apex
// In finish() of one batch, start another
public void finish(Database.BatchableContext bc) {
    Database.executeBatch(new NextBatch()); // Assumes slot is available
}
```

**Why it happens:** LLMs chain batch jobs in `finish()` without considering that only 5 batch jobs can be actively processing concurrently (the rest go to the flex queue, up to 100). If the flex queue is full, `Database.executeBatch` throws an exception and the chain breaks silently.

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    Integer activeBatches = [
        SELECT COUNT() FROM AsyncApexJob
        WHERE JobType = 'BatchApex'
        AND Status IN ('Processing', 'Preparing', 'Queued')
    ];
    if (activeBatches < 95) { // Leave headroom in flex queue
        Database.executeBatch(new NextBatch());
    } else {
        // Fallback: schedule retry via Schedulable or log for manual intervention
        System.schedule('RetryNextBatch', '0 0 * * * ? *', new BatchRetryScheduler());
    }
}
```

**Detection hint:** `Database\.executeBatch` in a `finish` method without checking `AsyncApexJob` count or wrapping in try/catch.

---

## Anti-Pattern 6: Ignoring the 250K row limit for @future method SOQL queries

**What the LLM generates:**

```apex
@future
public static void processAllContacts() {
    List<Contact> contacts = [SELECT Id, Email FROM Contact]; // No LIMIT
    // Process all contacts
}
```

**Why it happens:** LLMs know that async Apex gets higher governor limits but incorrectly assume unlimited queries. `@future` methods share the same 50K SOQL row limit as synchronous Apex. Only Batch Apex `start()` with `Database.getQueryLocator` gets the 50 million row limit.

**Correct pattern:**

```apex
// Use Batch Apex for unbounded record volumes
public class ContactProcessorBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id, Email FROM Contact');
    }
    public void execute(Database.BatchableContext bc, List<Contact> scope) {
        // Process in chunks
    }
    public void finish(Database.BatchableContext bc) {}
}
```

**Detection hint:** `@future` method with SOQL queries that have no `WHERE` filter or `LIMIT` clause, suggesting unbounded result sets.
