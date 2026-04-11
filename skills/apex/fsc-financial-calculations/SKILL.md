---
name: fsc-financial-calculations
description: "Use this skill when implementing custom financial calculation logic in Financial Services Cloud — including portfolio performance metrics (IRR, TWR), wealth rollup recalculation after bulk loads, custom Apex aggregation for objects outside native FSC rollup scope, and Data Processing Engine integration for large-scale writeback. NOT for standard declarative rollup summaries on supported out-of-the-box FSC objects, nor for configuring the FSC Rollup-by-Lookup admin UI itself."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
tags:
  - fsc
  - financial-services-cloud
  - rollup
  - portfolio
  - apex-batch
  - data-processing-engine
  - wealth-management
  - financial-calculations
inputs:
  - "FSC org with FinancialAccount, FinancialHolding, AssetsAndLiabilities objects configured"
  - "Clarity on whether custom objects or external custodian data are involved (determines Apex vs DPE path)"
  - "Data volume estimate for FinancialHolding records per household"
  - "Whether bulk data loads (Data Loader, API) are part of the workflow"
outputs:
  - "Apex Batchable class implementing rollup or performance metric logic"
  - "Guidance on disabling/re-enabling FSC rollup triggers around bulk loads"
  - "DPE recipe design recommendations for large-scale aggregation"
  - "Scheduled job skeleton for periodic portfolio performance recalculation"
triggers:
  - "FSC wealth rollup not updating after custodian data load"
  - "row lock errors when loading FinancialHolding records in bulk"
  - "portfolio IRR or TWR calculation not available natively in FSC"
  - "DPE recipe causing lock contention after RBL migration"
  - "custom aggregation needed for non-FSC objects in wealth management"
dependencies:
  - admin/financial-account-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# FSC Financial Calculations

Use this skill when you need custom Apex logic to calculate portfolio performance metrics, recalculate wealth rollups after bulk data operations, or aggregate financial data that falls outside the native FSC Rollup-by-Lookup (RBL) engine. It covers the full decision path from choosing the right calculation mechanism to implementing and testing bulkified Apex batch jobs or Data Processing Engine recipes.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Rollup engine in use:** Confirm whether the org uses native FSC Rollup-by-Lookup (RBL) triggers, Data Processing Engine (DPE), or both. RBL is the default; orgs on API version 55+ may have migrated to DPE. Check the Wealth Application Config custom setting fields `Enable_Rollup_Summary__c` and `Enable_Group_Record_Rollup__c`.
- **Object scope:** Identify whether the calculation touches only supported objects (`FinancialAccount`, `AssetsAndLiabilities`, `FinancialHolding`) or extends to custom objects or external custodian feed data. Native FSC rollup triggers fire only on the supported set; anything else requires custom Apex or DPE.
- **Data volume:** Estimate records per household. High-volume orgs (tens of thousands of `FinancialHolding` rows per account) face row-lock contention when rollup triggers and bulk DML run concurrently. This drives the need for the disable/re-enable pattern.
- **Most common wrong assumption:** Practitioners assume FSC auto-aggregates all financial data. Native triggers aggregate `CurrentValue` and `QuantityOnHand` from `FinancialHolding` up to the `FinancialAccount` and household level only. Portfolio performance metrics such as IRR and TWR have no native engine and always require custom implementation.
- **Governor limit in play:** Each `FinancialHolding` trigger update fires DML on parent `FinancialAccount` and potentially the household `Account`. At scale this exhausts row locks. The fix is to suppress triggers during bulk loads and run `FinServ.RollupRecalculationBatchable` post-load.

---

## Core Concepts

### Rollup-by-Lookup (RBL) Engine

FSC ships with an Apex-trigger-driven aggregation engine called Rollup-by-Lookup (RBL). When a `FinancialHolding__c` record is inserted or updated, platform triggers increment the `CurrentValue__c` and `QuantityOnHand__c` rollup fields on the parent `FinancialAccount__c`, and then cascade that sum to the household-level `Account`. This is synchronous and transactional, which works well for single-record or small-batch DML but causes row-lock errors when thousands of holdings are loaded at once. RBL only covers `FinancialAccount` and `Assets & Liabilities` object families. Custom objects are out of scope.

### Data Processing Engine (DPE) for Large-Scale Aggregation

Data Processing Engine is a batch-mode, no-code/low-code framework that reads source data, applies transformations, and writes results back to Salesforce objects. For FSC, DPE is used either as a replacement for RBL (when migrating away from trigger-based rollups) or as the only viable path for aggregating custom objects and external custodian data. Critical constraint: Salesforce generates a separate DPE definition when converting an existing RBL configuration one-to-one. Running multiple DPE definitions against the same target field concurrently causes lock contention identical to the RBL bulk-load problem. Build DPE recipes from scratch with a single final aggregate node that writes all computed values in one pass.

### Custom Apex Batch for Performance Metrics

FSC provides no native calculation engine for time-weighted return (TWR), internal rate of return (IRR), or any holding-period performance attribution. These must be implemented as custom `Database.Batchable` Apex classes scheduled via `System.scheduleBatch` or the Apex Scheduler. The batch queries `FinancialHolding__c` and associated transaction history (stored in custom objects or external objects), performs the calculation in `execute()` over scope-controlled chunks, and writes results back to a custom performance summary object or directly to `FinancialAccount__c` custom fields.

### Bulk Load Safety Protocol

When loading large volumes of `FinancialHolding__c`, `FinancialAccount__c`, or `AssetsAndLiabilities__c` records via Data Loader or API, the FSC rollup triggers must be disabled for the API user running the load. Disable by unchecking `Enable Rollup Summary` and `Enable Group Record Rollup` in the Wealth Application Config custom setting for that user. After the load completes, re-enable the setting and invoke `FinServ.RollupRecalculationBatchable` to rebuild all aggregates from scratch. Skipping the re-run leaves rolled-up totals stale.

---

## Common Patterns

### Pattern 1: Post-Bulk-Load Rollup Recalculation

**When to use:** Any time records are loaded via Data Loader, Bulk API, or a migration script rather than through the Salesforce UI or a standard single-record API call.

**How it works:**
1. Before loading, set `Enable_Rollup_Summary__c = false` and `Enable_Group_Record_Rollup__c = false` on the `WealthAppConfig__c` custom setting for the API/integration user.
2. Perform the bulk load.
3. After load completion, re-enable both settings.
4. Invoke `FinServ.RollupRecalculationBatchable` to rebuild all FSC aggregate values.

```apex
// Schedule recalculation immediately after bulk load
FinServ.RollupRecalculationBatchable batchJob =
    new FinServ.RollupRecalculationBatchable();
Database.executeBatch(batchJob, 200);
```

**Why not the alternative:** Leaving triggers enabled during bulk load causes row-lock contention on parent `FinancialAccount__c` records because hundreds of trigger executions try to update the same parent simultaneously within the same transaction window.

### Pattern 2: Custom Apex Batch for Portfolio IRR / TWR

**When to use:** When the org requires performance reporting metrics (IRR, TWR, or custom benchmarking) on client portfolios. No FSC native engine covers these.

**How it works:**
1. Create a custom object `PortfolioPerformance__c` (or add fields to `FinancialAccount__c`) to store computed metrics.
2. Implement `Database.Batchable<SObject>` with a SOQL start query scoped to `FinancialAccount__c` records needing recalculation.
3. In `execute()`, query associated `FinancialHolding__c` records and any transaction history for each account in the scope chunk.
4. Compute TWR using the modified Dietz method or sub-period linking.
5. DML-write results back in a list (bulkified) at the end of `execute()`.
6. Schedule with `System.scheduleBatch` or `System.schedule` for nightly execution.

```apex
global class PortfolioTWRBatch implements Database.Batchable<SObject>, Database.Stateful {

    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, Name, FinServ__Balance__c ' +
            'FROM FinServ__FinancialAccount__c ' +
            'WHERE FinServ__RecordTypeName__c = \'Investment Account\''
        );
    }

    global void execute(Database.BatchableContext bc, List<FinServ__FinancialAccount__c> scope) {
        List<PortfolioPerformance__c> results = new List<PortfolioPerformance__c>();
        for (FinServ__FinancialAccount__c acct : scope) {
            // Query holdings and compute TWR — implementation specific
            Decimal twr = computeTWR(acct.Id);
            results.add(new PortfolioPerformance__c(
                FinancialAccount__c = acct.Id,
                TWR__c = twr,
                AsOfDate__c = Date.today()
            ));
        }
        upsert results FinancialAccount__c;
    }

    global void finish(Database.BatchableContext bc) {}

    private Decimal computeTWR(Id accountId) {
        // Retrieve sub-period returns from transaction history and link
        return 0.0; // placeholder
    }
}
```

**Why not the alternative:** Attempting to compute TWR in a trigger or synchronous Apex fails on any meaningful dataset due to SOQL and CPU limits. Batch processing with a manageable scope size (50–200 accounts) is required.

### Pattern 3: DPE Recipe for Custom-Object Aggregation

**When to use:** When aggregation targets custom objects or external custodian data that is not covered by native FSC RBL triggers.

**How it works:**
1. Build a new DPE definition from scratch — do not convert an existing RBL definition.
2. Source nodes read from the custom object or external data source.
3. Group and aggregate nodes compute the desired rollup (sum, weighted average).
4. A single writeback node at the end of the recipe writes all computed values to the target object.
5. Schedule the DPE batch via the Data Processing Engine configuration in Setup.

**Why not the alternative:** Converting an RBL definition to DPE one-to-one causes Salesforce to generate a separate DPE definition per RBL rule. Running these concurrently against the same target record causes the same lock contention the pattern is meant to solve.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Aggregating `FinancialHolding` to `FinancialAccount` in real time | Native FSC RBL triggers (keep enabled) | Synchronous, transactional, no custom code needed |
| Bulk-loading hundreds of thousands of `FinancialHolding` rows | Disable RBL triggers, bulk load, run `FinServ.RollupRecalculationBatchable` | Avoids row-lock contention |
| Computing IRR, TWR, or other performance metrics | Custom `Database.Batchable` Apex | No native FSC calculation engine exists for performance metrics |
| Aggregating custom objects or external custodian data | DPE recipe built from scratch | RBL triggers do not fire on custom objects |
| Migrating from RBL to DPE | Build DPE recipes from scratch, single writeback node | One-to-one RBL-to-DPE conversion causes lock contention |
| Portfolio metrics needed in near-real-time | Custom Apex scheduled every 15 min or triggered via Platform Event | DPE is batch-only; use Apex for latency-sensitive calculations |

---

## Recommended Workflow

1. **Clarify scope and object coverage:** Confirm which objects the calculation touches (`FinancialHolding`, `AssetsAndLiabilities`, custom, external). Identify whether native RBL is enabled or if the org has migrated to DPE. Check the `WealthAppConfig__c` setting.
2. **Select the right mechanism:** Use the decision table above. Bulk load → disable/recalc pattern. Performance metrics → custom batch. Custom objects → DPE recipe from scratch.
3. **Implement and bulkify:** Write or review the Apex batch or DPE recipe. For Apex batches, verify the `execute()` scope is bounded (50–200 records for FinancialAccount), DML is outside loops, and `Database.Stateful` is used only when truly stateful aggregation is required.
4. **Handle the disable/re-enable pattern for bulk loads:** Update the `WealthAppConfig__c` setting before and after any bulk DML path. Enqueue `FinServ.RollupRecalculationBatchable` programmatically or document the manual step explicitly.
5. **Write Apex tests with FSC object coverage:** Instantiate `FinServ__FinancialAccount__c` and `FinServ__FinancialHolding__c` in test data. Assert that computed fields on `PortfolioPerformance__c` or the target object match expected values after batch execution.
6. **Test with bulk volume in a sandbox:** Load 5,000+ `FinancialHolding` rows and verify no row-lock errors occur and rollup totals are accurate post-recalculation.
7. **Review governor limit headroom:** Confirm the batch does not exceed 50,000 SOQL rows, 10,000 DML rows, or 60-second CPU limit per execute chunk. Adjust scope size if needed.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `WealthAppConfig__c` disable/re-enable pattern is documented or implemented for all bulk load paths
- [ ] `FinServ.RollupRecalculationBatchable` is invoked after bulk loads and tested in sandbox
- [ ] Custom Apex batch classes are bulkified — no SOQL or DML inside loops
- [ ] DPE recipes use a single writeback node, not one-to-one converted from RBL definitions
- [ ] Apex tests cover both the happy path and a bulk scenario (200+ records minimum)
- [ ] Performance metric calculations (IRR, TWR) are implemented in scheduled batch, not triggers
- [ ] Custom objects and external custodian data are routed through DPE or custom Apex, not assumed to be covered by RBL

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **RBL triggers fire synchronously on every FinancialHolding DML** — When any insert, update, or delete on `FinancialHolding__c` occurs, the FSC trigger immediately updates the parent `FinancialAccount__c` and household `Account`. In bulk operations this means hundreds of transactions contending for the same parent rows, producing row-lock errors that roll back the entire batch.
2. **DPE auto-conversion from RBL creates one definition per rule** — Using the Salesforce migration wizard to convert RBL to DPE generates a separate DPE definition for each RBL configuration entry. Scheduling all of them causes simultaneous writes to the same target fields and replicates the lock contention it was meant to solve.
3. **No native FSC engine for IRR or TWR** — Practitioners (and LLMs) sometimes assume FSC computes portfolio performance metrics natively. It does not. `CurrentValue__c` and `QuantityOnHand__c` are the only aggregated values. IRR, TWR, and benchmark comparisons require fully custom Apex implementation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `PortfolioTWRBatch.cls` | Apex Batchable class computing time-weighted return per FinancialAccount |
| `RollupRecalcTriggerManager.cls` | Utility class to programmatically toggle `WealthAppConfig__c` for API user before/after bulk loads |
| DPE recipe design notes | Single-node writeback recipe structure for custom-object aggregation |
| Scheduled job configuration | `System.schedule` or `scheduleBatch` call wiring the batch to a nightly cron |

---

## Related Skills

- admin/financial-account-setup — understand FSC object model and rollup admin configuration before implementing custom calculations
