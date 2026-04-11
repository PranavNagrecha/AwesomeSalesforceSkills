# Gotchas — FSC Financial Calculations

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: FSC Rollup Triggers Cause Row-Lock Errors During Bulk Data Loads

**What happens:** When thousands of `FinancialHolding__c` records are inserted or updated in bulk, the FSC Rollup-by-Lookup Apex triggers fire synchronously on every record. Each trigger execution attempts to increment the parent `FinancialAccount__c` balance. Multiple concurrent batches contending for the same parent row exceed the database row-lock timeout, causing `UNABLE_TO_LOCK_ROW` errors that roll back entire batches.

**When it occurs:** During any bulk DML operation that creates or modifies many `FinancialHolding__c` records associated with the same parent `FinancialAccount__c` — typically Data Loader jobs, migration scripts, Bulk API upserts, or nightly data feed integrations.

**How to avoid:** Before bulk loads, set `Enable_Rollup_Summary__c = false` and `Enable_Group_Record_Rollup__c = false` on the `WealthAppConfig__c` custom setting for the API/integration user. Complete the bulk load, then re-enable both flags and run `FinServ.RollupRecalculationBatchable` to rebuild all aggregated values. Never proceed straight from bulk load to user-facing reporting without running the recalculation batch first.

---

## Gotcha 2: DPE Auto-Conversion from RBL Multiplies Lock Contention

**What happens:** When using the Salesforce wizard to convert an existing Rollup-by-Lookup configuration to Data Processing Engine, Salesforce generates a separate DPE definition for each individual RBL rule. When these definitions are scheduled to run concurrently (or even sequentially with tight windows), they each write to the same target fields on the same records, reintroducing the lock contention problem that DPE migration was meant to solve.

**When it occurs:** After running the RBL-to-DPE migration wizard and scheduling all generated DPE jobs using the default auto-generated schedule — especially in orgs with many RBL rules covering the same target object.

**How to avoid:** Do not use the one-to-one RBL-to-DPE conversion wizard as-is. Build DPE recipes from scratch with a single final aggregate writeback node that computes all target values in one pass. A single DPE definition running sequentially against a target object will not cause lock contention because it processes records in an ordered, controlled batch pipeline rather than competing parallel writers.

---

## Gotcha 3: `FinServ.RollupRecalculationBatchable` Ignores Custom Objects

**What happens:** Practitioners who discover `FinServ.RollupRecalculationBatchable` assume it recalculates all financial aggregates in the org, including any custom financial objects added to the data model. In reality, `RollupRecalculationBatchable` only rebuilds rollup values for the objects covered by native FSC RBL triggers: `FinancialAccount__c` and `AssetsAndLiabilities__c` families. Custom objects such as external custodian positions or bespoke portfolio wrappers are silently ignored.

**When it occurs:** After building a custom aggregation data model alongside native FSC objects, then running `RollupRecalculationBatchable` expecting all aggregates to be refreshed — for example, after a migration or data correction.

**How to avoid:** Maintain a separate recalculation path for any custom-object aggregation — either a custom `Database.Batchable` class or a dedicated DPE recipe. Document in the org's technical runbook that there are two separate recalculation processes: the FSC-native `RollupRecalculationBatchable` for supported objects, and the custom batch/DPE process for everything else.

---

## Gotcha 4: Performance Metric Fields Are Not Provided by FSC — Silence Is Misleading

**What happens:** The `FinancialAccount__c` object exposes rollup fields like `FinServ__Balance__c` and `FinServ__TotalAssets__c`. Practitioners (and LLMs) conflate these balance aggregates with portfolio performance metrics and assume FSC computes or stores IRR, TWR, or benchmark-relative return. These fields do not exist anywhere in the standard FSC schema. Implementations that "look for the TWR field" waste time and ultimately deploy nothing.

**When it occurs:** When a wealth management team asks for a performance report and an implementor starts by searching for a native FSC performance metric field or formula, or asks an LLM to "show me how to surface the portfolio return in FSC."

**How to avoid:** Clarify upfront that FSC only aggregates current value and quantity. Any holding-period or return-based metric requires a custom implementation — a `PortfolioPerformance__c` custom object, custom fields on `FinancialAccount__c`, and a custom Apex batch or DPE recipe to populate them. Treat this as a greenfield Apex development task, not a configuration task.

---

## Gotcha 5: `Database.Stateful` Misuse Causes Memory Bloat Across Batch Chunks

**What happens:** Developers implementing the custom portfolio performance batch use `Database.Stateful` to accumulate intermediate results across all `execute()` chunks, building a large in-memory collection throughout the batch run. For orgs with thousands of accounts and large holding sets, this causes heap exhaustion errors (`System.LimitException: Apex heap size too large`) in later chunks.

**When it occurs:** When `Database.Stateful` is used to hold a `Map<Id, Decimal>` of computed results across all chunks so the final aggregate can be assembled in `finish()` — a pattern that feels natural but does not scale.

**How to avoid:** Write computed results directly to the database at the end of each `execute()` chunk rather than accumulating them in state. Use `Database.Stateful` only for lightweight counters (e.g., total records processed for logging) rather than data collections. If cross-chunk accumulation is truly required (e.g., linked return spanning all accounts), break the calculation into two batch jobs: the first writes sub-period data to a staging object, the second reads and links those results.
