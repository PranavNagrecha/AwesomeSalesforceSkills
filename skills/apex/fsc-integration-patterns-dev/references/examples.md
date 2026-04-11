# Examples — FSC Integration Patterns Dev

## Example 1: Disabling RBL and Running a Bulk FinancialHolding Reconciliation

**Context:** A wealth management firm runs a nightly job that loads 250,000 FinancialHolding records from a Schwab custodian position file into FSC. The first production run produced thousands of `UNABLE_TO_LOCK_ROW` errors and the job completed with a 30% failure rate.

**Problem:** Rollup-by-Lookup was active for the integration user. Bulk API processed 10 concurrent batches, each touching holdings under shared parent FinancialAccounts. Every write triggered a parent-level recalculation, causing concurrent row-lock contention on the same FinancialAccount rows.

**Solution:**

Before triggering the Bulk API ingest job, use the Tooling API or Metadata API to confirm RBL is disabled for the integration profile, or have the integration runner call a lightweight Apex endpoint that checks and toggles the setting:

```apex
// Pre-load: disable RBL for the integration user via Custom Setting
// Run as System Administrator before bulk job start
FinServ__WealthAppConfig__c cfg = FinServ__WealthAppConfig__c.getInstance();
if (cfg.FinServ__EnableRollups__c) {
    cfg.FinServ__EnableRollups__c = false;
    update cfg;
}

// After Bulk API job reaches JobComplete state, schedule DPE recalculation
// Do NOT re-enable RBL mid-load or between job batches
```

After the Bulk API 2.0 job reaches `JobComplete` status (poll via `/services/data/vXX.0/jobs/ingest/{jobId}`), enqueue the DPE recalculation:

```apex
// Post-load: enqueue DPE batch for household rollup recalculation
Database.executeBatch(new HouseholdRollupRecalcBatch(), 200);
```

**Why it works:** Disabling RBL for the integration user prevents the per-record parent lock acquisition. Bulk API parallel batches can then write FinancialHolding records without contention. DPE recalculates rollups in a single controlled batch after all holdings are settled, producing correct totals without row-lock risk.

---

## Example 2: Scheduled Batch Apex for Market Data Price Updates

**Context:** An asset management firm updates `CurrentValue` on FinancialHolding daily at market close using a market data vendor REST API. An earlier implementation placed the callout inside an `after update` trigger on FinancialHolding — it worked in the sandbox but failed immediately in production with `System.CalloutException: You have uncommitted work pending`.

**Problem:** Apex prohibits callouts after DML has been performed in the same transaction. The trigger fired after DML on FinancialHolding, making any subsequent callout illegal. The trigger also had no scope control — a bulk update of 50,000 holdings would attempt 50,000 synchronous callouts, far exceeding the 100-callout-per-transaction limit.

**Solution:**

Remove the callout from the trigger entirely. Use a `Schedulable` that enqueues a `Batchable`:

```apex
public class MarketDataScheduler implements Schedulable {
    public void execute(SchedulableContext ctx) {
        Database.executeBatch(new MarketDataPriceBatch(), 50);
    }
}

public class MarketDataPriceBatch implements Database.Batchable<SObject>, Database.AllowsCallouts {

    public Database.QueryLocator start(Database.BatchableContext bc) {
        // Core FSC namespace — adjust to FinServ__FinancialHolding__c for managed-package
        return Database.getQueryLocator(
            'SELECT Id, ExternalAccountId__c, CurrentValue FROM FinancialHolding WHERE IsActive__c = true'
        );
    }

    public void execute(Database.BatchableContext bc, List<FinancialHolding> holdings) {
        // Build list of external IDs for the batch chunk
        List<String> externalIds = new List<String>();
        for (FinancialHolding h : holdings) {
            externalIds.add(h.ExternalAccountId__c);
        }

        // Single callout per batch chunk to price endpoint
        Map<String, Decimal> prices = MarketDataService.getPrices(externalIds);

        List<FinancialHolding> toUpdate = new List<FinancialHolding>();
        for (FinancialHolding h : holdings) {
            if (prices.containsKey(h.ExternalAccountId__c)) {
                h.CurrentValue = prices.get(h.ExternalAccountId__c);
                toUpdate.add(h);
            }
        }
        update toUpdate;
    }

    public void finish(Database.BatchableContext bc) {
        // Publish Platform Event to trigger downstream DPE aggregation
        EventBus.publish(new MarketDataLoadComplete__e(JobId__c = bc.getJobId()));
    }
}
```

**Why it works:** Running callouts inside `Database.Batchable` with `Database.AllowsCallouts` starts each `execute()` chunk in a fresh transaction with no prior DML, making callouts legal. Scope of 50 keeps the callout count well below the 100-per-transaction limit. The `finish()` Platform Event decouples DPE aggregation from the load.

---

## Example 3: Remote Call-In Handler with Idempotency Check

**Context:** A Fidelity integration sends real-time account balance updates to Salesforce FSC when a trade settles. The first implementation used a simple insert, which created duplicate FinancialAccount records on retry events when the upstream system sent the same payload twice.

**Problem:** No idempotency guard. Each POST from Fidelity's webhook triggered an unconditional insert, producing duplicates when the external system retried on network timeout.

**Solution:**

```apex
@RestResource(urlMapping='/fsc/custodian/v1/accounts/*')
global class CustodianAccountHandler {

    @HttpPost
    global static void handlePost() {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;

        try {
            CustodianPayload payload = (CustodianPayload) JSON.deserialize(
                req.requestBody.toString(), CustodianPayload.class
            );

            // Idempotency: query by external ID before upsert
            List<FinancialAccount> existing = [
                SELECT Id FROM FinancialAccount
                WHERE ExternalId__c = :payload.externalAccountId
                LIMIT 1
            ];

            FinancialAccount fa = existing.isEmpty()
                ? new FinancialAccount()
                : existing[0];

            fa.ExternalId__c = payload.externalAccountId;
            fa.Balance__c = payload.currentBalance;
            fa.LastCustodianSync__c = System.now();

            upsert fa ExternalId__c;

            res.statusCode = 200;
            res.responseBody = Blob.valueOf('{"status":"ok","id":"' + fa.Id + '"}');

        } catch (Exception e) {
            res.statusCode = 500;
            res.responseBody = Blob.valueOf('{"error":"' + e.getMessage() + '"}');
        }
    }

    public class CustodianPayload {
        public String externalAccountId;
        public Decimal currentBalance;
    }
}
```

**Why it works:** The SOQL query before upsert prevents duplicate inserts on retry. Using `upsert` with an explicit external ID field rather than a conditional insert/update is safe under concurrent retry conditions because the database enforces uniqueness on the external ID field — the second concurrent upsert will fail cleanly rather than creating a duplicate.

---

## Anti-Pattern: Synchronous Callout from FinancialHolding Trigger

**What practitioners do:** Place an HTTP callout to a market data or custodian API directly inside an `after insert` or `after update` trigger on FinancialHolding to "keep prices current immediately."

**What goes wrong:** Any prior DML in the same transaction (including the write that fired the trigger) makes callouts illegal. The trigger throws `System.CalloutException: You have uncommitted work pending` on every invocation in production. Even if the trigger is the first DML in the transaction, a batch load of 50,000 holdings will exceed the 100-callout limit in the first batch chunk.

**Correct approach:** Move all callouts to a `Batchable` class that implements `Database.AllowsCallouts`, scheduled via a `Schedulable`. Trigger the batch from a Platform Event subscription if near-real-time behavior is required — the event handler fires in a separate transaction context where callouts are permitted.
