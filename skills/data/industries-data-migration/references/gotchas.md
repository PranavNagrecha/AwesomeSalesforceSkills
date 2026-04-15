# Gotchas — Industries Data Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: InsurancePolicyCoverage Accepts an Invalid InsurancePolicyAsset Reference Without Error

**What happens:** When `InsurancePolicyAssetId` is populated on an InsurancePolicyCoverage record, the platform accepts the insert even if the referenced InsurancePolicyAsset belongs to a different InsurancePolicy. There is no cross-object validation enforcing that the asset and the coverage belong to the same policy. The record is committed successfully, but the coverage will not appear in the correct policy detail view and may cause display errors in OmniStudio-based policy management screens.

**When it occurs:** During bulk load when coverage and asset files were joined on an incorrect key in the ETL transformation — for example, when a source system uses a composite key for asset identification and the ETL maps only the first component.

**How to avoid:** Before running the InsurancePolicyCoverage load, run a validation query in the target org that checks: for each coverage row in the load file, does the referenced InsurancePolicyAsset have the same InsurancePolicyId as the coverage's own InsurancePolicyId? Reject any mismatched rows before submission. A SOQL query joining InsurancePolicyAsset on InsurancePolicyId and comparing to the coverage file's policy reference can catch this pre-load.

---

## Gotcha 2: Bulk API 2.0 External ID Resolution is Case-Sensitive

**What happens:** Bulk API 2.0 external ID lookups are case-sensitive. A parent load file that writes `PREM-1042` and a child load file that references `prem-1042` produce a missing parent error on every mismatched row, even though the Premise record exists in the org. The API does not attempt case-insensitive matching and does not warn about near-misses.

**When it occurs:** Most commonly when source data comes from multiple legacy systems with different casing conventions, or when ETL transformations apply inconsistent case normalization to different object files. Also occurs when a re-extract produces values in different case than the original load.

**How to avoid:** Apply a consistent case normalization (uppercase recommended) to all external ID columns — both the own-key column and all parent-reference columns — in every load file before submission. Build the normalization into the ETL pipeline as a mandatory step, not a one-time fix.

---

## Gotcha 3: BillingStatement Inserts Blocked by Policy Status Validation

**What happens:** BillingStatement records referencing cancelled or expired InsurancePolicy records fail with validation rule errors if the org has rules that check InsurancePolicy.Status before allowing billing activity. Historical migrated policies frequently carry non-active statuses; the billing history for those policies cannot be loaded without bypassing these rules.

**When it occurs:** When migrating billing history for policies that were already cancelled, expired, or lapsed in the source system. The validation rule logic is designed for live transactional use and does not account for historical data migration scenarios.

**How to avoid:** Include BillingStatement in the automation bypass analysis before migration planning is finalized. Add the migration bypass flag to BillingStatement validation rules that check policy status. Test the bypass on a sample of cancelled policies in sandbox before full-volume load. Clear the bypass flag on all BillingStatement records after load is complete.

---

## Gotcha 4: ServiceAccount Requires Both Account and ServicePoint — Partial Loads Leave It Unloadable

**What happens:** ServiceAccount references both Account (the billing customer) and ServicePoint (the physical connection point). If the ServicePoint load completed only partially — for example, some ServicePoints failed due to missing Premise records — then any ServiceAccount row referencing a missing ServicePoint will also fail. Because ServiceAccount cannot be loaded until both parents are complete, a partial ServicePoint load blocks the entire ServiceAccount tier.

**When it occurs:** When the team tries to recover from a partial Premise or ServicePoint failure by skipping failed rows and continuing with ServiceAccount. The missing ServicePoint records create a gap that cascades.

**How to avoid:** Treat zero error rows as the mandatory gate condition before advancing to the next tier. If any Premise or ServicePoint rows fail, resolve those failures and re-run the failed rows before starting ServiceAccount. Keep a load tracking log that records confirmed success counts per tier to make gate checks explicit.

---

## Gotcha 5: InsurancePolicy External ID Field Must Be Created Before the Account Load, Not After

**What happens:** Teams often realize they need an external ID on InsurancePolicy only after the Account load is already complete. At that point, InsurancePolicy.Policy_External_ID__c does not exist yet, so the InsurancePolicy load file references a non-existent field. The job submission fails with a schema validation error, and the team must pause the migration to create the field, potentially delaying the cutover window.

**When it occurs:** When external ID field inventory is done incrementally (object by object) rather than upfront for the entire hierarchy. This is common when a practitioner reads the migration documentation one tier at a time.

**How to avoid:** Inventory and create all external ID fields for the entire object hierarchy — across all tiers — before any load job starts. The field creation step has no dependencies on data being present; it can be done in the target org as the first migration preparation step, well before any ETL extraction begins.
