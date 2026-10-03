# LLM Anti-Patterns: Async Apex

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

**Detection hint:** `@future` annotation in newly generated code. It should be `Queueable` unless there is an explicit reason (for example, a mixed DML workaround).

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

**Why it happens:** LLMs pattern-match on "needs to run asynchronously" and reach for Batch Apex. For 5 to 50 records, Batch Apex is overkill: it introduces a full lifecycle (start/execute/finish), queuing delays in the flex queue, and extra complexity. A Queueable or even synchronous processing is simpler.

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

## Anti-Pattern 3: Calling a future method from a Batch context

**What the LLM generates:**

```apex
public void execute(Database.BatchableContext bc, List<Account> scope) {
    for (Account a : scope) {
        ExternalSyncService.syncAccountFuture(a.Id); // @future from batch
    }
}
```

**Why it happens:** LLMs generate `@future` calls without checking the calling context. The governor limit "Maximum number of methods with the future annotation allowed per Apex invocation" is **50** synchronously and, asynchronously, **"0 in batch and future contexts; 50 in queueable context"**. So from a `@future` method or a Batch `execute()`/`finish()` the allocation is zero and the call fails at runtime. UNVERIFIED (2026-10-03): the exact exception type and message text.

**Queueable is the exception, and it is a real one.** A `Queueable.execute()` gets an allocation of **50** `@future` calls; calling `@future` from a Queueable is documented and supported, not an error. Salesforce does caution that "having multiple future methods fan out from a queueable job isn't a recommended practice as it can rapidly add many future methods to the asynchronous queue." That is a design smell to raise, not a platform restriction to assert.

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

**Detection hint:** `@future` method calls inside classes that implement `Database.Batchable`, or inside another `@future`-annotated method. A `@future` call inside a `Queueable` is **legal**; flag it only as a design review item (fan-out), never as a compile or runtime error.

---

## Anti-Pattern 4: Enqueuing multiple queueable jobs from a synchronous trigger

**What the LLM generates:**

```apex
trigger AccountTrigger on Account (after update) {
    for (Account a : Trigger.new) {
        if (a.NeedsSync__c) {
            System.enqueueJob(new SyncJob(a.Id)); // 200-row chunk can exceed the 50-per-transaction limit
        }
    }
}
```

**Why it happens:** LLMs generate per-record async dispatch. A synchronous transaction can enqueue up to 50 Queueables and an asynchronous one only 1 (Apex Developer Guide 262, Per-Transaction Apex Limits, L19573). Version 1.0.0 of this skill said the synchronous limit was 1; that was wrong. Per-record enqueues still fail: a 200-record trigger chunk can pass 50, and each job counts against the org's daily async executions.

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

**Why it happens:** LLMs chain batch jobs in `finish()` without considering that only 5 batch jobs can be queued or active (the rest wait in the flex queue with Status `Holding`, up to 100). If the flex queue already holds 100 jobs, `Database.executeBatch` throws a `LimitException` (Apex Developer Guide 262, "Holding Batch Jobs in the Apex Flex Queue").

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    Integer holding = [
        SELECT COUNT() FROM AsyncApexJob
        WHERE JobType = 'BatchApex'
        AND Status = 'Holding'
    ];
    if (holding < 95) { // Flex queue holds 100 jobs in Holding status; leave headroom
        Database.executeBatch(new NextBatch());
    } else {
        // Fallback: schedule retry via Schedulable or log for manual intervention
        System.schedule('RetryNextBatch', '0 0 * * * ? *', new BatchRetryScheduler());
    }
}
```

**Detection hint:** `Database\.executeBatch` in a `finish` method without checking `AsyncApexJob` count or wrapping in try/catch.

---

## Anti-Pattern 6: Ignoring the 50,000-row SOQL limit in @future methods

**What the LLM generates:**

```apex
@future
public static void processAllContacts() {
    List<Contact> contacts = [SELECT Id, Email FROM Contact]; // No LIMIT
    // Process all contacts
}
```

**Why it happens:** LLMs know that async Apex gets higher governor limits (200 SOQL queries, 12 MB heap, 60,000 ms CPU) and assume rows are unlimited too. The total number of records retrieved by SOQL is 50,000 in both synchronous and asynchronous Apex (Apex Developer Guide 262, Per-Transaction Apex Limits, L19546). Only a Batch `start()` returning `Database.getQueryLocator` reaches 50 million rows.

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

---

## Anti-Pattern 7: Doing the work, or the callout, inside Schedulable.execute

**What the LLM generates:**

```apex
global class NightlySync implements Schedulable {
    global void execute(SchedulableContext ctx) {
        HttpResponse res = new Http().send(buildRequest()); // synchronous callout
        List<Account> rows = [SELECT Id FROM Account WHERE Needs_Sync__c = true];
        update rows;
    }
}
```

**Why it happens:** The model treats the scheduler as an async worker with async limits.

**Correct pattern:** Synchronous limits apply to scheduled Apex, and synchronous callouts aren't supported from it (Apex Developer Guide 262, L19536 and "Apex Scheduler Notes and Best Practices"). Dispatch instead:

```apex
global class NightlySync implements Schedulable {
    global void execute(SchedulableContext ctx) {
        System.enqueueJob(new AccountSyncJob()); // implements Queueable, Database.AllowsCallouts
    }
}
```

**Detection hint:** `HttpRequest`, `Http().send`, or large SOQL and DML inside a class that implements `Schedulable`.
