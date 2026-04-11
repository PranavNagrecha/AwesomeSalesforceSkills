# Examples — FSC Financial Calculations

## Example 1: Disabling FSC Rollup Triggers for a Migration Load

**Context:** A wealth management firm is migrating 800,000 `FinancialHolding__c` records from a legacy system into FSC using Data Loader in 200-row batches. With FSC rollup triggers enabled, every batch insert fires synchronous DML against the parent `FinancialAccount__c` and household `Account`, causing row-lock errors that fail roughly 30% of batches.

**Problem:** The FSC Rollup-by-Lookup engine fires on every `FinancialHolding__c` DML operation. At bulk scale, many batches simultaneously try to update the same parent `FinancialAccount__c` rows. The database lock timeout is reached before the locks clear, and Salesforce rolls back the DML with a `UNABLE_TO_LOCK_ROW` error.

**Solution:**

Step 1 — Disable FSC rollup triggers for the integration API user before the load:

```apex
// Run this in Anonymous Apex before starting Data Loader
WealthAppConfig__c cfg = WealthAppConfig__c.getInstance('FinancialServicesCloud');
cfg.Enable_Rollup_Summary__c = false;
cfg.Enable_Group_Record_Rollup__c = false;
update cfg;
System.debug('FSC rollup triggers disabled for bulk load.');
```

Step 2 — Run the full Data Loader migration with triggers disabled.

Step 3 — Re-enable the setting and kick off `FinServ.RollupRecalculationBatchable`:

```apex
// Run after Data Loader completes
WealthAppConfig__c cfg = WealthAppConfig__c.getInstance('FinancialServicesCloud');
cfg.Enable_Rollup_Summary__c = true;
cfg.Enable_Group_Record_Rollup__c = true;
update cfg;

FinServ.RollupRecalculationBatchable batchJob =
    new FinServ.RollupRecalculationBatchable();
// Scope of 200 works well for most orgs; reduce to 50 if timeouts occur
Database.executeBatch(batchJob, 200);
System.debug('FSC rollup recalculation batch enqueued.');
```

**Why it works:** With triggers disabled, Data Loader inserts `FinancialHolding__c` rows without touching parent records, eliminating lock contention entirely. The subsequent `FinServ.RollupRecalculationBatchable` reads all holdings in bulk and computes parent totals in a controlled batch context where the platform can manage locks across scope chunks rather than within a single overcrowded transaction.

---

## Example 2: Custom Apex Batch for Time-Weighted Return

**Context:** A private banking team requires monthly TWR (time-weighted return) reports for each investment account. The FSC `CurrentValue__c` rollup only gives a point-in-time balance — it does not compute holding-period returns or account for cash flows.

**Problem:** There is no FSC-native mechanism for TWR or IRR. An LLM might suggest using formula fields or standard rollup summaries, neither of which can compute multi-period linked returns. A trigger-based approach hits CPU and SOQL limits on any real portfolio size.

**Solution:**

```apex
global class PortfolioTWRBatch
    implements Database.Batchable<SObject>, Database.Stateful {

    // Track how many accounts were processed for finish() logging
    global Integer processed = 0;

    global Database.QueryLocator start(Database.BatchableContext bc) {
        // Only process investment-type accounts with holdings
        return Database.getQueryLocator(
            'SELECT Id, Name ' +
            'FROM FinServ__FinancialAccount__c ' +
            'WHERE FinServ__FinancialAccountType__c = \'Investment Account\' ' +
            'AND FinServ__Balance__c > 0'
        );
    }

    global void execute(Database.BatchableContext bc,
                        List<FinServ__FinancialAccount__c> scope) {

        Set<Id> accountIds = new Map<Id, FinServ__FinancialAccount__c>(scope).keySet();

        // Query sub-period data from a custom transaction history object
        Map<Id, List<PortfolioTransaction__c>> txByAccount =
            new Map<Id, List<PortfolioTransaction__c>>();

        for (PortfolioTransaction__c tx : [
            SELECT FinancialAccount__c, TransactionDate__c, Amount__c, EndValue__c
            FROM PortfolioTransaction__c
            WHERE FinancialAccount__c IN :accountIds
            ORDER BY FinancialAccount__c, TransactionDate__c ASC
        ]) {
            if (!txByAccount.containsKey(tx.FinancialAccount__c)) {
                txByAccount.put(tx.FinancialAccount__c, new List<PortfolioTransaction__c>());
            }
            txByAccount.get(tx.FinancialAccount__c).add(tx);
        }

        List<PortfolioPerformance__c> results = new List<PortfolioPerformance__c>();

        for (FinServ__FinancialAccount__c acct : scope) {
            List<PortfolioTransaction__c> txList =
                txByAccount.containsKey(acct.Id)
                ? txByAccount.get(acct.Id)
                : new List<PortfolioTransaction__c>();

            Decimal twr = computeLinkedTWR(txList);

            results.add(new PortfolioPerformance__c(
                FinancialAccount__c = acct.Id,
                TWR__c             = twr,
                AsOfDate__c        = Date.today(),
                PeriodLabel__c     = String.valueOf(Date.today().year()) + '-' +
                                     String.valueOf(Date.today().month())
            ));
        }

        upsert results FinancialAccount__c;
        processed += scope.size();
    }

    global void finish(Database.BatchableContext bc) {
        System.debug('PortfolioTWRBatch complete. Accounts processed: ' + processed);
    }

    /**
     * Linked sub-period TWR using Modified Dietz approximation.
     * TWR = Product of (1 + sub-period return) - 1 across all periods.
     */
    private Decimal computeLinkedTWR(List<PortfolioTransaction__c> transactions) {
        if (transactions == null || transactions.isEmpty()) return 0;
        Decimal linkedReturn = 1.0;
        for (PortfolioTransaction__c tx : transactions) {
            if (tx.EndValue__c != null && tx.Amount__c != null && tx.Amount__c != 0) {
                Decimal subPeriodReturn = tx.EndValue__c / tx.Amount__c;
                linkedReturn *= subPeriodReturn;
            }
        }
        return linkedReturn - 1.0;
    }
}
```

Schedule the batch for monthly execution:

```apex
// Schedule to run at 2 AM on the first of each month
String cronExpr = '0 0 2 1 * ?';
System.schedule('Monthly Portfolio TWR Batch', cronExpr,
    new SchedulableTWRWrapper());
```

**Why it works:** Processing accounts in controlled scope chunks (50–100 per execute) keeps SOQL rows and CPU well within limits. Collecting all DML into a list and upserting once per chunk avoids the per-record DML anti-pattern. Using `Database.Stateful` only for the processed counter (not for accumulating large data) avoids memory bloat across chunks.

---

## Anti-Pattern: Assuming Native FSC Rollup Covers All Financial Aggregation

**What practitioners do:** After seeing `FinServ__Balance__c` auto-update when holdings are created, they assume all custom financial objects will similarly auto-aggregate, and build data models expecting automatic rollup without any custom code.

**What goes wrong:** Custom objects such as `ExternalCustodianPosition__c` or `ManagedPortfolioHolding__c` have no FSC trigger coverage. Rollup fields on `FinancialAccount__c` targeting these custom objects stay at zero regardless of how many child records exist. The bug is often only caught in UAT when aggregate reports show incorrect totals.

**Correct approach:** Before building a data model, confirm whether each object participates in FSC's supported rollup set (`FinancialAccount`, `AssetsAndLiabilities`, `FinancialHolding`). Any object outside that set requires either a custom Apex Batchable to compute and write aggregates or a DPE recipe. Document the aggregation gap explicitly in the technical design and include the Apex or DPE pattern as a required deliverable.
