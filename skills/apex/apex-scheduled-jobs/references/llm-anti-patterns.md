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

**Why it happens:** LLMs treat the Schedulable `execute` method like a Batch `execute` method, and then assume "async feature, async limits". Both halves are wrong. The Apex Developer Guide states the exception in a note above the limits table: "Although scheduled Apex is an asynchronous feature, synchronous limits apply to scheduled Apex jobs" (apexdev L19536). So the body gets 100 SOQL, 6 MB heap and 10,000 ms CPU — *less* than the Batch it should have dispatched. The guide's own recommendation is unambiguous: "all processing must take place in a separate class" (apexdev L16972–L16973).

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

**Why it happens:** LLMs confuse Unix cron (5 fields) with the Salesforce syntax, which the guide gives as `Seconds Minutes Hours Day_of_month Month Day_of_week Optional_year` (apexdev L16815–L16817) — six required fields plus an optional year, so a 6-field and a 7-field expression are both legal and a 5-field one never is. They also drop the `?`, which the guide defines as available "only… for Day_of_month and Day_of_week" and "typically used when specifying a value for one and not the other" (apexdev L16879–L16881). Every example in the guide follows that convention.

Two related fabrications to watch for: LLMs frequently assert that the seconds field must be `0` (the documented range is 0–59, and the guide's own example is `'20 30 8 10 2 ?'` at apexdev L16637), and they invent sub-hourly schedules (the guide states "Apex doesn't allow for a job to be scheduled more than once an hour", apexdev L16923). They also rarely produce `L`, `W`, or `#`, which have no Unix equivalent — `'0 0 22 ? * 6L'` for the last Friday of the month is a documented example (apexdev L16925).

**Correct pattern:**

```apex
// Seconds Minutes Hours Day_of_month Month Day_of_week [Optional_year]
String cronExp = '0 0 0 * * ?';   // Every day at midnight — 6 fields, year omitted
System.schedule('Daily Job', cronExp, new DailyCleanup());
```

**Detection hint:** cron string literals with fewer than 6 or more than 7 whitespace-separated fields, or with neither day field set to `?`. `scripts/check_apex_scheduled_jobs.py` enforces exactly this.

---

## Anti-Pattern 3: Not checking the 100 scheduled job limit before scheduling

**What the LLM generates:**

```apex
// In post-deployment script or anonymous Apex
System.schedule('My Job', '0 0 6 * * ? *', new MySchedulable());
// Throws System.AsyncException if 100 jobs already scheduled
```

**Why it happens:** LLMs generate `System.schedule` calls without checking whether the org is at or near the ceiling — 100 Apex classes scheduled concurrently, and **5 in Developer Edition** (salesforce_app_limits_cheatsheet L313), which is the number that actually bites in a scratch org or Trailhead playground. LLMs also count the wrong thing: an unfiltered `SELECT COUNT() FROM CronTrigger` includes scheduled Flows, report runs and dashboard refreshes, which are separate `CronJobDetail.JobType` values and do not compete for this ceiling.

**Correct pattern:**

```apex
// JobType '7' is scheduled Apex; '6' Flow, '8' report run, '3' dashboard refresh.
Integer activeApexJobs = [
    SELECT COUNT() FROM CronTrigger
    WHERE CronJobDetail.JobType = '7'
      AND State IN ('WAITING', 'ACQUIRED', 'EXECUTING', 'PAUSED', 'PAUSED_BLOCKED', 'BLOCKED')
];
if (activeApexJobs >= 100) {
    throw new IllegalArgumentException('Scheduled Apex ceiling reached: ' + activeApexJobs + '/100');
}
System.schedule('My Job', '0 0 6 * * ?', new MySchedulable());
```

Use `SchedulerAdmin.scheduleOrReplace()` from `references/code-examples.md`, which folds the count check and the abort into one call.

**Detection hint:** `System\.schedule\(` without a preceding `CronTrigger` count check, or a count query missing the `CronJobDetail.JobType = '7'` filter.

---

## Anti-Pattern 4: Scheduling a job without an abort-and-reschedule pattern for deployments

**What the LLM generates:**

```apex
// Scheduled once and never updated
System.schedule('Nightly Sync', '0 0 2 * * ? *', new NightlySyncSchedulable());
```

**Why it happens:** LLMs generate a one-time schedule call and stop there, so the script is not re-runnable: a second run throws `System.AsyncException: The Apex job named "jobName" is already scheduled for execution` (apexdev L16810–L16813), which is exactly what happens when a failed release is retried.

The deeper reason to abort first is the deploy lock, which LLMs almost never mention: "If there are one or more active scheduled jobs for an Apex class, you can't update the class **or any classes referenced by this class** through the Salesforce user interface" (apexdev L16604–L16606), and a Metadata API deploy fails with `This schedulable class has jobs pending or in progress - CronTrigger IDs (ids)` (apexdev L16990–L16992). The guide's own recommendation is to "first delete the scheduled job, and then deploy your changes. After deployment, create a new scheduled job with the updated class" (apexdev L16993–L16995).

UNVERIFIED (2026-09-05): whether a *live* job keeps running the previously compiled version of a class that was updated via the Metadata API bypass. The guide warns only that with the bypass enabled "the job can fail" (apexdev L16992–L16993); it does not describe which version executes.

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

**Why it happens:** LLMs forget the bracket. The guide's mechanism: "All asynchronous calls made after the startTest method are collected by the system. When stopTest is executed, all asynchronous processes are run synchronously" (apexdev L16712–L16716). The nuance LLMs also miss is that the job is not simply skipped without the bracket — "If you don't include the `System.schedule` method within the `startTest` and `stopTest` methods, the scheduled job executes at the end of your test method for Apex saved using Salesforce API version 25.0 and later" (apexdev L16717–L16720). It runs *too late* for any assertion in the method, which is why the failure reads as "the job never ran".

A second omission: `System.schedule` needs a job name unique among scheduled jobs, so a test method that hardcodes one can collide with another test in the same run. Generate a suffix per method.

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

**Why it happens:** LLMs do not distinguish between Schedulable and Queueable callout rules. The guide: "Synchronous Web service callouts aren't supported from scheduled Apex. To make asynchronous callouts, use Queueable Apex, implementing the `Database.AllowsCallouts` marker interface" (apexdev L16975–L16976).

The correction LLMs get wrong in the *other* direction is the Batch route. A dispatched Batch class may call out directly: "If your scheduled Apex executes a batch job using the `Database.AllowsCallouts` marker interface, callouts are supported from the batch class" (apexdev L16976–L16977). Models routinely insert an unnecessary Queueable hop between the Schedulable and a Batch that could have carried the marker itself. Note also that `Database.AllowsCallouts` on the `Schedulable` is not a documented route — the marker belongs on the dispatched class.

UNVERIFIED (2026-09-05): the exact exception thrown. Models confidently emit `System.CalloutException: Callout from scheduled Apex not supported`; that string is in neither apexdev.txt nor apexrefguide.txt. The restriction is documented; the message is not.

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


---

## Anti-Pattern 7: Assuming `CronTrigger` state proves the work succeeded

**What the LLM generates:**

```apex
// "Verify the nightly job is healthy"
CronTrigger ct = [SELECT State, NextFireTime FROM CronTrigger WHERE CronJobDetail.Name = 'Nightly Rollup'];
System.assertEquals('WAITING', ct.State);   // declares victory
```

**Why it happens:** models treat `CronTrigger` as the job's status record. It is the *timer's* status record. A `Schedulable` that dispatches a batch finishes in milliseconds and returns `CronTrigger` to `WAITING` for the next fire regardless of whether the dispatched batch then failed, threw, or processed zero records. Every monitoring answer an LLM gives from `CronTrigger` alone is a false-clean signal.

**Correct pattern:** join through to the work. `AsyncApexJob.CronTriggerId` "only applies to ScheduledApex job type" and is available in API version 53.0 and later (object_reference, AsyncApexJob), and `Status` / `NumberOfErrors` / `ExtendedStatus` carry the outcome.

```soql
SELECT Id, ApexClass.Name, JobType, Status, NumberOfErrors, ExtendedStatus,
       JobItemsProcessed, TotalJobItems, CreatedDate, CompletedDate
FROM AsyncApexJob
WHERE ApexClass.Name = 'AccountRollupBatch' AND CreatedDate = LAST_N_DAYS:3
ORDER BY CreatedDate DESC
```

**Detection hint:** a health check, monitoring query, or assertion that reads `CronTrigger` and never touches `AsyncApexJob`.

---

## Anti-Pattern 8: Capturing per-run values in the scheduler's constructor

**What the LLM generates:**

```apex
public class NightlyScheduler implements Schedulable {
    private Date runDate = Date.today();          // frozen at System.schedule() time
    private List<Id> targets;

    public NightlyScheduler(List<Id> targets) {
        this.targets = targets;                    // frozen too
    }

    public void execute(SchedulableContext sc) {
        Database.executeBatch(new RollupBatch(runDate, targets), 200);
    }
}
```

**Why it happens:** models carry over constructor-injection habits from stateless services, where a new instance is created per invocation. Scheduled Apex is the opposite: "Scheduled job objects, along with their member variables and properties, persist from initialization to subsequent scheduled runs. The object state at the time of invocation of `System.schedule()` persists in subsequent job executions" (apexdev L16984–L16986). So `runDate` is the date the job was *scheduled*, forever, and `targets` is a record list that goes stale the next day. The bug is invisible on day one, which is why it survives review.

**Correct pattern:** derive per-run values inside `execute()`, and mark anything that must not be serialized as `transient` — the guide's own remedy: "With Scheduled Apex, use the `transient` keyword so that member variables and properties aren't persisted" (apexdev L16987–L16989).

```apex
public with sharing class NightlyScheduler implements Schedulable {
    public transient Date runDateOverride;         // not serialized into the schedule

    public void execute(SchedulableContext sc) {
        Date runDate = (runDateOverride == null) ? Date.today() : runDateOverride;
        Database.executeBatch(new RollupBatch(runDate), 200);
    }
}
```

**Detection hint:** a non-`transient`, non-`static` field in a `Schedulable` class assigned from `Date.today()`, `Datetime.now()`, `UserInfo.*`, or a constructor parameter, and read inside `execute()`.
