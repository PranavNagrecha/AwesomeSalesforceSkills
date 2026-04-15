---
name: industries-data-migration
description: "Use this skill when bulk-migrating data into Salesforce Industries clouds — including InsurancePolicy and its child objects for Insurance, ServicePoint/Premise for Energy and Utilities, or subscriber/account hierarchies for Communications. Trigger keywords: insurance policy migration, InsurancePolicyCoverage load order, ServicePoint bulk load, Premise hierarchy, E&U data migration, telco subscriber migration, utility account import, industries object dependency. NOT for generic Salesforce data migration planning, FSC FinancialAccount migration, Health Cloud patient data migration, or Experience Cloud user migration."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "What is the correct load order for migrating insurance policy data including coverages and transactions into Salesforce Insurance?"
  - "How do I bulk load ServicePoint and Premise records into Energy and Utilities Cloud without foreign-key failures?"
  - "My InsurancePolicyCoverage inserts are failing because the parent InsurancePolicy or asset record does not exist yet — what is the correct sequence?"
  - "What external ID fields do I need on InsurancePolicy, Premise, and ServicePoint to run a re-runnable upsert migration?"
  - "How do I migrate subscriber account hierarchies or telco service records into Salesforce Communications Cloud?"
tags:
  - insurance
  - energy-utilities
  - industries
  - data-migration
  - bulk-load
  - external-id
  - load-order
inputs:
  - "Source system export files (CSV or equivalent) for all objects in scope — policies, coverages, assets, transactions, or utility service records"
  - "Target Industries cloud: Insurance, Energy and Utilities, or Communications"
  - "Org credentials and Salesforce CLI / Data Loader / Bulk API 2.0 access"
  - "External ID field names or migration ID strategy for each object in the hierarchy"
  - "Confirmation of whether Industry-specific automation (triggers, flows) should be suppressed during load"
outputs:
  - "Fully sequenced bulk load plan covering all object tiers with dependency notes"
  - "External ID field strategy for each intermediate object in the hierarchy"
  - "Pre-load and post-load checklist (automation suppression, validation rule bypass, rollback steps)"
  - "Data mapping table from source fields to target Industries object API names"
dependencies:
  - data/data-migration-planning
  - data/industries-data-model
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Industries Data Migration

This skill covers bulk migration execution for Salesforce Industries clouds — specifically the mandatory multi-tier object load sequences for Insurance (InsurancePolicy through BillingStatement), Energy and Utilities Cloud (Account through ServicePoint and ServiceAccount), and Communications Cloud subscriber hierarchies. It provides load ordering, external ID strategy, and automation-suppression guidance for each cloud. It does not cover generic Salesforce migration planning, FSC FinancialAccount objects, Health Cloud patient data, or Experience Cloud user provisioning — use the dedicated skills for those domains.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Identify the target Industries cloud** — Insurance, Energy and Utilities (E&U), or Communications. Each cloud has its own mandatory object hierarchy and the load sequences are not interchangeable.
- **Map the full object hierarchy before any load begins** — Industries objects are strictly hierarchical. Every intermediate object (Premise, InsurancePolicy, ServicePoint) must exist before child records reference it. Attempting a single-pass flat load fails silently or produces orphaned records.
- **Confirm external ID coverage** — Each object tier in the hierarchy requires its own external ID field. Using only Account as the anchor is the most common anti-pattern. Verify that custom external ID fields have been created and are populated in source extract files before the first load job runs.
- **Check which automation is active** — Insurance Policy triggers, E&U ServicePoint validation rules, and Industries-standard flows may reject bulk-loaded records that lack data present in real transactional flows. Plan to suppress or bypass these before load.

---

## Core Concepts

### 1. Insurance Cloud: Four-Tier Mandatory Load Order

Insurance data in Salesforce Insurance (formerly Financial Services Cloud Insurance) is organized in a strict parent-child hierarchy. The correct order is:

1. **Account / PersonAccount** — the policyholder. Every InsurancePolicy requires an Account owner.
2. **InsurancePolicy** — the top-level policy record. References Account. Must exist before any participant, asset, coverage, or transaction record can be inserted.
3. **InsurancePolicyParticipant** and **InsurancePolicyAsset** — participants (insured parties, beneficiaries) and covered assets (vehicles, properties) that belong to the policy. Both reference InsurancePolicy. Load these at the same tier; neither depends on the other.
4. **InsurancePolicyCoverage** — coverage records that describe what is covered and at what limit. References InsurancePolicy, and optionally InsurancePolicyAsset. Must be loaded after assets if the coverage is asset-specific.
5. **InsurancePolicyTransaction** and **BillingStatement** — transaction history (premiums, endorsements, cancellations) and billing records. Both reference InsurancePolicy and are the final tier.

Inverting any step creates referential integrity failures. InsurancePolicyCoverage inserted before InsurancePolicy will fail with a missing parent lookup error. InsurancePolicyTransaction loaded before InsurancePolicyCoverage may succeed technically but will produce data that is structurally inconsistent with how the platform populates these relationships in live usage.

### 2. Energy and Utilities Cloud: Three-Tier Utility Hierarchy

Energy and Utilities Cloud (E&U) organizes utility service data in a three-tier parent chain:

1. **Account** — the customer record. Every Premise and ultimately every service record traces back to an Account.
2. **Premise** — the physical service location (address, meter site). References Account. Must exist before ServicePoint or any service record is created.
3. **ServicePoint** — the individual connection point at a Premise (electric meter, gas meter). References Premise. Must exist before ServiceAccount or billing/usage records can reference it.
4. **ServiceAccount** — links an Account to a ServicePoint for billing and service purposes. Depends on both Account and ServicePoint. Load after both parents are confirmed present.

The three-tier chain (Account → Premise → ServicePoint → ServiceAccount) is mandatory. Loading ServicePoint records before Premise exists will fail. Loading ServiceAccount before ServicePoint exists will fail. There is no platform workaround — the foreign-key constraints enforce this at the database layer.

### 3. External ID Strategy: One Field Per Tier

The most common migration failure mode in Industries objects is using Account's external ID as the sole anchor for all upsert operations. This works at the Account tier but fails the moment you need to upsert InsurancePolicyCoverage records that reference an InsurancePolicy that was itself just loaded.

Each object tier that will be referenced as a parent by a child tier in the same migration must carry its own external ID field. The required minimum for an Insurance migration is:

| Object | Purpose of external ID |
|---|---|
| Account | Anchor for InsurancePolicy parent lookup |
| InsurancePolicy | Anchor for InsurancePolicyCoverage, InsurancePolicyParticipant, InsurancePolicyAsset, InsurancePolicyTransaction lookups |
| InsurancePolicyAsset | Anchor for asset-specific InsurancePolicyCoverage lookups (if coverages are asset-specific) |

For E&U, the required minimum is:

| Object | Purpose of external ID |
|---|---|
| Account | Anchor for Premise parent lookup |
| Premise | Anchor for ServicePoint parent lookup |
| ServicePoint | Anchor for ServiceAccount parent lookup |

All external ID fields must be created in the target org as custom fields with the **External ID** flag checked before any load job runs.

### 4. Automation Suppression During Bulk Load

Industries clouds ship with Apex triggers, validation rules, and flows that enforce business logic appropriate for transactional data entry. During bulk migration, records arrive out of the normal business process flow and may not satisfy all validation conditions (e.g., required coverage effective dates, premium calculation fields). Common suppression strategies:

- **Permission set / custom field bypass** — Add a boolean custom field (e.g., `Migration_Bypass__c`) to the object and update validation rules to skip when this field is true. Populate the field in your load file, then clear it post-load via a separate update job.
- **Dedicated ETL integration user** — Use a separate integration user whose profile bypasses selected validation rules via the standard Salesforce validation rule user criteria.
- **Trigger disablement** — Custom Apex triggers for Industries clouds can be disabled at the class level via Custom Settings or Custom Metadata during the migration window. Review which triggers exist before deciding on the approach.

Do not disable platform-enforced referential integrity checks (foreign key lookups) — these are not bypassable and the load sequence must satisfy them.

---

## Common Patterns

### Pattern A: Insurance Four-Pass Sequential Load

**When to use:** Any migration that includes InsurancePolicyCoverage, InsurancePolicyTransaction, or BillingStatement records.

**How it works:**
1. Load Account / PersonAccount records with an external ID field. Confirm success before proceeding.
2. Load InsurancePolicy with Account external ID as the parent reference. Confirm all rows succeed.
3. Load InsurancePolicyParticipant and InsurancePolicyAsset in parallel passes (both reference only InsurancePolicy). If coverages are asset-specific, confirm InsurancePolicyAsset is complete before loading InsurancePolicyCoverage.
4. Load InsurancePolicyCoverage referencing InsurancePolicy external ID (and InsurancePolicyAsset external ID where applicable).
5. Load InsurancePolicyTransaction and BillingStatement referencing InsurancePolicy external ID.

**Why not the alternative:** A single-pass upsert with all objects interleaved fails because Salesforce resolves parent lookups at insert time. A row referencing an InsurancePolicy that has not yet been committed in the same batch fails with a missing parent error regardless of the row order within the file.

### Pattern B: E&U Three-Tier Sequential Load

**When to use:** Any migration that includes ServicePoint, ServiceAccount, or usage/billing records for Energy and Utilities Cloud.

**How it works:**
1. Load Account records with an external ID field. Confirm all rows committed.
2. Load Premise records with Premise external ID field and Account external ID as the parent reference.
3. Load ServicePoint records with ServicePoint external ID field and Premise external ID as the parent reference.
4. Load ServiceAccount records referencing both Account external ID and ServicePoint external ID.

**Why not the alternative:** Flattening the load into a single file ordered by Account ID does not work. The Bulk API processes rows in parallel within a batch; a ServicePoint row and its parent Premise row cannot be guaranteed to commit in order within the same job. Separate sequential jobs are required.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| InsurancePolicyCoverage inserts failing with parent lookup errors | Verify InsurancePolicy load completed successfully; re-run coverage load only after confirmation | InsurancePolicyCoverage requires InsurancePolicy to exist; partial policy load leaves orphans |
| Asset-specific coverages and non-asset coverages in same file | Split into two loads: asset coverages after InsurancePolicyAsset is confirmed, non-asset coverages earlier | Mixing parent reference types in one file creates lookup ambiguity |
| ServicePoint inserts failing with missing Premise | Check that Premise external ID in ServicePoint file exactly matches the value loaded in the Premise job | Case-sensitive external ID mismatch is the most common cause |
| Validation rules blocking migration records | Add bypass flag to load file; update validation rule to skip when flag is true; clear flag post-load | Disabling rules org-wide risks live data; targeted bypass is safer |
| Re-runnable upsert vs insert for subsequent loads | Use Bulk API 2.0 upsert on external ID fields for all object tiers | Upsert is idempotent; pure inserts create duplicates on rerun |
| Communications subscriber hierarchy migration | Follow the same multi-tier sequencing: Account → ServiceAccount → SubscriberService → usage records | Telco objects follow the same parent-before-child constraint |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the target Industries cloud and map the full object hierarchy** — Determine whether the migration targets Insurance, Energy and Utilities, or Communications objects. Draw the complete parent-child dependency graph for every object in scope. Confirm which objects are in scope and which are out of scope before building load files.
2. **Create external ID fields on every intermediate object tier** — Create custom external ID fields in the target org for each object that will be referenced as a parent by a child object in the hierarchy. Populate these fields in the source extract files before any load job runs. Do not rely on Account external ID alone.
3. **Prepare source extract files in tier order** — Produce one CSV file per object, pre-populated with the appropriate external ID values and parent external ID references. Validate that parent external IDs in child files match exactly (case and format) the values written in the parent file.
4. **Configure automation suppression before the first load** — Identify active validation rules, Apex triggers, and flows that will reject migration records. Implement the agreed bypass strategy (bypass flag, integration user, or trigger custom setting). Test the bypass on a small sample load in a sandbox before full-volume load.
5. **Execute loads in strict dependency order and confirm each tier before proceeding** — Run each load job, wait for full completion, and verify zero error rows before starting the next tier. Do not start an InsurancePolicyCoverage job while the InsurancePolicy job is still processing.
6. **Clear bypass flags and re-enable automation post-load** — After all tiers complete successfully, run a separate update job to clear any bypass flags. Re-enable suppressed triggers or validation rules. Confirm the org's automation is fully restored.
7. **Validate record counts and spot-check relationships** — Query record counts per object and compare to source extract row counts. For a sample of policies or utility accounts, verify that all child records (participants, coverages, transactions; or premises, service points, service accounts) are correctly related and visible in the UI.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] External ID fields exist and are indexed on every intermediate object in the hierarchy (not just Account)
- [ ] Load files contain the correct parent external ID references matching exactly what was written in the parent tier
- [ ] Each tier was loaded and confirmed successful (zero error rows) before the next tier started
- [ ] Automation bypass strategy was implemented and tested on a sandbox sample before full-volume load
- [ ] Bypass flags were cleared and automation was restored after all tiers completed
- [ ] Record counts reconcile between source extract files and target org for all object tiers
- [ ] Spot-check of 5–10 parent records confirms all expected child records are present and correctly related

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **InsurancePolicyCoverage silently accepts an invalid InsurancePolicyAsset reference** — If `InsurancePolicyAssetId` is populated but the referenced asset does not belong to the same InsurancePolicy, the platform may accept the insert but the coverage will not display correctly in the policy detail view. Always validate that the asset external ID in the coverage file refers to an asset loaded under the same policy.
2. **Premise external ID mismatch is case-sensitive** — Bulk API 2.0 external ID resolution is case-sensitive. If the Premise load file used `PREM-001` and the ServicePoint load file references `prem-001`, the ServicePoint insert will fail with a missing parent error even though a matching Premise exists. Normalize case in all external ID columns before generating load files.
3. **BillingStatement requires InsurancePolicy to be in an active status** — Depending on org configuration, BillingStatement inserts may be blocked by validation rules or triggers that check `InsurancePolicy.Status`. Historical policy records migrated with a `Cancelled` or `Expired` status may fail BillingStatement loads if the validation rule does not account for migration bypass. Include BillingStatement in the automation bypass analysis.
4. **ServiceAccount requires both Account and ServicePoint to exist at insert time** — Unlike most child objects that reference only one parent, ServiceAccount references both Account (the billing customer) and ServicePoint (the connection point). Both must be fully committed before the ServiceAccount job starts. A partial Premise or ServicePoint load leaves ServiceAccount inserts with broken lookups.
5. **Bulk API 2.0 upsert on external ID does not update the external ID field itself** — If the external ID field contains the wrong value and you attempt to correct it via a upsert, the upsert key lookup finds no match and creates a new record instead of updating the existing one. To correct an external ID field value, use a standard update (not upsert) targeted by Salesforce record ID.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Tiered load sequence table | Ordered list of all objects to load with tier number, object API name, parent reference fields, and external ID field names |
| External ID field inventory | List of custom external ID fields to create per object, with field API name and whether it is unique/required |
| Automation bypass specification | List of validation rules, triggers, and flows to suppress, bypass method used, and restoration steps |
| Load job result log template | Table to record job ID, object name, total rows, success count, error count, and confirmation status for each tier |
| Post-load validation query set | SOQL queries to verify record counts and spot-check parent-child relationships for each object tier |

---

## Related Skills

- `data/data-migration-planning` — use for overall migration sequencing strategy, tool selection (Bulk API 2.0 vs Data Loader vs Apex), and rollback planning before executing any Industries-specific load
- `data/industries-data-model` — use to identify correct API names, relationship fields, and field-level constraints for Insurance and E&U objects before building data mappings
- `data/financial-account-migration` — use instead of this skill when the migration targets FSC FinancialAccount, FinancialHolding, or FinancialAccountTransaction objects
- `data/patient-data-migration` — use instead of this skill when the migration targets Health Cloud patient records
