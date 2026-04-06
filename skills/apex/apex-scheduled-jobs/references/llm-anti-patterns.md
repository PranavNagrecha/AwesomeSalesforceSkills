# LLM Anti-Patterns — Apex Scheduled Jobs

Common mistakes AI coding assistants make when generating or advising on Schedulable Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Putting heavy data processing directly in the Schedulable execute method

**What the LLM generates:**

```apex
public class DailyCleanup implements Schedulable {
    public void execute(SchedulableContext ctx) {
        List<Lead> staleLeads = [SELECT Id FROM Lead WHERE CreatedDate < LAST_N_DAYS:90];
        delete staleLeads; // Could be thousands of records — hits governor limits
    }
}
```

**Why it happens:** LLMs treat the Schedulable `execute` method like a Batch `execute` method. Scheduled Apex runs in a synchronous context with standard governor limits. Processing thousands of records directly causes `Too many DML rows` or CPU timeout exceptions.

**Correct pattern:**

```apex
public class DailyCleanup implements Schedulable {
    public void execute(SchedulableContext ctx) {
        // Dispatch to Batch Apex for the heavy lifting
        Database.executeBatch(new StaleLeadCleanupBatch(), 200);
    }
}
```

**Detection hint:** `Schedulable` class whose `execute` method contains SOQL queries that could return unbounded results or DML on large lists, without dispatching to Batch or Queueable.

---

## Anti-Pattern 2: Using invalid cron expression syntax

**What the LLM generates:**

```apex
// "Run every day at midnight"
String cronExp = '0 0 0 * * *'; // Wrong — missing 7th field or wrong day-of-week
System.schedule('Daily Job', cronExp, new DailyCleanup());
```

**Why it happens:** LLMs confuse Unix cron (5 fields) with Salesforce cron (7 fields: seconds, minutes, hours, day-of-month, month, day-of-week, year). They also forget that when day-of-month is specified, day-of-week must be `?` and vice versa.

**Correct pattern:**

```apex
// Salesforce cron: seconds minutes hours day-of-month month day-of-week year
String cronExp = '0 0 0 * * ? *'; // Every day at midnight
System.schedule('Daily Job', cronExp, new DailyCleanup());
```

**Detection hint:** Cron expressions with 5 or 6 fields instead of 7, or with `*` in both day-of-month and day-of-week positions.

---

## Anti-Pattern 3: Not checking the 100 scheduled job limit before scheduling

**What the LLM generates:**

```apex
// In post-deployment script or anonymous Apex
System.schedule('My Job', '0 0 6 * * ? *', new MySchedulable());
// Throws System.AsyncException if 100 jobs already scheduled
```

**Why it happens:** LLMs generate `System.schedule` calls without checking whether the org is at or near the 100 concurrent scheduled job limit. In production orgs with many managed packages, this limit is commonly close to full.

**Correct pattern:**

```apex
Integer activeJobs = [SELECT COUNT() FROM CronTrigger WHERE State = 'WAITING'];
if (activeJobs >= 95) {
    System.debug(LoggingLevel.ERROR, 'Approaching scheduled job limit: ' + activeJobs + '/100');
    // Alert admin or abort a stale job first
} else {
    System.schedule('My Job', '0 0 6 * * ? *', new MySchedulable());
}
```

**Detection hint:** `System\.schedule\(` without a preceding `CronTrigger` count check, especially in setup scripts.

---

## Anti-Pattern 4: Scheduling a job without an abort-and-reschedule pattern for deployments

**What the LLM generates:**

```apex
// Scheduled once and never updated
System.schedule('Nightly Sync', '0 0 2 * * ? *', new NightlySyncSchedulable());
```

**Why it happens:** LLMs generate a one-time schedule call. But when the Schedulable class is modified and redeployed, the existing scheduled job still references the old compiled version. The job must be aborted and rescheduled to pick up the new code.

**Correct pattern:**

```apex
// Abort existing job if present, then reschedule
String jobName = 'Nightly Sync';
List<CronTrigger> existing = [
    SELECT Id FROM CronTrigger
    WHERE CronJobDetail.Name = :jobName AND State IN ('WAITING', 'ACQUIRED')
];
for (CronTrigger ct : existing) {
    System.abortJob(ct.Id);
}
System.schedule(jobName, '0 0 2 * * ? *', new NightlySyncSchedulable());
```

**Detection hint:** `System\.schedule\(` without a preceding query for existing `CronTrigger` records with the same job name.

---

## Anti-Pattern 5: Testing scheduled Apex without Test.startTest/stopTest boundaries

**What the LLM generates:**

```apex
@IsTest
static void testScheduler() {
    String cronExp = '0 0 0 * * ? *';
    System.schedule('Test Job', cronExp, new DailyCleanup());
    // Assertions immediately — the scheduled job has not executed
    System.assertEquals(1, [SELECT COUNT() FROM AsyncApexJob WHERE JobType = 'ScheduledApex']);
}
```

**Why it happens:** LLMs forget that the scheduled job's `execute` method only fires synchronously in tests when bracketed by `Test.startTest()` and `Test.stopTest()`. Without that boundary, assertions about the job's side effects fail.

**Correct pattern:**

```apex
@IsTest
static void testScheduler() {
    // Setup test data
    Test.startTest();
    String cronExp = '0 0 0 15 6 ? 2099';
    String jobId = System.schedule('Test Job', cronExp, new DailyCleanup());
    Test.stopTest();

    // Verify the job was scheduled
    CronTrigger ct = [SELECT Id, CronExpression FROM CronTrigger WHERE Id = :jobId];
    System.assertEquals('0 0 0 15 6 ? 2099', ct.CronExpression);

    // Verify side effects of the execute method
    // (batch was dispatched, records updated, etc.)
}
```

**Detection hint:** Scheduled Apex test without `Test\.startTest` and `Test\.stopTest` bracketing the `System.schedule` call.

---

## Anti-Pattern 6: Making callouts directly from Schedulable execute

**What the LLM generates:**

```apex
public class ScheduledSync implements Schedulable {
    public void execute(SchedulableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ExternalApi/sync');
        req.setMethod('POST');
        new Http().send(req); // Callouts not allowed from Schedulable
    }
}
```

**Why it happens:** LLMs do not distinguish between Schedulable and Queueable callout restrictions. Scheduled Apex cannot make callouts directly. The callout must be delegated to a Queueable or future method that implements `Database.AllowsCallouts`.

**Correct pattern:**

```apex
public class ScheduledSync implements Schedulable {
    public void execute(SchedulableContext ctx) {
        System.enqueueJob(new SyncCalloutJob());
    }
}

public class SyncCalloutJob implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ExternalApi/sync');
        req.setMethod('POST');
        HttpResponse res = new Http().send(req);
    }
}
```

**Detection hint:** `Http\(\)\.send` or `new Http\(\)` inside a class that implements `Schedulable` directly.
