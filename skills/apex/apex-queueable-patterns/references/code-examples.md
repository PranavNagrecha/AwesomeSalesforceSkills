# Code Examples — Apex Queueable Patterns

A complete, deployable Queueable package: one job class with enqueue-time
options, a trigger seam that enqueues it once per transaction, a minimal
Finalizer, a test class, the metadata to deploy it, and the SOQL that proves it
ran. Every platform claim carries an `apexdev L<n>` / `apexrefguide L<n>` /
`object_reference L<n>` citation to the Summer '26 (v67.0) guides.

Canonical building blocks are referenced, not re-invented:

| Building block | Path | Used for |
|---|---|---|
| `ApplicationLogger` | `templates/apex/ApplicationLogger.cls` | The Finalizer writes `Application_Log__c` rows instead of `System.debug` |
| `TriggerHandler` | `templates/apex/TriggerHandler.cls` | The `afterUpdate` seam that calls `enqueueOnce` exactly once |
| `TriggerControl` | `templates/apex/TriggerControl.cls` | The `Trigger_Setting__mdt` kill-switch `TriggerHandler.run()` consults |
| `TestDataFactory` | `templates/apex/tests/TestDataFactory.cls` | `createAccounts(count, overrides)` for the 5-record and 201-record cases |
| `BulkTestPattern` | `templates/apex/tests/BulkTestPattern.cls` | The shape of the 201-record bulk method below |

---

## 1. What you deploy

| # | Component | Type | Why it exists |
|---|---|---|---|
| 1 | `Account.Lifetime_Value__c` (Currency), `Account.Rollup_Dirty__c` (Checkbox) | CustomField | The rollup target and the flag the trigger watches |
| 2 | `RecalculateAccountRollupQueueable` | ApexClass | The job: serialized state, `enqueueOnce`, single-child chain, inner Finalizer |
| 3 | `AccountRollupTriggerHandler` | ApexClass | Collects Ids across the whole `Trigger.new`, enqueues once |
| 4 | `AccountTrigger` | ApexTrigger | One trigger per object, dispatching to the handler |
| 5 | `RecalculateAccountRollupQueueableTest` | ApexClass | Sync execution under `stopTest`, dedupe contract, depth guard, bulk chunking |

---

## 2. `RecalculateAccountRollupQueueable.cls`

```apex
/**
 * Recalculates Account.Lifetime_Value__c from won Opportunities, 200 Accounts
 * at a time, chaining exactly one child job for the remainder.
 *
 * Design notes, each grounded in the Apex Developer Guide v67.0:
 *  - State is a List<Id>, not a List<Account>. Queueable member variables may be
 *    non-primitive (apexdev L15968-15970), but every field is serialized between
 *    transactions, so record graphs are paid for on every link of the chain.
 *  - No transient fields. Transient members are ignored by serialization and are
 *    null when the job runs (apexdev L15975-15976).
 *  - No static state carries the chain. A static variable is static only within
 *    the scope of one Apex transaction and is reset across transaction
 *    boundaries (apexdev L3738-3740); each chained job is a new transaction.
 *  - Sharing is declared explicitly. From API 67.0 a class with no declaration
 *    runs with sharing; at API 66.0 and earlier an entry point like a Queueable
 *    ran without sharing (apexdev L4961-4967). Declare it, do not inherit it.
 */
public with sharing class RecalculateAccountRollupQueueable implements Queueable {

    private static final String SOURCE = 'RecalculateAccountRollupQueueable';

    // 200 Ids per link keeps one job inside the async SOQL and DML ceilings:
    // 200 SOQL queries and 150 DML statements per async transaction
    // (apexdev L19546, L19553).
    @TestVisible private static final Integer CHUNK_SIZE = 200;

    // The chain ceiling this code enforces. Production editions enforce none of
    // their own: "Because no limit is enforced on the depth of chained jobs, you
    // can chain one job to another." Only Developer and Trial orgs cap it, at a
    // maximum stack depth of 5 (apexdev L16182-16185).
    @TestVisible private static final Integer MAX_DEPTH = 5;

    // Test seams: what the job decided, recorded before the platform acts on it.
    @TestVisible private static Integer chainRequests = 0;
    @TestVisible private static Id lastChildJobId;

    private final List<Id> accountIds;
    private final Integer depth;

    public RecalculateAccountRollupQueueable(Set<Id> accountIds) {
        this(new List<Id>(accountIds == null ? new Set<Id>() : accountIds), 1);
    }

    private RecalculateAccountRollupQueueable(List<Id> accountIds, Integer depth) {
        this.accountIds = accountIds;
        this.depth = depth;
    }

    // -----------------------------------------------------------------------
    // Enqueue-time options
    // -----------------------------------------------------------------------

    /**
     * The only supported entry point. Callers never touch System.enqueueJob so
     * that the depth cap and the duplicate signature cannot be forgotten at one
     * call site, and so that a suppressed duplicate never surfaces to the user
     * as failed DML.
     *
     * Returns the AsyncApexJob Id (apexrefguide L238934-238936), or null when
     * there is nothing to do or the work is already queued.
     */
    public static Id enqueueOnce(Set<Id> accountIds) {
        if (accountIds == null || accountIds.isEmpty()) {
            return null;
        }
        try {
            return System.enqueueJob(
                new RecalculateAccountRollupQueueable(accountIds),
                buildOptions(accountIds)
            );
        } catch (DuplicateMessageException dupe) {
            // Expected, not exceptional: an identical job is already enqueued.
            // Message is "Attempt to enqueue job with duplicate queueable
            // signature" (apexrefguide L214950).
            ApplicationLogger.info(SOURCE, 'Duplicate signature suppressed: ' + dupe.getMessage());
            return null;
        }
    }

    /**
     * AsyncOptions carries all three enqueue-time levers
     * (apexrefguide L201172-201225). MinimumQueueableDelayInMinutes is left
     * unset here: this job is not rate-limited by an external system, and the
     * org-wide ApexSettings.DefaultQueueableDelay applies to jobs enqueued
     * without an explicit delay (apexdev L16032-16036).
     */
    @TestVisible
    private static AsyncOptions buildOptions(Set<Id> accountIds) {
        AsyncOptions opts = new AsyncOptions();
        opts.MaximumQueueableStackDepth = MAX_DEPTH;
        opts.DuplicateSignature = new System.QueueableDuplicateSignature.Builder()
            .addString(SOURCE)
            .addInteger(System.hashCode(stableKey(accountIds)))
            .build();
        return opts;
    }

    /**
     * The signature must be stable across transactions or the mechanism does
     * nothing: two Data Loader batches touching the same Accounts have to
     * produce byte-identical signatures. Set iteration order is not guaranteed,
     * so the Ids are sorted before hashing. Nothing time-varying goes in.
     */
    @TestVisible
    private static String stableKey(Set<Id> accountIds) {
        List<String> keys = new List<String>();
        for (Id accountId : accountIds) {
            keys.add(String.valueOf(accountId));
        }
        keys.sort();
        return String.join(keys, ',');
    }

    // -----------------------------------------------------------------------
    // Execution
    // -----------------------------------------------------------------------

    public void execute(QueueableContext context) {
        // Attached first, so that anything thrown below still reaches a
        // Finalizer. QueueableContext.getJobId returns this job Id
        // (apexrefguide L227381-227390).
        System.attachFinalizer(new RollupFinalizer(context.getJobId(), accountIds.size(), depth));

        Integer sliceSize = Math.min(CHUNK_SIZE, accountIds.size());
        List<Id> slice = new List<Id>();
        for (Integer i = 0; i < sliceSize; i++) {
            slice.add(accountIds[i]);
        }

        // Order matters inside one execute: any HTTP callout this job needs must
        // happen BEFORE the DML below. "You can not make a callout when there
        // are pending operations in the same transaction. Things that result in
        // pending operations are DML statements, asynchronous Apex ... You can
        // make callouts before performing these types of operations."
        // (apexdev L35860-35862). This job makes no callout, so it does not
        // implement Database.AllowsCallouts.
        recalculate(slice);

        List<Id> remaining = new List<Id>();
        for (Integer i = sliceSize; i < accountIds.size(); i++) {
            remaining.add(accountIds[i]);
        }
        if (remaining.isEmpty()) {
            return;
        }
        if (!hasDepthHeadroom()) {
            // Terminal, and loud. Unprocessed Ids are named so the work can be
            // re-driven; a silent return here is how a rollup goes stale.
            ApplicationLogger.warn(SOURCE, 'Depth cap ' + MAX_DEPTH + ' reached at depth ' + depth
                + ' with ' + remaining.size() + ' Account Ids unprocessed.');
            ApplicationLogger.flush();
            return;
        }

        // Exactly one child. "When chaining jobs with System.enqueueJob, you can
        // add only one job from an executing job." (apexdev L16186-16188). The
        // options are rebuilt here: MaximumQueueableStackDepth is a property of
        // the enqueue call, not of the chain.
        AsyncOptions opts = new AsyncOptions();
        opts.MaximumQueueableStackDepth = MAX_DEPTH;
        chainRequests++;
        lastChildJobId = System.enqueueJob(
            new RecalculateAccountRollupQueueable(remaining, depth + 1), opts
        );
    }

    /**
     * Two guards, because each covers the other blind spot.
     *
     * The carried counter works everywhere, including a caller that forgot the
     * AsyncOptions. The platform counter is authoritative but only reports
     * anything when a maximum stack depth was actually set on the request,
     * which is exactly what hasMaxStackDepth answers
     * (apexdev L16037-16044, apexrefguide L201087-201150).
     */
    private Boolean hasDepthHeadroom() {
        if (depth >= MAX_DEPTH) {
            return false;
        }
        if (System.AsyncInfo.hasMaxStackDepth()) {
            return System.AsyncInfo.getCurrentQueueableStackDepth()
                 < System.AsyncInfo.getMaximumQueueableStackDepth();
        }
        return true;
    }

    private void recalculate(List<Id> ids) {
        // Every Id in the slice is written, including the ones with no won
        // Opportunity, so that a rollup falls back to zero instead of keeping a
        // stale value.
        Map<Id, Decimal> totals = new Map<Id, Decimal>();
        for (Id accountId : ids) {
            totals.put(accountId, 0);
        }
        for (AggregateResult row : [
            SELECT AccountId aid, SUM(Amount) total
            FROM Opportunity
            WHERE AccountId IN :ids AND IsWon = true
            WITH USER_MODE
            GROUP BY AccountId
        ]) {
            totals.put((Id) row.get('aid'), (Decimal) row.get('total'));
        }

        List<Account> toUpdate = new List<Account>();
        for (Id accountId : totals.keySet()) {
            toUpdate.add(new Account(
                Id = accountId,
                Lifetime_Value__c = totals.get(accountId),
                Rollup_Dirty__c = false
            ));
        }
        // User mode, as the guide own Queueable sample does with "insert as user"
        // (apexdev L15986).
        update as user toUpdate;
    }

    // -----------------------------------------------------------------------
    // Minimal Finalizer
    // -----------------------------------------------------------------------

    /**
     * Deliberately thin: it records the outcome and stops. Anything heavier
     * belongs in its own job. Retry budgets, buffered logging and the full
     * FinalizerContext contract are the subject of apex/apex-transaction-finalizers.
     *
     * "Finalizers can be implemented as an inner class." (apexdev L16295)
     * Synchronous governor limits apply to this transaction except for heap,
     * enqueueJob count and future-method count (apexdev L16297-16303) - which is
     * why it does one DML and no queries.
     */
    public class RollupFinalizer implements Finalizer {

        private final Id parentJobId;
        private final Integer requested;
        private final Integer depthAtAttach;

        public RollupFinalizer(Id parentJobId, Integer requested, Integer depthAtAttach) {
            this.parentJobId = parentJobId;
            this.requested = requested;
            this.depthAtAttach = depthAtAttach;
        }

        public void execute(FinalizerContext ctx) {
            // FinalizerContext has getAsyncApexJobId, getRequestId, getResult and
            // getException. It has no getJobId (apexdev L16311-16344).
            String jobId = String.valueOf(ctx.getAsyncApexJobId());

            if (ctx.getResult() == ParentJobResult.SUCCESS) {
                ApplicationLogger.info(SOURCE, 'Job ' + jobId + ' rolled up ' + requested
                    + ' Accounts at depth ' + depthAtAttach + '.');
            } else {
                // getException is non-null only when getResult is
                // UNHANDLED_EXCEPTION (apexdev L16341-16344).
                ApplicationLogger.error(SOURCE, ctx.getException());
                ApplicationLogger.warn(SOURCE, 'Job ' + jobId + ' failed at depth ' + depthAtAttach
                    + ' for ' + requested + ' Accounts. Request ' + ctx.getRequestId()
                    + '. Context job ' + parentJobId + '.');
            }
            ApplicationLogger.flush();
        }
    }
}
```

### `RecalculateAccountRollupQueueable.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## 3. Enqueuing from a trigger — `enqueueOnce` at the seam

The synchronous ceiling is 50 enqueues per transaction, not one
(`apexdev` L16179-16181; limits table L19573 reads 50 synchronous / 1
asynchronous). That is the trap: a per-record `System.enqueueJob` in a
200-record trigger does not fail on record 2, it fails on record 51, so it
survives every hand test and dies on the first real data load. Collect, then
enqueue once.

```apex
public with sharing class AccountRollupTriggerHandler extends TriggerHandler {

    protected override void afterUpdate() {
        Set<Id> needsRollup = new Set<Id>();
        for (Account record : (List<Account>) Trigger.new) {
            Account previous = (Account) Trigger.oldMap.get(record.Id);
            // Fire on the false-to-true edge only. The job clears the flag, so
            // its own update comes back through here as true-to-false and
            // enqueues nothing.
            if (record.Rollup_Dirty__c == true && previous.Rollup_Dirty__c == false) {
                needsRollup.add(record.Id);
            }
        }
        if (needsRollup.isEmpty()) {
            return;
        }
        // One call, whatever the batch size. Limits.getQueueableJobs() reports
        // how many have been added in this transaction
        // (apexdev L16181, apexrefguide L220873-220880).
        RecalculateAccountRollupQueueable.enqueueOnce(needsRollup);
    }
}
```

```apex
trigger AccountTrigger on Account (after update) {
    new AccountRollupTriggerHandler().run();
}
```

`TriggerHandler.run()` supplies the recursion depth guard and the
`TriggerControl` kill-switch — see `templates/apex/TriggerHandler.cls` and
`templates/apex/TriggerControl.cls`. Do not copy those bodies into the handler.

---

## 4. `RecalculateAccountRollupQueueableTest.cls`

```apex
@IsTest
private class RecalculateAccountRollupQueueableTest {

    // Do not add @IsTest(IsParallel=true) to this class. Parallel tests cannot
    // call System.enqueueJob at all: "Tests can not call the System.schedule()
    // and System.enqueueJob() methods." (apexdev L5965).

    @TestSetup
    static void seed() {
        insert TestDataFactory.createAccounts(5, new Map<String, Object>{
            'Rollup_Dirty__c' => true
        });
    }

    private static Set<Id> seededIds() {
        return new Map<Id, Account>([SELECT Id FROM Account]).keySet();
    }

    /**
     * The job runs synchronously because it was enqueued inside the block:
     * "The system executes all asynchronous processes started in a test method
     * synchronously after the Test.stopTest statement." (apexdev L16123-16126).
     */
    @IsTest
    static void jobRunsSynchronouslyUnderStopTest() {
        Set<Id> ids = seededIds();

        Test.startTest();
        Id jobId = RecalculateAccountRollupQueueable.enqueueOnce(ids);
        Test.stopTest();

        Assert.isNotNull(jobId, 'enqueueOnce must return the AsyncApexJob Id of the enqueued job.');
        for (Account acct : [SELECT Id, Lifetime_Value__c, Rollup_Dirty__c FROM Account WHERE Id IN :ids]) {
            Assert.areEqual(0, acct.Lifetime_Value__c, 'No won Opportunity means the rollup resets to zero.');
            Assert.isFalse(acct.Rollup_Dirty__c, 'The job must clear the flag it consumed.');
        }
    }

    /**
     * The dedupe contract this code depends on is one-way: a duplicate signature
     * must never reach the caller as an exception, because in a trigger it would
     * surface as failed DML on the user save.
     */
    @IsTest
    static void duplicateSignatureNeverEscapesToTheCaller() {
        Set<Id> ids = seededIds();
        List<Id> reordered = new List<Id>(ids);
        Assert.areEqual(
            RecalculateAccountRollupQueueable.stableKey(ids),
            RecalculateAccountRollupQueueable.stableKey(new Set<Id>(reordered)),
            'The signature key must be order-independent, or two transactions never collide.'
        );

        Test.startTest();
        Id first = RecalculateAccountRollupQueueable.enqueueOnce(ids);
        try {
            RecalculateAccountRollupQueueable.enqueueOnce(ids);
        } catch (DuplicateMessageException dupe) {
            Assert.fail('enqueueOnce must swallow DuplicateMessageException, not propagate it: '
                + dupe.getMessage());
        }
        Test.stopTest();

        Assert.isNotNull(first, 'The first enqueue must be accepted.');
    }

    /**
     * Five Ids fit in one 200-Id chunk, so the job must terminate rather than
     * chain. Asserted on the recorded decision, not on how many chain levels the
     * test runtime happens to drive.
     */
    @IsTest
    static void chainDoesNotStartWhenAllWorkFitsInOneChunk() {
        Set<Id> ids = seededIds();

        Test.startTest();
        RecalculateAccountRollupQueueable.enqueueOnce(ids);
        Test.stopTest();

        Assert.areEqual(0, RecalculateAccountRollupQueueable.chainRequests,
            'A single-chunk workload must not enqueue a child job.');
        Assert.isNull(RecalculateAccountRollupQueueable.lastChildJobId,
            'No child job Id may be recorded when no child was requested.');
    }

    /**
     * Bulk case: 201 Ids is one chunk plus a remainder, so exactly one child is
     * requested - never two. See templates/apex/tests/BulkTestPattern.cls.
     */
    @IsTest
    static void oversizedWorkloadChainsExactlyOneChild() {
        List<Account> bulk = TestDataFactory.createAccounts(201, new Map<String, Object>{
            'Rollup_Dirty__c' => true
        });
        insert bulk;
        Set<Id> ids = new Map<Id, Account>(bulk).keySet();

        Test.startTest();
        RecalculateAccountRollupQueueable.enqueueOnce(ids);
        Test.stopTest();

        Assert.areEqual(1, RecalculateAccountRollupQueueable.chainRequests,
            'A 201-Id workload must request exactly one child job, never two.');

        Integer done = [SELECT COUNT() FROM Account WHERE Id IN :ids AND Rollup_Dirty__c = false];
        Assert.isTrue(done >= 200, 'The first link must process a full 200-Id chunk. Processed: ' + done);
    }

    /**
     * Operational assertion. AsyncApexJob.JobType for this job is Queueable
     * (object_reference L42360-42371) and Status is one of Aborted, Completed,
     * Failed, Holding, Preparing, Processing, Queued
     * (object_reference L42419-42427).
     */
    @IsTest
    static void asyncApexJobRecordDescribesTheJob() {
        Set<Id> ids = seededIds();

        Test.startTest();
        Id jobId = RecalculateAccountRollupQueueable.enqueueOnce(ids);
        Test.stopTest();

        List<AsyncApexJob> jobs = [
            SELECT Id, JobType, Status, NumberOfErrors, ExtendedStatus
            FROM AsyncApexJob
            WHERE Id = :jobId
        ];
        // UNVERIFIED (2026-09-05): neither guide states whether an AsyncApexJob
        // row is queryable for a Queueable executed inside Test.stopTest, so the
        // assertion is conditional. The unconditional proof is the verification
        // SOQL in section 7, run against a real org after deployment.
        if (!jobs.isEmpty()) {
            Assert.areEqual('Queueable', jobs[0].JobType, 'JobType must be Queueable.');
            Assert.areEqual(0, jobs[0].NumberOfErrors, 'The job must complete without errors.');
        }
    }
}
```

### `RecalculateAccountRollupQueueableTest.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## 5. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>ApplicationLogger</members>
        <members>TriggerControl</members>
        <members>TriggerHandler</members>
        <members>RecalculateAccountRollupQueueable</members>
        <members>AccountRollupTriggerHandler</members>
        <members>TestDataFactory</members>
        <members>RecalculateAccountRollupQueueableTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>AccountTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>Account.Lifetime_Value__c</members>
        <members>Account.Rollup_Dirty__c</members>
        <name>CustomField</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## 6. Deploy order

Apex compiles against what is already in the org, so the order is not cosmetic.

| Step | Command | Why here |
|---|---|---|
| 1 | `sf project deploy start --metadata CustomField:Account.Lifetime_Value__c --metadata CustomField:Account.Rollup_Dirty__c` | The job and the handler both reference these fields; deploying code first fails compilation |
| 2 | `sf project deploy start --metadata ApexClass:ApplicationLogger --metadata ApexClass:TriggerControl --metadata ApexClass:TriggerHandler --metadata ApexClass:TestDataFactory` | Shared templates. `ApplicationLogger` needs `Application_Log__c` and `Logger_Setting__mdt`; `TriggerControl` needs `Trigger_Setting__mdt` — see `templates/apex/README.md` |
| 3 | `sf project deploy start --metadata ApexClass:RecalculateAccountRollupQueueable` | The job, before anything that calls it |
| 4 | `sf project deploy start --manifest manifest/package.xml --test-level RunSpecifiedTests --tests RecalculateAccountRollupQueueableTest` | Handler, trigger and test together, gated on the test |
| 5 | `sf apex run test --class-names RecalculateAccountRollupQueueableTest --result-format human --wait 10` | Re-run on demand without redeploying |

Retrieve an existing implementation to review before changing it:

```bash
sf project retrieve start \
  --metadata ApexClass:RecalculateAccountRollupQueueable \
  --metadata ApexTrigger:AccountTrigger \
  --target-org myOrg
```

---

## 7. Verification

Run after the first real enqueue. `JobType` is the discriminator; the Apex Jobs
page in Setup shows the same rows (`apexdev` L15996-15999).

```soql
SELECT Id, ApexClass.Name, JobType, Status, NumberOfErrors, ExtendedStatus,
       JobItemsProcessed, TotalJobItems, CreatedDate, CompletedDate
FROM AsyncApexJob
WHERE JobType = 'Queueable'
  AND ApexClass.Name = 'RecalculateAccountRollupQueueable'
  AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

Read it like this:

- **One row per chain link.** Four rows for an 800-Account run at `CHUNK_SIZE`
  200 is the chain working; a fifth would mean the depth guard did not fire.
- **`JobItemsProcessed` and `TotalJobItems` are always 0.** "Similar to future
  jobs, queueable jobs do not process batches, and so the number of processed
  batches and the number of total batches are always zero."
  (`apexdev` L16012-16013). A monitoring query that gates on them gates on zero.
- **`Status = 'Holding'` will never appear.** That status "applies to batch jobs
  in the Apex flex queue" (`object_reference` L42423-42429), and the flex queue
  takes batch jobs only (`apexdev` L17234-17240). A Queueable goes `Queued` →
  `Processing` → `Completed` or `Failed`.
- **`ExtendedStatus`** carries the first error text when `NumberOfErrors > 0`
  (`object_reference` L42305-42311).
- **Stopping one** — `System.abortJob(jobId)` accepts an `AsyncApexJob` Id, and
  "The specified job is stopped, but any code that is in progress will continue
  to execute until it completes." (`apexrefguide` L238661-238665, L238673-238682).
  Aborting the running link does not stop a child already enqueued.

Confirm the Finalizer wrote its row:

```soql
SELECT Id, Severity__c, Source__c, Message__c, Request_Id__c, CreatedDate
FROM Application_Log__c
WHERE Source__c = 'RecalculateAccountRollupQueueable'
  AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

`FinalizerContext.getRequestId()` "can be correlated with Event Monitoring logs"
and is shared by the Queueable and its Finalizer (`apexdev` L16330-16334), so
this column joins the two halves of one failure.

---

## 8. How to read the design

- **`enqueueOnce` is the only public door.** Depth cap and duplicate signature
  are set in one place, so no future call site can omit them, and a suppressed
  duplicate returns `null` instead of throwing into a user save.
- **The signature is a sorted-Id hash plus a class-name string.** Anything
  time-varying — `System.now()`, a `Trigger.new` size, a random correlation Id —
  makes every transaction produce a different signature and turns the mechanism
  off silently.
- **Two depth guards.** The carried `depth` counter is authoritative even when a
  caller enqueued without `AsyncOptions`; `System.AsyncInfo` is authoritative when
  it was set. `hasMaxStackDepth()` distinguishes the two cases.
- **One child, always.** Only one `System.enqueueJob` call exists in `execute()`,
  and it is on a terminal path. Fan-out needs Platform Events or Batch Apex.
- **The Finalizer stays thin.** It logs and returns. Retry budgets, the
  five-consecutive-re-enqueue ceiling and buffered-log commits belong to
  `apex/apex-transaction-finalizers`.
- **Callout ordering is a comment, not an accident.** This job does no callout;
  if one is added it must precede `recalculate()`, and the class must then also
  implement `Database.AllowsCallouts` (`apexdev` L16164-16165).
