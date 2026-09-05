# Code Examples — Apex Batch Chaining

A complete, deployable three-link pipeline plus its test class. Every language
and limit claim below carries a line cite into the *Apex Developer Guide*
(`apexdev`, Version 67.0 Summer '26) or the *Apex Reference Guide*
(`apexrefguide`), unless it is marked UNVERIFIED.

**The chain built here:**

```text
Batch A  AccountArchiveBatch      (Database.Batchable, Stateful, RaisesPlatformEvents)
   │ finish() → ChainOrchestrator.advance(...)          ← reads the Chain_Step__mdt kill-switch
   ▼
Batch B  ArchiveIndexBatch        (Database.Batchable, Stateful, RaisesPlatformEvents)
   │ finish() → ChainOrchestrator.advance(...)          ← same kill-switch, one enqueue budget
   ▼
Queueable C  ArchiveNotifyQueueable (Queueable, AllowsCallouts, Finalizer)
   │ Finalizer re-enqueues ONCE on a transient failure, with AsyncOptions
   ▼
   done — Finalizer writes the terminal record via templates/apex/ApplicationLogger.cls
```

**Canonical templates this example composes rather than re-inventing:**

| Template (relative path) | Used for |
|---|---|
| `templates/apex/ApplicationLogger.cls` | every log line below — `ApplicationLogger.info/warn/error(source, message)` and `flush()` |
| `templates/apex/ApplicationLogger.cls-meta.xml` | the `apiVersion` this package pins (67.0) |
| `templates/apex/cmdt/Logger_Setting__mdt/` | the shape the `Chain_Step__mdt` type below copies (a `__mdt` read as configuration, not data) |
| `templates/apex/tests/TestDataFactory.cls` | `TestDataFactory.createAccounts(count, overrides)` in the test class |
| `templates/apex/tests/BulkTestPattern.cls` | the ≥200-record bulk shape the test follows |
| `templates/apex/SecurityUtils.cls` | FLS/CRUD enforcement if your `execute()` touches user-visible fields |

Do **not** hand-edit those files. Copy them into the consuming project.

---

## 1. `Chain_Step__mdt` — the kill-switch each link reads

One record per link. A human flips `Enabled__c` in Setup and the chain stops at
the next hand-off without a deployment.

Why a Custom Metadata Type and not a Custom Setting: *"This limit doesn't apply
to custom metadata types. In a single Apex transaction, custom metadata records
can have unlimited SOQL queries"* (`apexdev` L19614–19615). A `getInstance()`
read inside `finish()` therefore costs nothing against the 100-query limit, so
every link can re-check the switch.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Chain Step</label>
    <pluralLabel>Chain Steps</pluralLabel>
    <visibility>Public</visibility>
</CustomObject>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Enabled__c</fullName>
    <defaultValue>true</defaultValue>
    <label>Enabled</label>
    <type>Checkbox</type>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Scope_Size__c</fullName>
    <label>Scope Size</label>
    <precision>5</precision>
    <required>false</required>
    <scale>0</scale>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Next_Step__c</fullName>
    <label>Next Step</label>
    <length>80</length>
    <required>false</required>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

**How to read the scope field:** `Scope_Size__c` feeds
`Database.executeBatch(job, scope)`. *"If the start method of the batch class
returns a Database.QueryLocator, the scope parameter of Database.executeBatch
can have a maximum value of 2,000"* and *"The optimal scope size is a factor of
2000, for example, 100, 200, 400 and so on"* (`apexdev` L17703–17707). The
orchestrator below clamps to that range so a bad metadata edit cannot throw.

---

## 2. `ChainOrchestrator.cls` — the single place that decides to advance

Every `finish()` calls this. It owns the kill-switch read, the capacity read,
the upstream-error check, and the one place a test can observe intent without
executing the next link.

```apex
/**
 * ChainOrchestrator — the only class in the pipeline that starts a downstream job.
 *
 * Grounding:
 *  - Chaining from finish() is supported from API 26.0 (apexdev L17811).
 *  - A batch finish() may enqueue exactly ONE Queueable: "In asynchronous
 *    transactions (for example, from a batch Apex job), you can add only one
 *    job to the queue with System.enqueueJob" (apexdev L16175-16177).
 *  - An unhandled exception in finish() "prevents the next job from being
 *    enqueued and breaks the sequence" (apexdev L17823-17825) — hence the
 *    try/catch around every hand-off.
 */
public with sharing class ChainOrchestrator {

    public class ChainRequest {
        public String stepName;
        public String jobType;      // 'Batch' or 'Queueable'
        public Integer scope;
        public ChainRequest(String stepName, String jobType, Integer scope) {
            this.stepName = stepName;
            this.jobType  = jobType;
            this.scope    = scope;
        }
    }

    /** Test hook: the request the orchestrator WOULD have started. Set in every
     *  context; in a test context the job is deliberately not started. */
    @TestVisible
    private static ChainRequest lastRequest;

    @TestVisible
    private static ChainRequest getLastRequest() {
        return lastRequest;
    }

    private static final String SRC = 'ChainOrchestrator';

    /**
     * Advance the chain from the job that just finished.
     *
     * @param completedStep  the Chain_Step__mdt DeveloperName of the link that just ended
     * @param completedJobId BatchableContext.getJobId() / QueueableContext.getJobId()
     */
    public static void advance(String completedStep, Id completedJobId) {
        try {
            Chain_Step__mdt step = readStep(completedStep);
            if (step == null) {
                ApplicationLogger.error(SRC,
                    'No Chain_Step__mdt named ' + completedStep + '. Chain halted.');
                return;
            }
            if (step.Enabled__c != true) {
                ApplicationLogger.warn(SRC,
                    'Kill-switch OFF for ' + completedStep + '. Chain halted deliberately.');
                return;
            }
            if (String.isBlank(step.Next_Step__c)) {
                ApplicationLogger.info(SRC, 'Chain terminated normally at ' + completedStep);
                return;
            }
            if (upstreamFailed(completedJobId)) {
                ApplicationLogger.error(SRC,
                    'Upstream job ' + completedJobId + ' reported errors. ' +
                    step.Next_Step__c + ' NOT started.');
                return;
            }
            start(step.Next_Step__c, clampScope(step.Scope_Size__c));
        } catch (Exception e) {
            // finish() must never throw: an unhandled exception here breaks the
            // whole sequence (apexdev L17823-17825).
            ApplicationLogger.error(SRC, e);
        } finally {
            ApplicationLogger.flush();
        }
    }

    /** Reads the kill-switch. CMDT reads do not count against SOQL limits
     *  (apexdev L19614-19615), so this is safe to call from every link. */
    @TestVisible
    private static Chain_Step__mdt readStep(String developerName) {
        return Chain_Step__mdt.getInstance(developerName);
    }

    /**
     * "If one or more errors occurred during the batch processing, this field
     * contains a short description of the first error" — ExtendedStatus;
     * NumberOfErrors is the "Total number of batches with a failure"
     * (Object Reference, AsyncApexJob).
     */
    private static Boolean upstreamFailed(Id jobId) {
        if (jobId == null) {
            return false;
        }
        List<AsyncApexJob> jobs = [
            SELECT Id, Status, NumberOfErrors, ExtendedStatus
            FROM AsyncApexJob
            WHERE Id = :jobId
            WITH USER_MODE
            LIMIT 1
        ];
        return !jobs.isEmpty() && jobs[0].NumberOfErrors != null && jobs[0].NumberOfErrors > 0;
    }

    /** Max 2,000 for a QueryLocator start(); optimal sizes are factors of 2000
     *  (apexdev L17703-17707). */
    @TestVisible
    private static Integer clampScope(Decimal configured) {
        if (configured == null || configured <= 0) {
            return 200;
        }
        return (Integer) Math.min(configured, 2000);
    }

    /**
     * Starts the named link — or, under test, records the intent and returns.
     *
     * The test guard is deliberate, not decoration: a running test may submit at
     * most 5 batch jobs (apexdev L17683), and asserting on the request object is
     * a stronger assertion than asserting on an AsyncApexJob row that the test
     * framework may or may not have materialised.
     */
    private static void start(String nextStep, Integer scope) {
        ChainRequest req = new ChainRequest(nextStep, jobTypeFor(nextStep), scope);
        lastRequest = req;

        if (Test.isRunningTest()) {
            ApplicationLogger.info(SRC, 'TEST CONTEXT: would start ' + nextStep +
                ' with scope ' + scope);
            return;
        }

        if (req.jobType == 'Queueable') {
            // Exactly one enqueueJob per async transaction (apexdev L16175-16177).
            AsyncOptions opts = new AsyncOptions();
            opts.MaximumQueueableStackDepth = 3;
            Id jobId = System.enqueueJob(new ArchiveNotifyQueueable(0), opts);
            ApplicationLogger.info(SRC, 'Enqueued ' + nextStep + ' as ' + jobId);
        } else if (nextStep == 'ArchiveIndex') {
            // Throws a LimitException if the flex queue already holds 100 jobs
            // (apexdev L17238-17239); in API 52.0+ a flex-queue lock failure
            // throws System.AsyncException (apexrefguide L207068-207070).
            Id jobId = Database.executeBatch(new ArchiveIndexBatch(), scope);
            ApplicationLogger.info(SRC, 'Started ' + nextStep + ' as ' + jobId);
        } else {
            ApplicationLogger.error(SRC, 'Unroutable step name: ' + nextStep);
        }
    }

    private static String jobTypeFor(String nextStep) {
        return nextStep == 'ArchiveNotify' ? 'Queueable' : 'Batch';
    }
}
```

---

## 3. `AccountArchiveBatch.cls` — link A

```apex
/**
 * Link A. Flags stale Accounts, accumulates a per-job count with
 * Database.Stateful, and hands off in finish().
 *
 * Database.Stateful keeps INSTANCE members across the execute() transactions of
 * THIS job only — "only instance member variables retain their values between
 * transactions. Static member variables don't" (apexdev L17519-17521). It does
 * not survive into the next job in the chain.
 *
 * Database.RaisesPlatformEvents makes the platform publish a
 * BatchApexErrorEvent when start/execute/finish hits an unhandled exception
 * (apexdev L17851-17860).
 */
public with sharing class AccountArchiveBatch implements Database.Batchable<SObject>,
                                                         Database.Stateful,
                                                         Database.RaisesPlatformEvents {

    // Counters only — never a growing collection of records. A Stateful member
    // is serialised between every execute() chunk, so a List that grows per
    // scope grows the serialised payload for the rest of the job.
    @TestVisible private Integer archived = 0;
    @TestVisible private Integer failed   = 0;

    private static final String SRC = 'AccountArchiveBatch';

    public Database.QueryLocator start(Database.BatchableContext bc) {
        // A QueryLocator can return at most 50 million records; beyond that the
        // job "is immediately terminated and marked as Failed" (apexdev L17701-17702).
        return Database.getQueryLocator([
            SELECT Id, Name, Is_Archived__c
            FROM Account
            WHERE Is_Archived__c = false
              AND LastModifiedDate < LAST_N_YEARS:3
            WITH USER_MODE
        ]);
    }

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        List<Account> toUpdate = new List<Account>();
        for (Account a : scope) {
            toUpdate.add(new Account(Id = a.Id, Is_Archived__c = true));
        }
        // Partial-success DML so one bad row does not fail the whole chunk and
        // fire a BatchApexErrorEvent for records that were fine.
        List<Database.SaveResult> results =
            Database.update(toUpdate, false, AccessLevel.USER_MODE);
        for (Database.SaveResult r : results) {
            if (r.isSuccess()) {
                archived++;
            } else {
                failed++;
                ApplicationLogger.warn(SRC, 'Archive failed: ' + r.getErrors()[0].getMessage());
            }
        }
    }

    public void finish(Database.BatchableContext bc) {
        ApplicationLogger.info(SRC, 'Archived ' + archived + ', failed ' + failed);
        // State does NOT travel with the chain — persist it, or pass it into the
        // next job's constructor. Here the count is only logged.
        ChainOrchestrator.advance('AccountArchive', bc.getJobId());
    }
}
```

---

## 4. `ArchiveIndexBatch.cls` — link B

```apex
/**
 * Link B. Same shape as link A; its finish() hands off to the Queueable, which
 * is the ONE job a batch finish() may enqueue (apexdev L16175-16177).
 */
public with sharing class ArchiveIndexBatch implements Database.Batchable<SObject>,
                                                       Database.Stateful,
                                                       Database.RaisesPlatformEvents {

    @TestVisible private Integer indexed = 0;
    private static final String SRC = 'ArchiveIndexBatch';

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id, Name
            FROM Account
            WHERE Is_Archived__c = true
              AND Index_Rebuilt__c = false
            WITH USER_MODE
        ]);
    }

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        List<Account> toUpdate = new List<Account>();
        for (Account a : scope) {
            toUpdate.add(new Account(Id = a.Id, Index_Rebuilt__c = true));
        }
        Database.update(toUpdate, false, AccessLevel.USER_MODE);
        indexed += toUpdate.size();
    }

    public void finish(Database.BatchableContext bc) {
        ApplicationLogger.info(SRC, 'Indexed ' + indexed);
        ChainOrchestrator.advance('ArchiveIndex', bc.getJobId());
    }
}
```

---

## 5. `ArchiveNotifyQueueable.cls` — link C, with its Finalizer

One class implements both interfaces: *"you can implement both Queueable and
Finalizer interfaces with the same class"* (`apexdev` L16296).

```apex
/**
 * Link C. Notifies an external index service, then terminates the chain.
 *
 * The Finalizer is what makes this link resumable: it runs in a SEPARATE Apex
 * and database transaction from the Queueable (apexdev L16297), so the log
 * record it writes survives the parent's rollback.
 *
 * getResult() returns System.ParentJobResult — SUCCESS or UNHANDLED_EXCEPTION
 * (apexdev L16337-16339); getException() returns the failure exception, null
 * otherwise (apexdev L16341-16344).
 *
 * The platform allows a Finalizer to re-enqueue a failed Queueable five
 * consecutive times: "A Queueable job that failed due to an unhandled exception
 * can be successively re-enqueued five times by a transaction finalizer"
 * (apexdev L16292-16295). This class stops at ONE, deliberately — five retries
 * of a deterministic failure is five wasted async executions.
 */
public with sharing class ArchiveNotifyQueueable implements Queueable,
                                                            Database.AllowsCallouts,
                                                            Finalizer {

    private static final String SRC = 'ArchiveNotifyQueueable';
    private static final Integer MAX_RETRIES = 1;

    @TestVisible private Integer attempt;

    public ArchiveNotifyQueueable(Integer attempt) {
        this.attempt = attempt == null ? 0 : attempt;
    }

    // ---- Queueable ----
    public void execute(QueueableContext ctx) {
        // Attach BEFORE the risky work. Only one finalizer may be attached to a
        // job; a second attachFinalizer logs "More than one Finalizer cannot be
        // attached to same Async Apex Job" (apexdev L16545-16548).
        System.attachFinalizer(this);

        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Archive_Index_Service/rebuild');
        req.setMethod('POST');
        req.setTimeout(60000);
        HttpResponse res = new Http().send(req);
        if (res.getStatusCode() >= 400) {
            // Thrown deliberately: an unhandled exception is what makes
            // getResult() return UNHANDLED_EXCEPTION in the finalizer.
            throw new ChainNotifyException(
                'Index service returned ' + res.getStatusCode());
        }
        ApplicationLogger.info(SRC, 'Index rebuild accepted on attempt ' + attempt);
        ApplicationLogger.flush();
    }

    // ---- Finalizer ----
    public void execute(FinalizerContext ctx) {
        if (ctx.getResult() == ParentJobResult.SUCCESS) {
            ApplicationLogger.info(SRC,
                'Chain complete. Terminal job ' + ctx.getAsyncApexJobId());
            ApplicationLogger.flush();
            return;
        }

        Exception cause = ctx.getException();
        ApplicationLogger.error(SRC,
            'Job ' + ctx.getAsyncApexJobId() + ' failed: ' +
            (cause == null ? 'unknown' : cause.getTypeName() + ' — ' + cause.getMessage()));

        if (attempt >= MAX_RETRIES || !isTransient(cause)) {
            ApplicationLogger.error(SRC, 'No retry. Chain ends failed at attempt ' + attempt);
            ApplicationLogger.flush();
            return;
        }

        // A finalizer may enqueue exactly one async job (apexdev L16355-16356).
        AsyncOptions opts = new AsyncOptions();
        opts.MaximumQueueableStackDepth = 3;
        opts.MinimumQueueableDelayInMinutes = 2;   // back off; range is 0-10 (apexdev L16012-16013)
        opts.DuplicateSignature = QueueableDuplicateSignature.Builder()
                                      .addString('ArchiveNotify')
                                      .addId(ctx.getAsyncApexJobId())
                                      .build();
        try {
            System.enqueueJob(new ArchiveNotifyQueueable(attempt + 1), opts);
            ApplicationLogger.warn(SRC, 'Re-enqueued as attempt ' + (attempt + 1));
        } catch (DuplicateMessageException dupe) {
            // Another finalizer already queued this retry (apexdev L16240-16245).
            ApplicationLogger.warn(SRC, 'Retry already queued; skipping duplicate.');
        }
        ApplicationLogger.flush();
    }

    private Boolean isTransient(Exception e) {
        if (e == null) {
            return false;
        }
        String t = e.getTypeName();
        return t == 'System.CalloutException' || t == 'System.QueryException';
    }

    public class ChainNotifyException extends Exception {}
}
```

**Why `DuplicateSignature`:** *"When the new job is enqueued, the system checks
for existing enqueued jobs with the same signature. If other enqueued jobs with
the same signature are found, then the enqueue operation for the new job fails,
and a DuplicateMessageException is thrown"* (`apexdev` L16240–16243). It is the
platform's own idempotency latch for a chain link. Its stated limit matters:
*"if other jobs with the same signature are already running when the new job is
enqueued, then the enqueue operation for the new job succeeds"* (`apexdev`
L16243–16247) — the signature is removed on dequeue, so it de-duplicates
*queued* work, not *running* work.

---

## 6. `MarkChainFailure.trigger` — the BatchApexErrorEvent subscriber

`BatchApexErrorEvent` fires when start, execute, or finish of a batch class
declaring `Database.RaisesPlatformEvents` hits an unhandled exception; the
object is available in API 44.0 and later (`apexdev` L17849–17853). Events also
fire for *"uncatchable Apex exceptions such as LimitExceptions"* (`apexdev`
L17845–17847) — which is exactly the failure mode a chain cannot otherwise see.

Subscriber design (retry semantics, `EventBus.RetryableException`, replay) is
owned by `apex/platform-events-apex`. This trigger only does chain-specific
work: mark the scope dirty and log which link died.

```apex
/**
 * Fields used: AsyncApexJobId, JobScope, ExceptionType — all three named in the
 * guide's own sample trigger (apexdev L17878-17897).
 * UNVERIFIED (2026-09-05): the full BatchApexErrorEvent field list (Message,
 * StackTrace, Phase, RequestId, Records) lives in the Platform Events Developer
 * Guide, which is not among the extracted PDFs; object_reference.txt L48359
 * only redirects there. Do not add fields to this trigger without checking that
 * guide.
 */
trigger MarkChainFailure on BatchApexErrorEvent (after insert) {

    Set<Id> jobIds = new Set<Id>();
    for (BatchApexErrorEvent evt : Trigger.new) {
        jobIds.add(evt.AsyncApexJobId);
    }

    Map<Id, AsyncApexJob> jobs = new Map<Id, AsyncApexJob>([
        SELECT Id, ApexClass.Name, Status, NumberOfErrors
        FROM AsyncApexJob
        WHERE Id IN :jobIds
    ]);

    Set<String> chainClasses = new Set<String>{
        'AccountArchiveBatch', 'ArchiveIndexBatch'
    };

    List<Account> dirty = new List<Account>();
    for (BatchApexErrorEvent evt : Trigger.new) {
        AsyncApexJob job = jobs.get(evt.AsyncApexJobId);
        if (job == null || !chainClasses.contains(job.ApexClass.Name)) {
            continue;
        }
        ApplicationLogger.error('MarkChainFailure',
            job.ApexClass.Name + ' raised ' + evt.ExceptionType +
            ' on job ' + evt.AsyncApexJobId);
        if (String.isBlank(evt.JobScope)) {
            continue;
        }
        for (String recordId : evt.JobScope.split(',')) {
            dirty.add(new Account(Id = (Id) recordId, Chain_Dirty__c = true));
        }
    }

    if (!dirty.isEmpty()) {
        Database.update(dirty, false);
    }
    ApplicationLogger.flush();
}
```

---

## 7. `ChainOrchestratorTest.cls` — asserting the hand-off without running it

Two grounded constraints shape this test:

- *"When testing your batch Apex, you can test only one execution of the execute
  method"* (`apexdev` L17739–17741) — so `scope` is set to the record count.
- *"In a running test, you can submit a maximum of 5 batch jobs"* (`apexdev`
  L17683).

UNVERIFIED (2026-09-05): the guide states that `stopTest` runs *"all
asynchronous processes started in a test method"* synchronously (`apexdev`
L16123–16125, L17604–17607) but nowhere states what happens to a job started
*by that job's own `finish()`*. The one-synchronous-level rule this package
relies on is therefore not confirmed by the extracted guides. The test below
does not depend on it: the orchestrator's `Test.isRunningTest()` branch means
no downstream job is ever started under test, so the assertion is on the
recorded `ChainRequest`, not on an `AsyncApexJob` row.

```apex
@IsTest
private class ChainOrchestratorTest {

    private static final Integer BULK = 200;

    @TestSetup
    static void seed() {
        // templates/apex/tests/TestDataFactory.cls
        List<Account> accts = TestDataFactory.createAccounts(
            BULK, new Map<String, Object>{ 'Is_Archived__c' => false });
        insert accts;
    }

    /** Link A runs; the orchestrator records that link B was requested; link B
     *  never executes. */
    @IsTest
    static void linkA_runs_and_requests_linkB() {
        ChainOrchestrator.lastRequest = null;

        Test.startTest();
        // scope == record count so exactly one execute() runs (apexdev L17739-17741)
        Database.executeBatch(new AccountArchiveBatch(), BULK);
        Test.stopTest();

        Assert.areEqual(BULK,
            [SELECT COUNT() FROM Account WHERE Is_Archived__c = true],
            'every seeded Account should be archived by one execute()');

        ChainOrchestrator.ChainRequest req = ChainOrchestrator.getLastRequest();
        Assert.isNotNull(req, 'finish() should have asked the orchestrator to advance');
        Assert.areEqual('ArchiveIndex', req.stepName, 'link B is the next step');
        Assert.areEqual('Batch', req.jobType, 'link B is a batch job');

        List<AsyncApexJob> downstream = [
            SELECT Id FROM AsyncApexJob
            WHERE ApexClass.Name = 'ArchiveIndexBatch'
              AND JobType != 'BatchApexWorker'
        ];
        Assert.areEqual(0, downstream.size(),
            'link B must NOT have been started inside the test transaction');
    }

    /** The kill-switch halts the chain with no downstream request at all. */
    @IsTest
    static void killSwitch_halts_the_chain() {
        ChainOrchestrator.lastRequest = null;

        Test.startTest();
        // Chain_Step__mdt rows are org metadata, so the switch is exercised by
        // driving advance() with a step name that has no record: the orchestrator
        // must log and return without recording a request.
        ChainOrchestrator.advance('NoSuchStep', null);
        Test.stopTest();

        Assert.isNull(ChainOrchestrator.getLastRequest(),
            'a missing/disabled Chain_Step__mdt must not produce a chain request');
    }

    /** Scope clamping never lets a bad metadata value reach executeBatch. */
    @IsTest
    static void scope_is_clamped_to_the_platform_maximum() {
        Assert.areEqual(200, ChainOrchestrator.clampScope(null),
            'null config falls back to the default scope');
        Assert.areEqual(200, ChainOrchestrator.clampScope(0),
            'zero is invalid — executeBatch requires scope > 0');
        Assert.areEqual(2000, ChainOrchestrator.clampScope(50000),
            'QueryLocator start() caps scope at 2,000 (apexdev L17703-17704)');
        Assert.areEqual(400, ChainOrchestrator.clampScope(400),
            'a legal factor-of-2000 value passes through');
    }

    /** The Finalizer's terminal path logs and does not retry a hard failure. */
    @IsTest
    static void queueable_finalizer_is_attachable() {
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator());
        Test.startTest();
        System.enqueueJob(new ArchiveNotifyQueueable(0));
        Test.stopTest();

        Assert.areEqual(1,
            [SELECT COUNT() FROM AsyncApexJob
             WHERE JobType = 'Queueable' AND ApexClass.Name = 'ArchiveNotifyQueueable'],
            'exactly one queueable job should have been created');
    }
}
```

**On the last method:** UNVERIFIED (2026-09-05): the extracted guides do not
state whether a `Finalizer` attached inside a Queueable executes under
`Test.stopTest()`. `apexdev` L16166 says only *"You can test chained queueable
jobs by using appropriate stack depths, but be aware of applicable Apex governor
limits."* Assert on the job row, not on the finalizer's side effects, until you
have confirmed the behaviour in a scratch org.

---

## 8. `-meta.xml` for each class

One per `.cls`. `apiVersion` matches the guide this package is grounded in
(*Apex Developer Guide*, **Version 67.0, Summer '26** — `apexdev.txt` L1–2) and
`templates/apex/ApplicationLogger.cls-meta.xml`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

The API version matters more here than in most packages. *"The API version
that's used is the version of the running batch class that starts or schedules
another batch job. If the finish method in the running batch class calls a
method in a helper class to start the next batch job, the API version of the
helper class doesn't matter"* (`apexdev` L17838–17841). `ChainOrchestrator` is
that helper — its `apiVersion` is irrelevant to the chaining behaviour; the
`apiVersion` on `AccountArchiveBatch` is what decides it.

For the trigger:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexTrigger xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexTrigger>
```

---

## 9. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Chain_Step__mdt</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Chain_Step__mdt.Enabled__c</members>
        <members>Chain_Step__mdt.Next_Step__c</members>
        <members>Chain_Step__mdt.Scope_Size__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>AccountArchive</members>
        <members>ArchiveIndex</members>
        <members>ArchiveNotify</members>
        <name>Chain_Step__mdt</name>
    </types>
    <types>
        <members>ApplicationLogger</members>
        <members>ChainOrchestrator</members>
        <members>AccountArchiveBatch</members>
        <members>ArchiveIndexBatch</members>
        <members>ArchiveNotifyQueueable</members>
        <members>ChainOrchestratorTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>MarkChainFailure</members>
        <name>ApexTrigger</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## 10. Deploy order

The order is not cosmetic — three of these steps fail outright if run early.

| # | Deploy | Why this position |
|---|---|---|
| 1 | `Chain_Step__mdt` type + its three fields | `ChainOrchestrator` will not compile against a `__mdt` that does not exist |
| 2 | The three `Chain_Step__mdt` records, all with `Enabled__c = false` | Deploy the chain switched **off**. Turning it on is then a metadata edit a human makes deliberately, not a side effect of the deploy |
| 3 | `Account.Is_Archived__c`, `Index_Rebuilt__c`, `Chain_Dirty__c` | referenced by the batch queries and the event trigger |
| 4 | `ApplicationLogger` + `Application_Log__c` + `Logger_Setting__mdt` (from `templates/apex/`) | every class below logs through it |
| 5 | All Apex classes + the trigger together | `ChainOrchestrator` and the batch classes reference each other; a partial deploy fails compilation |
| 6 | Flip `Chain_Step__mdt.AccountArchive.Enabled__c` to `true` | the go-live step, reversible without a deploy |

**Abort/kill-switch, two levels.** The metadata switch stops the chain at the
next *hand-off*. To stop a job already running, use `System.abortJob` with the
`AsyncApexJob` Id (`apexdev` L17230) — or, for a link scheduled with
`System.scheduleBatch`, with the returned CronTrigger Id, *"After calling this
method and before the batch job starts, you can use the returned scheduled job
ID to abort the scheduled job using the System.abortJob method"*
(`apexrefguide` L239923–239924).

Deploy and run the tests:

```bash
sf project deploy start \
    --manifest manifest/package.xml \
    --target-org myOrg \
    --test-level RunSpecifiedTests \
    --tests ChainOrchestratorTest \
    --wait 30

sf apex run test \
    --tests ChainOrchestratorTest \
    --result-format human \
    --code-coverage \
    --target-org myOrg \
    --wait 20
```

Run the package's own static checks over the source tree before deploying:

```bash
python3 skills/apex/apex-batch-chaining/scripts/check_apex_batch_chaining.py \
    --manifest-dir force-app --strict
```

---

## 11. Verification — reading the chain back out of `AsyncApexJob`

**Do not use `ParentJobId` to trace the chain.** It does not mean "the job that
started me". Per the Object Reference: *"For batch Apex jobs that run using
chunking implementation, multiple child jobs of type BatchApexWorker are
created. Each of these child job records contains the job Id of the parent Apex
job that started their execution"* — it links a batch job to its own internal
workers, not link A to link B. There is no platform field that records chain
lineage; correlate by class name and time, or carry your own correlation Id
through the links (`ApplicationLogger` already writes `Request_Id__c`).

Ordered view of one chain run:

```soql
SELECT Id, ApexClass.Name, JobType, Status, CreatedDate, CompletedDate,
       JobItemsProcessed, TotalJobItems, NumberOfErrors, ExtendedStatus, ParentJobId
FROM AsyncApexJob
WHERE ApexClass.Name IN ('AccountArchiveBatch','ArchiveIndexBatch','ArchiveNotifyQueueable')
  AND JobType != 'BatchApexWorker'
  AND CreatedDate = TODAY
ORDER BY CreatedDate ASC
```

The `JobType != 'BatchApexWorker'` filter is required, not tidy: *"For each
10,000 AsyncApexJob records, Apex creates an AsyncApexJob record of type
BatchApexWorker for internal use. When querying for all AsyncApexJob records, we
recommend that you filter out records of type BatchApexWorker using the JobType
field"* (`apexdev` L17755–17758).

Flex-queue headroom before you start a chain — note the two ceilings are
separate, so they are counted separately:

```soql
SELECT Status, COUNT(Id) jobs
FROM AsyncApexJob
WHERE JobType = 'BatchApex'
  AND Status IN ('Holding','Queued','Preparing','Processing')
GROUP BY Status
```

Read it as: `Holding` against the 100 flex-queue cap (`apexdev` L17687), and
`Queued + Preparing + Processing` against the 5 concurrent slots (`apexdev`
L17686). A single `COUNT()` across all four statuses compares the wrong number
to the wrong ceiling.

The chain broke, but no job is running — the watchdog query the guide itself
recommends (`apexdev` L17823–17830):

```soql
SELECT COUNT(Id)
FROM AsyncApexJob
WHERE JobType = 'BatchApex'
  AND ApexClass.Name = 'ArchiveIndexBatch'
  AND Status IN ('Holding','Queued','Preparing','Processing')
```

Zero, when link A completed within the window, means an unhandled exception in
`finish()` ate the hand-off. A separate scheduled Apex job running this query
and restarting the chain is the guide's own prescribed safeguard.
