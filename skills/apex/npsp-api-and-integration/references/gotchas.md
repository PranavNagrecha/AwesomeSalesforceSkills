# Gotchas — NPSP API and Integration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Direct Opportunity Insert Bypasses All NPSP Processing

**What happens:** When Opportunity and OppPayment records are inserted directly (via Data Loader, REST API, or Apex without BDI), NPSP's TDTM trigger framework is not invoked for BDI-specific processing. GAU allocations are not created, soft credits are not processed, Household Account rollup totals (`TotalGifts__c`, `LargestGift__c`, etc.) are not recalculated correctly, and Salesforce Elevate payment IDs are not linked.

**When it occurs:** Every integration that routes around BDI — peer-to-peer fundraising imports, event platform gift syncs, and Data Loader gift history migrations.

**How to avoid:** Route ALL gift data through `npsp__DataImport__c` and `BDI_DataImport_API`. No exceptions. If BDI cannot handle a specific gift type, document the exception and manually create the associated NPSP allocation and soft credit records.

---

## Gotcha 2: ERD Installments API Does Not Persist Opportunity Records

**What happens:** `RD2_ApiService.getInstallments()` returns a list of calculated projection objects. These projections are NOT persisted to the database and no Opportunity records are created by calling this method. Future installment Opportunities are created by the `RD2_OpportunityEvaluation_BATCH` Apex scheduled job.

**When it occurs:** When developers build donor portals or cash flow projection tools that call `getInstallments()` and then query for the returned installments as Opportunity records.

**How to avoid:** Use `getInstallments()` exclusively for display/projection purposes. For actual Opportunity records, query `npe03__Recurring_Donation__c` child Opportunities. Never check for Opportunity creation as a side effect of the Installments API.

---

## Gotcha 3: BDI Advanced Mapping Must Be Enabled for Custom Field Mapping

**What happens:** An integration populates custom fields on `npsp__DataImport__c` (via Advanced Mapping configuration) and they are silently ignored in processing. Custom Opportunity, Contact, or Payment fields mapped via BDI are only processed when Advanced Mapping is enabled in NPSP Settings > Advanced Mapping.

**When it occurs:** When a developer configures Advanced Mapping field-level definitions in the NPSP UI but the Advanced Mapping feature switch itself is not enabled. Or when the integration was built in a sandbox with Advanced Mapping enabled but the production org does not have it enabled.

**How to avoid:** Verify `npsp__Advanced_Mapping_Enabled__c = true` in the `npsp__Data_Import_Settings__mdt` Custom Metadata record before building any integration that relies on custom field mapping. Add this as a post-deployment check.

---

## Gotcha 4: BDI Batch Size Limit Is 50,000 Records per File (Not Per Invocation)

**What happens:** The NPSP Data Importer supports up to 50,000 records in a single batch file (100 MB maximum file size for CSV imports). Integrations that try to push more than 50,000 DataImport records in a single BDI batch job may hit governor limits or memory constraints.

**When it occurs:** Large historical gift migrations and event platform imports with high gift volumes.

**How to avoid:** Chunk DataImport record creation and BDI processing into batches of no more than 50,000 records. For very large imports (500,000+ gifts), schedule multiple BDI batch runs across multiple days rather than one massive batch.

---

## Gotcha 5: Household Rollup Recalculation Does Not Run in Real-Time After BDI

**What happens:** After a large BDI import, household `TotalGifts__c`, `NumberOfClosedOpps__c`, and `LargestGift__c` rollup fields on Contact and Account are not immediately updated. NPSP's Customizable Rollups (CRLP) runs as a batch job on a schedule — rollup fields reflect the state at the last batch run, not the state after the most recent import.

**When it occurs:** During and immediately after large bulk imports when fundraising staff check household totals and find them inaccurate.

**How to avoid:** After any bulk BDI import, manually trigger a CRLP batch recalculation run via NPSP Settings > Batch Processing > Recalculate Customizable Rollups, or call `CRLP_RollupBatch_SVC.runLdvBatch()` programmatically. Document this as a required post-import step.
