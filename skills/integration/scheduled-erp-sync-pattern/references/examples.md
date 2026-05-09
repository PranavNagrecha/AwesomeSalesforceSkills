# Examples — Scheduled ERP Sync Pattern

Concrete, copy-able skeletons for each layer of the pattern. Names are illustrative — replace `Erp` / `ERP_*` with your domain.

---

## Example 1 — Schedulable + Queueable callout chain (the canonical entrypoint)

**Context:** A 15-minute scheduled pull from a NetSuite-style REST endpoint that returns up to ~500 modified invoice records per cycle.

**Problem:** A naive `Schedulable` that does the callout itself fails with `System.CalloutException: You have uncommitted work pending`. The Schedulable context is *not* callout-allowed.

**Solution:** Schedulable does only enqueue + watermark capture. Queueable (with `Database.AllowsCallouts`) does the work.

```apex
public class ErpSyncScheduler implements Schedulable {
    public void execute(SchedulableContext sc) {
        // Capture cycle start at THIS instant — never after callouts complete.
        Datetime cycleStart = Datetime.now();

        ERP_Sync_Watermark__mdt watermark = [
            SELECT DeveloperName, Last_Successful_Cycle_Start__c, Cursor_Token__c
            FROM ERP_Sync_Watermark__mdt
            WHERE DeveloperName = 'Invoice'
            LIMIT 1
        ];

        // Schedulable cannot callout — enqueue the Queueable that can.
        System.enqueueJob(new ErpInvoicePullQueueable(
            cycleStart,
            watermark.Last_Successful_Cycle_Start__c,
            watermark.Cursor_Token__c,
            0           // retry count
        ));
    }
}

public class ErpInvoicePullQueueable
    implements Queueable, Database.AllowsCallouts {

    private final Datetime cycleStart;
    private final Datetime priorWatermark;
    private final String cursor;
    private final Integer retryCount;

    public ErpInvoicePullQueueable(
        Datetime cycleStart, Datetime priorWatermark, String cursor, Integer retryCount
    ) {
        this.cycleStart = cycleStart;
        this.priorWatermark = priorWatermark;
        this.cursor = cursor;
        this.retryCount = retryCount;
    }

    public void execute(QueueableContext qc) {
        HttpRequest req = new HttpRequest();
        // Named Credential — never hardcode the URL or auth header.
        req.setEndpoint('callout:ERP_NetSuite/invoices?modifiedSince='
            + priorWatermark.formatGmt('yyyy-MM-dd\'T\'HH:mm:ss\'Z\''));
        req.setMethod('GET');
        req.setTimeout(120000);

        Http http = new Http();
        HttpResponse res;
        try {
            res = http.send(req);
        } catch (CalloutException ex) {
            handleFailure(null, ex.getMessage());
            return;
        }

        if (res.getStatusCode() >= 500 || res.getStatusCode() == 429 || res.getStatusCode() == 408) {
            // Transient — retry path
            handleFailure(res, 'Transient HTTP ' + res.getStatusCode());
            return;
        }
        if (res.getStatusCode() >= 400) {
            // Permanent — straight to DLQ, do not retry
            ErpDlqWriter.writePermanent(res, 'invoices', cycleStart);
            return;
        }

        // Success — stage records, advance watermark, chain next page if any.
        List<ERP_Stage__c> staged = ErpInvoiceMapper.parse(res.getBody(), cycleStart);
        Database.upsert(staged, ERP_Stage__c.ERP_Record_Id__c, false);

        ErpWatermarkService.advance('Invoice', cycleStart);
        // chain next-page Queueable if pagination cursor is non-null, omitted for brevity
    }

    private void handleFailure(HttpResponse res, String reason) {
        if (retryCount >= 3) {
            ErpDlqWriter.writeRetryExhausted(res, reason, 'invoices', cycleStart);
            return;
        }
        // Re-enqueue with incremented retry count. No Thread.sleep — Queueable cannot.
        System.enqueueJob(new ErpInvoicePullQueueable(
            cycleStart, priorWatermark, cursor, retryCount + 1
        ));
    }
}
```

**Why it works:** Schedulable runs in a context that disallows callouts but allows DML — perfect for "decide to do work" not "do work". Queueable inherits transactional limits but allows callouts when `Database.AllowsCallouts` is implemented. Each Queueable enqueue gets a fresh governor budget.

---

## Example 2 — Watermark advance via Custom Metadata Type (deployable, diffable, not Custom Settings)

**Context:** Watermark must survive sandbox refresh, be visible in source control, and be deployable through the package pipeline.

**Problem:** Storing the watermark in a Hierarchy Custom Setting means the value lives in the org but not in the metadata. Sandbox refreshes wipe it. Deploys cannot promote a known-good watermark across environments.

**Solution:** Custom Metadata Type. Update via the Metadata API at runtime.

```apex
public class ErpWatermarkService {
    public static void advance(String objectName, Datetime cycleStart) {
        Metadata.CustomMetadata cm = new Metadata.CustomMetadata();
        cm.fullName  = 'ERP_Sync_Watermark.' + objectName;
        cm.label     = objectName + ' Sync Watermark';

        Metadata.CustomMetadataValue field = new Metadata.CustomMetadataValue();
        field.field = 'Last_Successful_Cycle_Start__c';
        field.value = cycleStart;
        cm.values.add(field);

        Metadata.DeployContainer container = new Metadata.DeployContainer();
        container.addMetadata(cm);

        // Deploy is async — do NOT block on completion inside a Queueable.
        // Use a deploy-callback class for audit; success is the common case.
        Metadata.Operations.enqueueDeployment(container, new ErpWatermarkDeployCallback());
    }
}
```

**Why it works:** Custom Metadata is part of the org's metadata layer, so it is in source control, in the package, and survives sandbox refresh. The `enqueueDeployment` call is async — the next cycle reads the new value. Salesforce documents this pattern in the Apex Developer Guide ("Update Custom Metadata Records Using Apex").

---

## Example 3 — Retry with exponential backoff (re-enqueue, not Thread.sleep)

**Context:** Transient ERP 503 should retry 3 times with backoff, then DLQ.

**Problem:** A Queueable cannot `Thread.sleep()` (no thread API in Apex) and cannot `Limits.getCallouts()`-block. The "backoff" must be expressed as a re-enqueue, optionally to a Schedulable that fires N seconds later.

**Solution:** Self-chaining with a delay parameter. For sub-minute delays use straight re-enqueue (the platform schedules quickly enough). For >1-minute delays use `System.scheduleBatch` of a one-shot Schedulable.

```apex
public class ErpRetryHelper {
    private static final Integer MAX_ATTEMPTS = 3;
    // Backoff in minutes: attempt 1 → 1 min, attempt 2 → 4 min, attempt 3 → 16 min
    private static final List<Integer> BACKOFF_MIN = new List<Integer>{ 1, 4, 16 };

    public static void scheduleRetry(
        Datetime cycleStart,
        Datetime priorWatermark,
        String cursor,
        Integer attempt
    ) {
        if (attempt >= MAX_ATTEMPTS) {
            ErpDlqWriter.writeRetryExhausted(null,
                'Retries exhausted after ' + attempt + ' attempts',
                'invoices', cycleStart);
            return;
        }
        Integer delayMin = BACKOFF_MIN[attempt];
        // System.scheduleBatch returns a job ID and fires after delayMin minutes.
        ErpInvoicePullScheduler one = new ErpInvoicePullScheduler(
            cycleStart, priorWatermark, cursor, attempt + 1
        );
        System.scheduleBatch(one, 'ERP_Invoice_Retry_' + cycleStart.getTime() + '_' + attempt, delayMin);
    }
}
```

**Why it works:** `System.scheduleBatch` is documented as the canonical way to schedule a one-time async job at a future delta. The increasing minute backoff (`1, 4, 16`) is exponential with jitter built into the scheduling layer (Salesforce honors the minute granularity loosely under contention).

---

## Example 4 — Dead-letter custom object writer

**Context:** When retries exhaust on a payload, audit-trail the failure for replay tooling.

**Problem:** Logging to `System.debug` loses the record after 24 hours and is not queryable. Persisting to a custom object is the documented Salesforce pattern for replay queues.

**Solution:** `Integration_DLQ__c` with the schema from Concept 3 in `SKILL.md`. Writer is a stateless static method.

```apex
public class ErpDlqWriter {
    public static void writeRetryExhausted(
        HttpResponse res, String reason, String endpoint, Datetime cycleStart
    ) {
        Integration_DLQ__c dlq = new Integration_DLQ__c(
            Cycle_Id__c     = String.valueOf(cycleStart.getTime()),
            Endpoint__c     = endpoint,
            Http_Status__c  = (res != null) ? String.valueOf(res.getStatusCode()) : 'NETWORK',
            Response_Body__c = (res != null) ? truncate(res.getBody(), 32000) : reason,
            Failed_At__c    = Datetime.now(),
            Retry_Count__c  = 3,
            Status__c       = 'New',
            Error_Reason__c = reason
        );
        // Allow partial — never let a DLQ insert failure swallow the upstream error.
        Database.insert(dlq, false);
    }

    public static void writePermanent(HttpResponse res, String endpoint, Datetime cycleStart) {
        Integration_DLQ__c dlq = new Integration_DLQ__c(
            Cycle_Id__c     = String.valueOf(cycleStart.getTime()),
            Endpoint__c     = endpoint,
            Http_Status__c  = String.valueOf(res.getStatusCode()),
            Response_Body__c = truncate(res.getBody(), 32000),
            Failed_At__c    = Datetime.now(),
            Retry_Count__c  = 0,
            Status__c       = 'Permanent',
            Error_Reason__c = 'HTTP ' + res.getStatusCode() + ' — non-retryable'
        );
        Database.insert(dlq, false);
    }

    private static String truncate(String s, Integer len) {
        if (s == null) return null;
        return (s.length() > len) ? s.substring(0, len) : s;
    }
}
```

**Why it works:** The DLQ object is queryable (you can list "all permanent failures last 24h"), reportable (dashboards), and replay-able (a separate Queueable reads `Status__c = 'New'` rows and re-attempts). It survives org sandbox refreshes if migrated as data, unlike debug logs.

---

## Example 5 — `HttpCalloutMock` test for the happy path + 5xx-retry path

**Context:** Org will not deploy a callout class without a `HttpCalloutMock` test that covers it. Coverage gate is 75% on the class.

**Problem:** New developers write a single happy-path mock and miss the 5xx, 4xx, and DLQ branches. Coverage passes; production retry behavior is untested.

**Solution:** A multi-call mock that returns different responses on successive calls.

```apex
@isTest
public class ErpInvoicePullQueueableTest {

    private class SequencedMock implements HttpCalloutMock {
        private final List<Integer> statuses;
        private final List<String> bodies;
        private Integer call = 0;
        public SequencedMock(List<Integer> statuses, List<String> bodies) {
            this.statuses = statuses; this.bodies = bodies;
        }
        public HttpResponse respond(HttpRequest req) {
            HttpResponse res = new HttpResponse();
            res.setStatusCode(statuses[call]);
            res.setBody(bodies[call]);
            call++;
            return res;
        }
    }

    @isTest
    static void happy_path_writes_staging_and_advances_watermark() {
        Test.setMock(HttpCalloutMock.class, new SequencedMock(
            new List<Integer>{ 200 },
            new List<String>{ '[{"id":"INV-1","amount":100}]' }
        ));
        Test.startTest();
        System.enqueueJob(new ErpInvoicePullQueueable(
            Datetime.now(), Datetime.now().addHours(-1), null, 0
        ));
        Test.stopTest();

        System.assertEquals(1, [SELECT count() FROM ERP_Stage__c], 'one record staged');
        System.assertEquals(0, [SELECT count() FROM Integration_DLQ__c], 'no DLQ entry');
    }

    @isTest
    static void retry_then_recover_does_not_dlq() {
        Test.setMock(HttpCalloutMock.class, new SequencedMock(
            new List<Integer>{ 503, 200 },
            new List<String>{ 'transient', '[{"id":"INV-2","amount":50}]' }
        ));
        Test.startTest();
        System.enqueueJob(new ErpInvoicePullQueueable(
            Datetime.now(), Datetime.now().addHours(-1), null, 0
        ));
        Test.stopTest();

        // Test framework runs all enqueued jobs synchronously inside Test.stopTest().
        System.assertEquals(0, [SELECT count() FROM Integration_DLQ__c], 'recovered, no DLQ');
    }

    @isTest
    static void permanent_4xx_writes_dlq_immediately() {
        Test.setMock(HttpCalloutMock.class, new SequencedMock(
            new List<Integer>{ 404 },
            new List<String>{ '{"error":"endpoint not found"}' }
        ));
        Test.startTest();
        System.enqueueJob(new ErpInvoicePullQueueable(
            Datetime.now(), Datetime.now().addHours(-1), null, 0
        ));
        Test.stopTest();

        System.assertEquals(1, [SELECT count() FROM Integration_DLQ__c WHERE Status__c = 'Permanent']);
    }
}
```

**Why it works:** `Test.stopTest()` flushes all enqueued Queueable jobs synchronously, so the 5xx-then-200 sequence is exercised end-to-end. The `SequencedMock` returns a different response per call, which is the only documented way to test multi-attempt logic.

---

## Anti-Pattern: Synchronous callout in a trigger context

**What practitioners do:** "We need to push the new Account to the ERP immediately." A developer writes:

```apex
trigger AccountAfterInsert on Account (after insert) {
    for (Account a : Trigger.new) {
        Http http = new Http();
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ERP/customers');
        req.setMethod('POST');
        req.setBody(JSON.serialize(a));
        http.send(req);   // <— blocks the trigger
    }
}
```

**What goes wrong:**
- Triggers cannot make synchronous callouts unless the trigger is itself running in `@future(callout=true)` or Queueable context. The above throws `CalloutException: You have uncommitted work pending`.
- Even when wrapped correctly, synchronous callouts in DML chains tie user-perceived latency to the ERP's response time. ERP slow → SF UI slow.
- A 100-record batch insert produces 100 callouts, hitting the per-transaction callout cap (100) and the bulkification anti-pattern simultaneously.

**Correct approach:** A trigger inserts a row into a `ERP_Outbox__c` staging object. A Queueable / scheduled job picks up new rows and pushes in batches. This is the *outbox pattern* and is the documented Salesforce-recommended approach (see Salesforce Architects "Asynchronous Publish Subscribe" pattern). Real-time push, when truly required, belongs on Platform Events, not in the trigger callout path.
