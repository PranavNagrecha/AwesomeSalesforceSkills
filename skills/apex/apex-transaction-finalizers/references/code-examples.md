# Code Examples — Apex Transaction Finalizers

A complete, deployable pair: a bulk-safe Queueable that calls out, a `System.Finalizer` that logs the failure through the canonical logger and re-enqueues under a bounded counter, and the test class. Every platform claim in the comments carries an Apex Developer Guide v67.0 (`apexdev.txt`) or Apex Reference Guide v67.0 (`apexrefguide.txt`) line reference.

Canonical building blocks reused rather than re-invented:

| Path | Used for |
|---|---|
| `templates/apex/ApplicationLogger.cls` | `error(source, Exception)` / `info` / `flush` — the durable log façade over `Application_Log__c` |
| `templates/apex/tests/MockHttpResponseGenerator.cls` | `Test.setMock` callout stub, including `pushSequence(...)` for retry simulation |
| `templates/apex/tests/TestDataFactory.cls` | `createAccounts(count, overrides)` for the bulk (200-record) case |
| `templates/apex/HttpClient.cls` | Substitute for the raw `Http().send()` below when the project already standardises callouts |

---

## 1. Custom object the dead-letter row lands in

`Async_Job_Error__c` is the durable failure record. Field API names used by `AccountEnrichmentFinalizer` below:

| Field | Type | Carries |
|---|---|---|
| `Async_Apex_Job_Id__c` | Text(18) | `ctx.getAsyncApexJobId()` — join key to `AsyncApexJob` (ref guide L215642-215649) |
| `Request_Id__c` | Text(64) | `ctx.getRequestId()` — Event Monitoring correlation (ref guide L215674) |
| `Job_Type__c` | Text(80) | Apex class name of the parent Queueable |
| `Attempt__c` | Number(2,0) | Which attempt exhausted the ceiling |
| `Exception_Type__c` | Text(255) | `Exception.getTypeName()` |
| `Error_Message__c` | Text(255) | `Exception.getMessage()` |
| `Stack_Trace__c` | Long Text Area | `Exception.getStackTraceString()` |
| `Payload_JSON__c` | Long Text Area | The record IDs the job was working on |
| `Trace__c` | Long Text Area | Log lines the Queueable buffered onto the Finalizer before it died |

If the project already deploys `templates/apex/custom_objects/`, log to `Application_Log__c` via `ApplicationLogger` and keep `Async_Job_Error__c` only for the dead-letter/reprocessing queue — the two answer different questions (what happened vs. what still needs replaying).

---

## 2. Parent Queueable — `AccountEnrichmentQueueable.cls`

```apex
/**
 * AccountEnrichmentQueueable — pushes a chunk of Accounts to an enrichment API.
 *
 * Bulk-safe: one SOQL query and one callout for the whole chunk, no DML or SOQL
 * inside a loop. Attaches a Finalizer so that a failure — including a
 * LimitException, which no try/catch can intercept — still produces a durable
 * record and a bounded retry.
 */
public with sharing class AccountEnrichmentQueueable implements Queueable, Database.AllowsCallouts {

    private final List<Id> accountIds;
    private final Integer attempt;

    /** Test seam: forces the unhandled-exception path without a real outage. */
    @TestVisible private static Boolean simulateUnhandledFailure = false;

    public AccountEnrichmentQueueable(List<Id> accountIds) {
        this(accountIds, 0);
    }

    public AccountEnrichmentQueueable(List<Id> accountIds, Integer attempt) {
        this.accountIds = accountIds == null ? new List<Id>() : accountIds;
        this.attempt    = attempt == null ? 0 : attempt;
    }

    public void execute(QueueableContext ctx) {

        // Attach FIRST. Everything after this line is covered; anything before it is not.
        // "Attach a finalizer within a Queueable job's execute method." (apexdev L16347-16348)
        AccountEnrichmentFinalizer finalizer =
            new AccountEnrichmentFinalizer(accountIds, attempt);
        System.attachFinalizer(finalizer);

        // Mutating the Finalizer after attaching is supported and is the documented
        // buffering pattern: "The Finalizer framework uses the state of the Finalizer
        // object (if attached) at the end of Queueable execution." (apexdev L16358-16359)
        finalizer.note('attempt=' + attempt + ' size=' + accountIds.size());

        if (simulateUnhandledFailure) {
            throw new CalloutException('Simulated downstream outage');
        }

        // One query for the chunk — never inside a loop.
        List<Account> accounts = [
            SELECT Id, Name, BillingCountry, Website
            FROM Account
            WHERE Id IN :accountIds
            WITH USER_MODE
        ];
        if (accounts.isEmpty()) {
            finalizer.note('no accessible accounts in chunk; nothing to send');
            return;
        }

        // One callout for the chunk.
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Enrichment_API/v1/accounts');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setTimeout(60000);
        req.setBody(JSON.serialize(accounts));

        HttpResponse res = new Http().send(req);
        if (res.getStatusCode() >= 300) {
            // Unhandled on purpose: the Finalizer is the recovery path, not a catch block.
            throw new CalloutException(
                'Enrichment API returned HTTP ' + res.getStatusCode() + ': ' + res.getStatus());
        }

        finalizer.note('enriched=' + accounts.size() + ' http=' + res.getStatusCode());

        // One DML for the chunk.
        List<Account> toUpdate = applyEnrichment(accounts, res.getBody());
        if (!toUpdate.isEmpty()) {
            update as user toUpdate;
        }
    }

    private static List<Account> applyEnrichment(List<Account> accounts, String body) {
        Map<String, Object> payload = (Map<String, Object>) JSON.deserializeUntyped(body);
        Map<String, Object> byId = payload.containsKey('accounts')
            ? (Map<String, Object>) payload.get('accounts')
            : new Map<String, Object>();
        List<Account> touched = new List<Account>();
        for (Account a : accounts) {
            Object enriched = byId.get(a.Id);
            if (enriched instanceof Map<String, Object>) {
                Object site = ((Map<String, Object>) enriched).get('website');
                if (site != null && String.valueOf(site) != a.Website) {
                    a.Website = String.valueOf(site);
                    touched.add(a);
                }
            }
        }
        return touched;
    }
}
```

---

## 3. Finalizer — `AccountEnrichmentFinalizer.cls`

```apex
/**
 * AccountEnrichmentFinalizer — guaranteed post-execution handler for
 * AccountEnrichmentQueueable.
 *
 * Runs in its own Apex and Database transaction: "The Queueable job and the
 * Finalizer run in separate Apex and Database transactions." (apexdev L16297)
 * So this class's DML survives the parent's rollback.
 *
 * Governor limits here are the SYNCHRONOUS ones, except heap size, the
 * System.enqueueJob count and the @future count, which use asynchronous limits.
 * (apexdev L16298-16303)
 */
public with sharing class AccountEnrichmentFinalizer implements Finalizer {

    /**
     * The platform allows five consecutive re-enqueues from a finalizer and then
     * fails the call (apexdev L16293-16295, L16523). Stop at 3 so the dead-letter
     * row is written by our code rather than by the platform giving up.
     */
    @TestVisible private static final Integer MAX_ATTEMPTS = 3;

    // NOT transient. "Variables that are declared transient are ignored by
    // serialization and deserialization, and therefore don't persist in the
    // Transaction Finalizer." (apexdev L16360-16362)
    private final List<Id> accountIds;
    private final Integer attempt;
    private final List<String> trace = new List<String>();

    public AccountEnrichmentFinalizer(List<Id> accountIds, Integer attempt) {
        this.accountIds = accountIds == null ? new List<Id>() : accountIds;
        this.attempt    = attempt == null ? 0 : attempt;
    }

    /** Called by the Queueable while it runs; buffers a line into finalizer state. */
    public void note(String message) {
        trace.add(System.now().format('HH:mm:ss.SSS') + ' ' + message);
    }

    /**
     * The interface method. Signature is fixed:
     *   public void execute(System.FinalizerContext finalizerContext)  (apexrefguide L215587)
     */
    public void execute(FinalizerContext ctx) {
        // FinalizerContext has FOUR methods: getAsyncApexJobId, getRequestId,
        // getResult, getException (apexdev L16317, apexrefguide L215612-215614).
        // There is no getJobId() on FinalizerContext — that belongs to QueueableContext.
        handle(ctx.getResult(), ctx.getException(), ctx.getAsyncApexJobId(), ctx.getRequestId());
    }

    /**
     * Decision logic, split out so tests can drive every ParentJobResult branch
     * without needing the platform to schedule a finalizer.
     * Returns true when a retry was enqueued.
     */
    @TestVisible
    private Boolean handle(System.ParentJobResult result,
                           Exception cause,
                           Id parentJobId,
                           String requestId) {

        String source = 'AccountEnrichmentQueueable[' + parentJobId + ']';

        // "The enum takes these values: SUCCESS, UNHANDLED_EXCEPTION." (apexdev L16340)
        if (result == System.ParentJobResult.SUCCESS) {
            // getException() "returns ... null otherwise" on SUCCESS (apexrefguide L215654)
            ApplicationLogger.info(source, String.join(trace, ' | '));
            ApplicationLogger.flush();
            return false;
        }

        // UNHANDLED_EXCEPTION from here down.
        ApplicationLogger.error(source, cause);   // ERROR severity flushes immediately

        Integer nextAttempt = attempt + 1;
        if (nextAttempt < MAX_ATTEMPTS && isRetryable(cause)) {
            // THE one async job this finalizer may enqueue: "You can enqueue a single
            // asynchronous Apex job (Queueable, Future, or Batch) in the finalizer's
            // implementation of the execute method." (apexdev L16355-16356)
            System.enqueueJob(new AccountEnrichmentQueueable(accountIds, nextAttempt));
            return true;
        }

        writeDeadLetter(cause, parentJobId, requestId, nextAttempt);
        return false;
    }

    /**
     * UNVERIFIED (2026-09-05): the Apex Developer Guide does not classify which
     * exceptions are worth retrying from a finalizer. This allowlist is a design
     * choice — retry transport and row-lock failures, never validation failures,
     * because replaying a deterministic failure just burns the five-retry budget.
     */
    private static Boolean isRetryable(Exception cause) {
        if (cause == null) {
            return false;
        }
        if (cause instanceof CalloutException) {
            return true;
        }
        String message = cause.getMessage() == null ? '' : cause.getMessage();
        return message.contains('UNABLE_TO_LOCK_ROW');
    }

    private void writeDeadLetter(Exception cause, Id parentJobId, String requestId, Integer attemptNo) {
        Async_Job_Error__c row = new Async_Job_Error__c(
            Async_Apex_Job_Id__c = String.valueOf(parentJobId),
            Request_Id__c        = requestId,
            Job_Type__c          = 'AccountEnrichmentQueueable',
            Attempt__c           = attemptNo,
            Exception_Type__c    = cause == null ? 'Unknown' : cause.getTypeName(),
            Error_Message__c     = cause == null ? 'Unknown' : cause.getMessage().left(255),
            Stack_Trace__c       = cause == null ? null : cause.getStackTraceString(),
            Payload_JSON__c      = JSON.serialize(accountIds),
            Trace__c             = String.join(trace, '\n')
        );

        // Guard every DML in a finalizer. A runtime error here surfaces only as
        // "Error processing finalizer for queueable job id: {0}" in the log
        // (apexdev L16580) — there is no second finalizer to catch it.
        try {
            insert row;
        } catch (Exception dmlEx) {
            System.debug(LoggingLevel.ERROR,
                'AccountEnrichmentFinalizer: dead-letter insert failed for job '
                + parentJobId + ' — ' + dmlEx.getMessage());
        }
    }
}
```

**Fused variant.** Both worked examples in the guide put both interfaces on one class — `public class LoggingFinalizer implements Finalizer, Queueable` (apexdev L16373) — and attach with `System.attachFinalizer(this)` (apexdev L16393). Use that shape when the buffered log is the whole point; use the two-class shape above when the Finalizer is reused by more than one Queueable. Under the fused shape, `getJobId()` (from `QueueableContext`) and `getAsyncApexJobId()` (from `FinalizerContext`) are both in scope in the same file, which is the single commonest source of the wrong-method bug.

---

## 4. Class metadata — `*.cls-meta.xml`

One per class, alongside the `.cls`. `apiVersion` matches the guide this package is grounded in (Apex Developer Guide **Version 67.0, Summer '26**, `apexdev.txt` L2) and `templates/apex/ApplicationLogger.cls-meta.xml`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

At API v67.0 a class with no explicit sharing keyword runs `with sharing`: "In API version 67.0 and later, classes without an explicit sharing declaration run in with sharing mode" (apexdev L4961). Both classes above still declare it, per the guide's own recommendation to "always include an explicit sharing declaration on Apex classes that include database operations or SOQL queries" (apexdev L4873–4874).

---

## 5. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>AccountEnrichmentQueueable</members>
        <members>AccountEnrichmentFinalizer</members>
        <members>AccountEnrichmentFinalizerTest</members>
        <members>ApplicationLogger</members>
        <members>MockHttpResponseGenerator</members>
        <members>TestDataFactory</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Async_Job_Error__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Enrichment_API</members>
        <name>NamedCredential</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## 6. Test class — `AccountEnrichmentFinalizerTest.cls`

```apex
@IsTest
private class AccountEnrichmentFinalizerTest {

    private static List<Id> seedAccounts(Integer count) {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < count; i++) {
            accounts.add(new Account(Name = 'Enrich Co ' + i, BillingCountry = 'GB'));
        }
        insert accounts;
        return new List<Id>(new Map<Id, Account>(accounts).keySet());
    }

    /**
     * SUCCESS path, end to end.
     * "The system executes all asynchronous processes started in a test method
     * synchronously after the Test.stopTest statement." (apexdev L16124-16125)
     */
    @IsTest
    static void enqueuedJobSucceedsAndWritesNoDeadLetter() {
        List<Id> ids = seedAccounts(5);
        Test.setMock(HttpCalloutMock.class,
            new MockHttpResponseGenerator().withResponse(200, '{"accounts":{}}'));

        Test.startTest();
        System.enqueueJob(new AccountEnrichmentQueueable(ids));
        Test.stopTest();

        Assert.areEqual(0, [SELECT COUNT() FROM Async_Job_Error__c],
            'A successful run must not write a dead-letter row.');
    }

    /**
     * Bulk safety: 200 records must still be one query and one callout, so the
     * job must not approach the SOQL/callout ceilings.
     */
    @IsTest
    static void bulkChunkStaysWithinLimits() {
        List<Id> ids = seedAccounts(200);
        Test.setMock(HttpCalloutMock.class,
            new MockHttpResponseGenerator().withResponse(200, '{"accounts":{}}'));

        Test.startTest();
        System.enqueueJob(new AccountEnrichmentQueueable(ids));
        Test.stopTest();

        Assert.areEqual(0, [SELECT COUNT() FROM Async_Job_Error__c],
            '200-record chunk must complete without a dead-letter row.');
    }

    /**
     * UNHANDLED_EXCEPTION path.
     *
     * UNVERIFIED (2026-09-05): the Apex Developer Guide documents how to test a
     * Queueable (L16121-16146) but says nothing about whether an attached
     * Finalizer runs during Test.stopTest, nor how to make getResult() return
     * UNHANDLED_EXCEPTION in test context. Letting the Queueable actually throw
     * inside startTest/stopTest fails the test method itself, so the failure
     * branch is driven through the @TestVisible seam instead. Re-point this test
     * at the platform path only after confirming the behaviour in a scratch org.
     */
    @IsTest
    static void failureBelowCeilingEnqueuesExactlyOneRetry() {
        List<Id> ids = seedAccounts(3);
        AccountEnrichmentFinalizer f = new AccountEnrichmentFinalizer(ids, 0);
        f.note('attempt=0 size=3');

        Test.startTest();
        Boolean retried = f.handle(
            System.ParentJobResult.UNHANDLED_EXCEPTION,
            new CalloutException('Read timed out'),
            null,
            'REQ-TEST-1');
        Integer queued = Limits.getQueueableJobs();
        Test.stopTest();

        Assert.isTrue(retried, 'A retryable failure below the ceiling must re-enqueue.');
        Assert.areEqual(1, queued,
            'A finalizer may enqueue exactly one async job (apexdev L16355).');
        Assert.areEqual(0, [SELECT COUNT() FROM Async_Job_Error__c],
            'A retried attempt must not also write a dead-letter row.');
    }

    @IsTest
    static void failureAtCeilingWritesDeadLetterAndStops() {
        List<Id> ids = seedAccounts(2);
        AccountEnrichmentFinalizer f =
            new AccountEnrichmentFinalizer(ids, AccountEnrichmentFinalizer.MAX_ATTEMPTS - 1);
        f.note('attempt=exhausted');

        Test.startTest();
        Boolean retried = f.handle(
            System.ParentJobResult.UNHANDLED_EXCEPTION,
            new CalloutException('Read timed out'),
            null,
            'REQ-TEST-2');
        Test.stopTest();

        Assert.isFalse(retried, 'The attempt ceiling must stop the retry chain.');
        List<Async_Job_Error__c> rows = [
            SELECT Attempt__c, Exception_Type__c, Job_Type__c, Trace__c
            FROM Async_Job_Error__c
        ];
        Assert.areEqual(1, rows.size(), 'Exhausted retries must leave exactly one dead-letter row.');
        Assert.areEqual('AccountEnrichmentQueueable', rows[0].Job_Type__c);
        Assert.areEqual(AccountEnrichmentFinalizer.MAX_ATTEMPTS, (Integer) rows[0].Attempt__c);
        Assert.isTrue(rows[0].Trace__c.contains('attempt=exhausted'),
            'Buffered finalizer state must reach the dead-letter row.');
    }

    /** A deterministic failure must never consume the retry budget. */
    @IsTest
    static void nonRetryableFailureGoesStraightToDeadLetter() {
        List<Id> ids = seedAccounts(1);
        AccountEnrichmentFinalizer f = new AccountEnrichmentFinalizer(ids, 0);

        Test.startTest();
        Boolean retried = f.handle(
            System.ParentJobResult.UNHANDLED_EXCEPTION,
            new IllegalArgumentException('Required field missing: BillingCountry'),
            null,
            'REQ-TEST-3');
        Test.stopTest();

        Assert.isFalse(retried, 'A validation-shaped failure must not be retried.');
        Assert.areEqual(1, [SELECT COUNT() FROM Async_Job_Error__c]);
    }

    /** SUCCESS must be inert: no retry, no dead letter. */
    @IsTest
    static void successResultTakesNoCompensatingAction() {
        AccountEnrichmentFinalizer f = new AccountEnrichmentFinalizer(seedAccounts(1), 0);
        f.note('ok');

        Test.startTest();
        Boolean retried = f.handle(System.ParentJobResult.SUCCESS, null, null, 'REQ-TEST-4');
        Integer queued = Limits.getQueueableJobs();
        Test.stopTest();

        Assert.isFalse(retried, 'SUCCESS must not enqueue anything.');
        Assert.areEqual(0, queued, 'SUCCESS must not consume the enqueue slot.');
        Assert.areEqual(0, [SELECT COUNT() FROM Async_Job_Error__c]);
    }
}
```

`@IsTest` classes carry the same `-meta.xml` shown in section 4. Note the absence of `SeeAllData=true` — the test seeds its own Accounts, so it runs in any org.

---

## 7. Deploy and verify

```bash
# Static check before deploying — flags Finalizer-specific defects the compiler cannot see
python3 skills/apex/apex-transaction-finalizers/scripts/check_apex_transaction_finalizers.py \
    --manifest-dir force-app

# Deploy the manifest
sf project deploy start -x manifest/package.xml -o myOrg -w 30

# Run only this suite, with coverage, and fail the shell on a failed assertion
sf apex run test -o myOrg \
    -n AccountEnrichmentFinalizerTest \
    -r human -w 20 -c -y

# Retrieve back to confirm what actually landed
sf project retrieve start -x manifest/package.xml -o myOrg
```

**Runtime verification (after a real, non-test run).** Confirm the Finalizer fired and correlate it with the parent job:

```soql
SELECT Id, ApexClass.Name, Status, NumberOfErrors, ExtendedStatus,
       CreatedDate, CompletedDate, JobType
FROM AsyncApexJob
WHERE ApexClass.Name = 'AccountEnrichmentQueueable'
  AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

```soql
SELECT Async_Apex_Job_Id__c, Request_Id__c, Attempt__c,
       Exception_Type__c, Error_Message__c, CreatedDate
FROM Async_Job_Error__c
WHERE CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

Join the two on `AsyncApexJob.Id = Async_Job_Error__c.Async_Apex_Job_Id__c` — that ID comes from `getAsyncApexJobId()`, which the reference guide names as the method "To correlate the request with the AsyncApexJob table" (apexrefguide L215674). A dead-letter row with an `Attempt__c` equal to `MAX_ATTEMPTS` means the retry chain ended on your ceiling. An `AsyncApexJob` row with `Status = 'Failed'` and **no** matching dead-letter row means the Finalizer itself failed — check the debug log for `Error processing finalizer for queueable job id:` (apexdev L16580).

**Setup check:** Setup → Apex Jobs shows the parent Queueable. The Finalizer does not appear as a separate job row, because "Using a finalizer doesn't count as an extra execution against your daily Async Apex limit" (apexdev L16298); the retry it enqueues *does* appear as its own `AsyncApexJob` row.
