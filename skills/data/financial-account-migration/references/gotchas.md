# Gotchas — Financial Account Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: RBL Apex Triggers Cause Row-Lock Errors During Bulk Insert

**What happens:** When loading FinancialHolding or FinancialAccountTransaction records in bulk, the FSC Rollup-by-Lookup Apex triggers fire synchronously on every inserted row and attempt to update the parent FinancialAccount record's aggregated balance fields. If multiple rows share the same parent FinancialAccount (which is the normal case — one account has many holdings), concurrent Bulk API workers race to lock the same parent row, generating `UNABLE_TO_LOCK_ROW` DML exceptions. The load job fails after a few hundred rows, and retrying without a fix reproduces the same error.

**When it occurs:** Any bulk DML against `FinServ__FinancialHolding__c` or `FinServ__FinancialAccountTransaction__c` in a managed-package FSC org where `FinServ__EnableRollupSummary__c` is true (the default). The error surfaces in Data Loader error logs and Bulk API job failure details as `UNABLE_TO_LOCK_ROW`.

**How to avoid:** Before the ETL job begins, disable RBL for the ETL integration user by setting `FinServ__EnableRollupSummary__c = false` in the `FinServ__WealthAppConfig__c` custom setting. After all loads complete, re-enable the setting and invoke `FinServ.RollupRecalculationBatchable` (batch size 200) to rebuild all aggregated values. Do not skip the recalculation step — account totals will remain stale until it runs.

---

## Gotcha 2: Balance History Storage Differs Between Managed Package and Core FSC

**What happens:** The managed-package FSC org stores account balance as a single overwritable field (`FinServ__Balance__c`) on FinancialAccount — there is no native snapshot history. Core FSC (API v61.0+) stores balance history as child `FinancialAccountBalance` records, with one row per point-in-time snapshot. A migration runbook written for one model produces silent data loss when applied to the other. Specifically, applying the single-field strategy to a Core FSC org results in no `FinancialAccountBalance` child records, empty trend charts, and incorrect analytics — with no load errors to indicate a problem.

**When it occurs:** Any time a practitioner migrates from a managed-package org environment (or uses a managed-package runbook) to a Core FSC deployment, or vice versa, without confirming which balance storage model applies.

**How to avoid:** Confirm the deployment model before any migration design. Check for the presence of the `FinServ__` namespace in the target org to identify managed-package; query the `FinancialAccountBalance` object availability to confirm Core FSC. Design balance migration around the correct model: multiple `FinancialAccountBalance` rows for Core FSC, single field write for managed package.

---

## Gotcha 3: FinancialSecurity Must Pre-Exist Before FinancialHolding Insert

**What happens:** `FinancialHolding` has a required lookup field (`FinancialSecurityId` in Core FSC; `FinServ__FinancialSecurity__c` in the managed package) that references the FinancialSecurity instrument master. If FinancialSecurity records for the referenced instruments do not already exist in the target org at the time of the FinancialHolding load, every FinancialHolding row that references a missing security fails with a foreign-key constraint error. The entire FinancialHolding batch is rejected, and the holding records are not created.

**When it occurs:** When migration teams treat FinancialSecurity as a subordinate lookup to be loaded later, or when source system terminology ("instrument", "product", "security master") is not mapped to the FSC FinancialSecurity object. Orgs that use pre-seeded instrument data (from a data vendor feed) may also have gaps between vendor-loaded securities and the positions in the migrated source.

**How to avoid:** Include FinancialSecurity in the pre-load phase — load it immediately after Account/PersonAccount and before FinancialAccount. Build a reconciliation step that compares the set of security identifiers (CUSIP, ISIN, ticker) present in the target FinancialSecurity object against the security references in the FinancialHolding source file. Resolve any gaps before starting the FinancialHolding load job.

---

## Gotcha 4: FinancialAccountTransaction Is a Standard Object in Core FSC, Not Always Custom

**What happens:** Practitioners accustomed to the managed-package FSC pattern know `FinServ__FinancialAccountTransaction__c` as a custom object in the `FinServ__` namespace. When building a Core FSC migration, they either target the wrong API name, attempt to create a replacement custom object, or look for the managed-package custom object and conclude that transactions are not supported. In Core FSC (API v61.0+), `FinancialAccountTransaction` is a first-class standard object — targeting the managed-package custom object name in a Core FSC org returns zero results or "object not found" errors.

**When it occurs:** Cross-model migrations, org-to-org migrations where source and target are on different FSC models, or when reusing a managed-package data mapping document in a Core FSC project.

**How to avoid:** Confirm the correct API name for each object against the target deployment model before building CSV column mappings or Data Loader job configurations. Use `sf sobject describe --sobject FinancialAccountTransaction` to verify object availability and field names in the target org.

---

## Gotcha 5: Primary Owner Role Must Exist Before FinancialHolding

**What happens:** FSC business logic and certain validation rules assume that a FinancialAccount has at least one `FinancialAccountRole` record with `Role = Primary Owner` before holdings or transactions are loaded. In some orgs, missing or incomplete role records cause trigger errors or silent exclusion of accounts from household rollups even after recalculation runs.

**When it occurs:** When FinancialAccountRole records are loaded out of order (after FinancialHolding), or when the Primary Owner role is omitted from the migration scope because it was not explicitly modeled in the source system.

**How to avoid:** Load FinancialAccountRole records — at minimum the Primary Owner for each FinancialAccount — immediately after the FinancialAccount load and before FinancialHolding. Verify role completeness with a SOQL count query after the role load and before proceeding.
