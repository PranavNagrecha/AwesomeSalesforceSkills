# Gotchas — Historical Order Migration

Non-obvious Salesforce CPQ platform behaviors that cause real production problems during historical order migration.

## Gotcha 1: Batch Size > 1 Silently Bypasses CPQ Renewal-Preparation Logic

**What happens:** When SBQQ__Subscription__c or SBQQ__Asset__c records are inserted via Bulk API 2.0, Data Loader, or any ETL tool with batch size greater than 1, CPQ's package triggers run in bulk mode and skip the per-record renewal-preparation logic. The records insert without errors and appear correct in SOQL queries. The internal renewal fields that CPQ populates during the trigger (used by the renewal engine to generate quote lines) are never set.

**When it occurs:** Whenever the batch size for CPQ Legacy Data Upload objects is not explicitly set to 1. Default batch sizes in Data Loader (200) and Bulk API 2.0 are far above the required limit. This is the most common cause of blank renewal quote lines after a historical CPQ migration.

**How to avoid:** Set batch size to 1 for every job loading SBQQ__Quote__c, SBQQ__QuoteLine__c, SBQQ__Subscription__c, and SBQQ__Asset__c during Legacy Data Upload. In Data Loader, set `Batch size` = 1 in the Settings dialog before each import job. In custom ETL scripts, process records one at a time using the Salesforce REST API (`/services/data/vXX.0/sobjects/SBQQ__Subscription__c`) rather than Bulk API 2.0 for these objects.

---

## Gotcha 2: SBQQ__Asset__c Root Id Must Be Null When Revised Asset Is Populated

**What happens:** `SBQQ__Asset__c.SBQQ__RootId__c` and `SBQQ__Asset__c.SBQQ__RevisedAsset__c` are mutually exclusive for revised assets. If both fields are populated, CPQ does not reject the record — it inserts successfully. The corruption is invisible in the data. At the first amendment or renewal that touches the asset, CPQ traverses both chains simultaneously and generates duplicate amendment quote lines or creates an infinite loop in the asset chain traversal.

**When it occurs:** During migrations from source systems that store both the root asset pointer and the immediate predecessor pointer on every asset record. Teams map both source fields directly to CPQ fields without knowing that CPQ treats them as exclusive on revised assets.

**How to avoid:** Apply this rule during CSV preparation: if `SBQQ__RevisedAsset__c` is non-null, set `SBQQ__RootId__c` to blank/null before loading. Run a pre-load check: `SELECT Id FROM SBQQ__Asset__c WHERE SBQQ__RootId__c != null AND SBQQ__RevisedAsset__c != null` should return zero rows after load.

---

## Gotcha 3: CPQ Legacy Data Upload Only Works for Contract-Based Renewal Model

**What happens:** CPQ supports two renewal models: contract-based and asset-based. Legacy Data Upload procedures — the batch size 1 requirement, the Subscription record structure, the Quote approval flags — are defined and tested exclusively for the contract-based model. In an asset-based renewal org, SBQQ__Subscription__c records loaded via Legacy Data Upload may insert without errors but will not participate in the renewal generation process because asset-based renewals derive renewal lines from SBQQ__Asset__c records, not Subscription records.

**When it occurs:** When a migration team applies Legacy Data Upload procedures to an org where `SBQQ__RenewalModel__c` is set to `Asset Based` in the CPQ package settings. The resulting subscriptions look correct but are functionally dead from a renewal perspective.

**How to avoid:** Before any load begins, query the CPQ package settings: `SELECT SBQQ__RenewalModel__c FROM SBQQ__CustomAction__c` or navigate to CPQ Package Settings in Setup and confirm the Renewal Model field. If the org uses asset-based renewals, consult the CPQ Asset-Based Renewal documentation separately — the migration approach is fundamentally different.

---

## Gotcha 4: CPQ Price Rules and Product Rules Fire During Data Load

**What happens:** CPQ price rules and product rules are triggered on every SBQQ__Quote__c and SBQQ__QuoteLine__c save, including during data loads. A price rule configured to recalculate net price based on a discount schedule will overwrite the historically correct price being loaded from the source system with a price calculated by the current org's pricing configuration. The overwritten price is stored on the record with no indication that a rule modified it.

**When it occurs:** Whenever price or product rules are active during the Legacy Data Upload. Many teams discover this problem when post-load validation reveals that loaded net prices differ from source prices — sometimes by significant amounts for records with applicable discount schedules.

**How to avoid:** Disable price rules and product rules in CPQ Package Settings before any Quote or Quote Line records are inserted. Re-enable them only after the full load is validated. Document the current rule configuration before disabling so it can be restored exactly. Some orgs also have CPQ-triggered Flows on Quote objects — audit Flow configuration to ensure no automation overwrites pricing during load.

---

## Gotcha 5: Contract Must Be Activated Before Subscriptions Participate in Renewal

**What happens:** SBQQ__Subscription__c records linked to a Contract in `Draft` status are not treated as active subscriptions by CPQ's renewal engine. CPQ only generates renewal opportunities for contracts with `Status = Activated`. If historical contracts are left in Draft after the migration — whether intentionally or by oversight — the renewal engine will not fire for them at the subscription end date.

**When it occurs:** When the migration team loads Contract records in Draft status (the default) and does not update them to Activated after the load. This is especially common when the Contract `Status` field was not explicitly mapped in the migration CSV, defaulting to Draft on all inserted records.

**How to avoid:** After all Subscription records are loaded and validated for a given Contract, update the Contract `Status` to `Activated` if the subscription term has already started. Build this step explicitly into the load sequence: Contracts are inserted in Draft, Subscriptions are loaded and validated, then Contracts are updated to Activated in a final step before the migration wave is marked complete.

---

## Gotcha 6: SBQQ__Quote__c Without Approved + Primary Flags Is Invisible to CPQ Renewal Engine

**What happens:** The CPQ renewal engine, when generating a renewal opportunity for an expiring contract, looks for an `SBQQ__Quote__c` linked to the Contract where `SBQQ__Status__c = Approved` and `SBQQ__Primary__c = true`. If the historical Quote was loaded with Draft status or `Primary = false`, the renewal engine finds no qualifying quote and generates a renewal opportunity with blank or default product lines, ignoring the subscription records entirely.

**When it occurs:** When historical CPQ Quotes are inserted with default field values (`Status = Draft`, `Primary = false`) because the migration team treats the Quote as a data-only record rather than a functional CPQ anchor.

**How to avoid:** Always insert historical SBQQ__Quote__c records with `SBQQ__Status__c = Approved` and `SBQQ__Primary__c = true`. These values are technical markers required by the renewal engine, not workflow status indicators. Include explicit column mappings for both fields in every Quote CSV prepared for Legacy Data Upload.
