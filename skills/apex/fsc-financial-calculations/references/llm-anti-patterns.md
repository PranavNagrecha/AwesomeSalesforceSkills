# LLM Anti-Patterns — FSC Financial Calculations

Common mistakes AI coding assistants make when generating or advising on FSC financial calculations.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Assuming FSC Natively Computes Portfolio Performance Metrics

**What the LLM generates:** Guidance to "look up the `PortfolioReturn__c` field on `FinancialAccount__c`" or "use the FSC Performance Summary feature," implying that IRR, TWR, or benchmark-relative return is available as a standard field or native FSC feature.

**Why it happens:** LLMs conflate the presence of financial aggregation fields (`Balance__c`, `TotalAssets__c`) with a full performance calculation engine. Training data that covers FSC rollup behavior may not clearly distinguish between balance aggregation and holding-period return calculations.

**Correct pattern:**

```
FSC only aggregates CurrentValue and QuantityOnHand from FinancialHolding to FinancialAccount.
No native FSC field or feature computes IRR, TWR, or any holding-period performance metric.
Implement performance metrics as a custom Database.Batchable Apex class writing to a
custom PortfolioPerformance__c object or custom fields on FinancialAccount__c.
```

**Detection hint:** Any response that mentions a field like `TWR__c`, `IRR__c`, `PortfolioReturn__c`, or `PerformanceSummary__c` as a standard FSC field should be flagged. These do not exist in the FSC schema.

---

## Anti-Pattern 2: Recommending Trigger-Based Portfolio Calculation

**What the LLM generates:** A `trigger on FinancialHolding__c (after insert, after update)` that queries all holdings for the parent account and computes a portfolio-wide metric (sum, weighted average, IRR approximation) synchronously.

**Why it happens:** Triggers are the most common Salesforce pattern for reactively maintaining derived values. LLMs trained on general Salesforce Apex patterns default to triggers without accounting for FSC-specific volume constraints.

**Correct pattern:**

```apex
// WRONG: trigger-based portfolio calculation at scale
trigger FinancialHoldingTrigger on FinServ__FinancialHolding__c (after insert, after update) {
    // Querying all holdings per account inside a trigger hits SOQL limits at bulk scale
    List<FinServ__FinancialHolding__c> allHoldings = [
        SELECT ... FROM FinServ__FinancialHolding__c WHERE ...
    ];
}

// CORRECT: scheduled Apex batch
global class PortfolioMetricBatch implements Database.Batchable<SObject> {
    // Process accounts in scope-controlled chunks — see examples.md
}
```

**Detection hint:** Any response suggesting a `trigger on FinServ__FinancialHolding__c` that contains an inner SOQL query or computes an aggregate across the parent account's full holding set should be rejected.

---

## Anti-Pattern 3: Skipping the Disable/Re-Enable Trigger Pattern for Bulk Loads

**What the LLM generates:** A bulk data load procedure (Data Loader steps, Bulk API script, or migration instructions) that loads `FinancialHolding__c` records directly without any mention of the `WealthAppConfig__c` custom setting, and proceeds to verify results without running `FinServ.RollupRecalculationBatchable`.

**Why it happens:** The `WealthAppConfig__c` trigger-suppression mechanism is FSC-specific and underdocumented. General Salesforce Apex and data migration training data does not include it. LLMs default to the generic "bulk load, then verify" pattern without the FSC safety steps.

**Correct pattern:**

```apex
// Step 1: disable FSC rollup triggers before bulk load
WealthAppConfig__c cfg = WealthAppConfig__c.getInstance('FinancialServicesCloud');
cfg.Enable_Rollup_Summary__c = false;
cfg.Enable_Group_Record_Rollup__c = false;
update cfg;

// Step 2: run bulk load (Data Loader, API, etc.)

// Step 3: re-enable and recalculate
cfg.Enable_Rollup_Summary__c = true;
cfg.Enable_Group_Record_Rollup__c = true;
update cfg;
Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 200);
```

**Detection hint:** Any FSC bulk migration or data load guide that does not reference `WealthAppConfig__c`, `Enable_Rollup_Summary__c`, or `RollupRecalculationBatchable` is missing the FSC safety protocol.

---

## Anti-Pattern 4: Using the RBL-to-DPE Auto-Conversion Wizard and Treating the Output as Production-Ready

**What the LLM generates:** Instructions to use the Salesforce "Migrate to Data Processing Engine" wizard on all existing RBL definitions, accept the generated DPE definitions as-is, and schedule them all to run in the same maintenance window.

**Why it happens:** The wizard exists and is documented, so LLMs recommend it as the straightforward migration path. The lock-contention consequence of running multiple concurrently generated DPE definitions against shared target fields is a production-only failure mode not prominent in official migration documentation.

**Correct pattern:**

```
Do NOT schedule all auto-generated DPE definitions simultaneously.
Either:
1. Run them strictly sequentially with no overlapping schedule windows, OR
2. (Preferred) Discard auto-generated definitions and build a single DPE recipe
   from scratch with a single writeback node that handles all target fields in one pass.
One DPE definition = one recalculation run = no lock contention.
```

**Detection hint:** Any DPE migration recommendation that outputs multiple DPE definitions running on the same schedule without explicit sequencing should be reviewed for lock-contention risk.

---

## Anti-Pattern 5: Treating `FinServ.RollupRecalculationBatchable` as a Full-Org Recalculation Tool

**What the LLM generates:** Post-migration or post-correction runbooks that instruct the team to "run the FSC recalculation batch to refresh all financial aggregates," implying that `FinServ.RollupRecalculationBatchable` covers all financial objects in the org.

**Why it happens:** The batch is prominently documented as the FSC aggregate reset tool, and its name does not suggest any scope limitation. LLMs naturally recommend it as the universal fix for any stale rollup in an FSC org.

**Correct pattern:**

```
FinServ.RollupRecalculationBatchable covers ONLY:
- FinancialAccount__c (FSC-native)
- AssetsAndLiabilities__c (FSC-native)

It does NOT cover:
- Custom financial objects (ExternalCustodianPosition__c, etc.)
- External object aggregates
- Custom performance metric fields (TWR, IRR)

Maintain a separate recalculation Apex batch or DPE recipe for every custom
aggregation path. Document both processes in the org runbook.
```

**Detection hint:** Any runbook that lists only `FinServ.RollupRecalculationBatchable` as the recalculation step in an org that has custom financial objects should be flagged as incomplete.

---

## Anti-Pattern 6: Accumulating Large Collections in `Database.Stateful` Across All Batch Chunks

**What the LLM generates:** A `Database.Batchable` class that uses `Database.Stateful` to accumulate a `Map<Id, List<Decimal>>` of intermediate results across all `execute()` chunks, then performs the final computation in `finish()`.

**Why it happens:** This mirrors a natural in-memory aggregation pattern. LLMs that understand `Database.Stateful` may suggest it without accounting for the cumulative heap cost across hundreds of execute chunks.

**Correct pattern:**

```apex
// WRONG: accumulating across all chunks
global class BadBatch implements Database.Batchable<SObject>, Database.Stateful {
    global Map<Id, List<Decimal>> allResults = new Map<Id, List<Decimal>>();
    global void execute(...) {
        // adds to allResults — grows without bound
    }
    global void finish(...) {
        // processes allResults — may already have hit heap limit
    }
}

// CORRECT: write results per chunk, no in-memory accumulation
global class GoodBatch implements Database.Batchable<SObject> {
    global void execute(...) {
        List<PortfolioPerformance__c> results = new List<PortfolioPerformance__c>();
        // compute and collect for this chunk only
        upsert results FinancialAccount__c; // write at end of each chunk
    }
}
```

**Detection hint:** A `Database.Batchable` class where `Database.Stateful` is used alongside a `Map` or `List` field that grows in `execute()` and is consumed in `finish()` should be reviewed for heap exhaustion risk.
