---
name: opportunity-pipeline-migration
description: "Use when migrating historical Opportunity records into Salesforce — covering stage history recreation, amount and close date mapping, product line item load sequencing (Product2 → Price Book → OpportunityLineItem), team member (OpportunityTeamMember) and revenue split (OpportunitySplit) loading, and Pricebook2 assignment. NOT for generic multi-object data migration planning (use data-migration-planning). NOT for ongoing CRM sync or ETL pipeline architecture. NOT for opportunity record type or sales process configuration."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Performance
triggers:
  - "how do I migrate opportunity stage history from our legacy CRM into Salesforce"
  - "loading opportunity line items fails with price book errors after migrating opportunities"
  - "how do I load opportunity products and keep the correct amounts and unit prices from our old system"
  - "OpportunitySplit load failing after opportunity migration — what order do I load revenue splits"
  - "how do I recreate opportunity pipeline history in Salesforce after cutover"
  - "migrating won and lost opportunities from Dynamics to Salesforce with historical close dates"
tags:
  - opportunity
  - pipeline-migration
  - opportunitylineitem
  - opportunityhistory
  - opportunitysplit
  - opportunityteammember
  - pricebook
  - bulk-api
  - data-migration
  - stage-history
inputs:
  - "Source opportunity data export: fields for Name, AccountId, StageName, Amount, CloseDate, Probability, Type, OwnerId, Pricebook2Id (or equivalent)"
  - "Product and pricing data: Product2 catalog, standard Price Book Entry prices, custom Price Book Entry prices"
  - "Stage history export: prior stage values and stage-change dates per opportunity (from source CRM audit log)"
  - "Team member assignments: user IDs, team roles, opportunity access levels"
  - "Revenue split configuration: SplitType names and percentages per team member"
  - "Org configuration: active Price Books, OpportunitySplits enabled flag, forecast categories per stage"
  - "External ID fields on Opportunity, Product2, and Account for cross-reference upserts"
outputs:
  - "Load sequence specification: Product2 → Standard PBE → Custom PBE → Opportunity (with Pricebook2Id) → OpportunityLineItem → OpportunityTeamMember → OpportunitySplit"
  - "CSV column mapping for each object aligned to Bulk API 2.0 upsert format"
  - "Stage history approximation strategy (Activity or Task records noting historical stages, since OpportunityHistory is read-only)"
  - "Pricebook2 assignment verification checklist"
  - "OpportunitySplit pre-load configuration checklist (SplitType and feature flag)"
  - "Post-migration validation queries for amount totals, line item counts, and team member coverage"
  - "Completed opportunity-pipeline-migration-template.md"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Opportunity Pipeline Migration

This skill activates when a practitioner needs to migrate historical Opportunity records — including products, line items, team members, and revenue splits — from a legacy system into Salesforce. It covers the strict object load sequence required by Salesforce referential integrity, the read-only constraint on OpportunityHistory, Price Book assignment mechanics, and the prerequisite configuration steps for OpportunitySplit.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Price Book inventory**: Which Price Books are active in the target org? Every Opportunity must be assigned a valid `Pricebook2Id` before its OpportunityLineItems can be inserted. The standard Price Book always exists; custom Price Books must be configured before the migration.
- **OpportunitySplits enabled**: Is Opportunity Splits enabled in the org (Setup > Opportunity Splits)? If not, OpportunitySplit records cannot be loaded at all. Enabling Splits also requires at least one SplitType to be configured and active before the first split record is inserted.
- **OpportunityHistory is read-only**: The OpportunityHistory object (which stores StageName change history) is system-generated and cannot be directly inserted via API. This is the most common wrong assumption — practitioners attempt to insert historical stage records and receive "Object not insertable" errors. Historical stage data must be preserved through a workaround (see Core Concepts).
- **Forecast category derives from StageName**: `ForecastCategoryName` on Opportunity is not a freely settable field — it is derived from the StageName-to-ForecastCategory mapping in the org's Sales Process configuration. Load the correct `StageName` and the forecast category follows automatically.
- **Key limits in play**: OpportunityLineItem requires both a valid `OpportunityId` and a valid `PricebookEntryId` — both parent records must exist before any line item row is inserted. OpportunityTeamMember requires the parent Opportunity to exist. OpportunitySplit requires both the Opportunity and the OpportunityTeamMember to exist.

---

## Core Concepts

### Load Sequence: Strict Dependency Order

Salesforce enforces referential integrity at insert time. Inserting a record that references a non-existent parent causes the row to fail immediately. For Opportunity pipeline migrations, the required load sequence is:

1. **Product2** — the product catalog records that Price Book Entries reference
2. **Standard Price Book Entry** (PricebookEntry with `IsStandard = true` Pricebook2) — every product must have a Standard Price Book Entry before it can have a custom Price Book Entry
3. **Custom Price Book Entry** (PricebookEntry with a custom Pricebook2Id) — required if Opportunities reference a non-standard Price Book
4. **Opportunity** (with `Pricebook2Id` populated) — must be assigned to a Price Book at load time if line items will be loaded; cannot change Price Book after line items exist
5. **OpportunityLineItem** — references both `OpportunityId` and `PricebookEntryId`; both must exist
6. **OpportunityTeamMember** — references `OpportunityId` and `UserId`; Opportunity must exist
7. **OpportunitySplit** — references `OpportunityId` and `SplitOwnerId`; requires Splits enabled and SplitType configured

Violating this order (for example, loading OpportunityLineItems before Opportunities, or loading custom Price Book Entries before Standard Price Book Entries for the same product) causes batch failures that are difficult to diagnose if the sequence is not documented.

### OpportunityHistory: Read-Only and System-Generated

`OpportunityHistory` is a child object of Opportunity that Salesforce automatically creates whenever certain tracked fields — most importantly `StageName`, `Amount`, `CloseDate`, `Probability`, and `ForecastCategory` — are edited on an Opportunity record. It is a read-only object: the Salesforce API returns `sObject not insertable` if a direct insert is attempted via Bulk API 2.0 or SOAP API.

`OpportunityFieldHistory` is similarly read-only and tracks field-level changes with old and new values.

**Workaround for preserving historical stage data:**

Since stage history cannot be directly inserted, practitioners have two options:

**Option A — Task/Activity notes (recommended):** For each historical stage transition in the source export, create a Task record (or a custom object record) on the Opportunity that records the stage name, the date of the transition, and relevant context (e.g., "Stage as of 2024-06-15: Proposal/Price Quote — $45,000"). This preserves the information in a queryable, reportable form even though it does not appear in the standard Stage History related list.

**Option B — Multiple sequential updates (expensive but produces real history):** Insert the Opportunity with its earliest historical stage, then issue a series of update operations on the Opportunity record, changing `StageName` (and optionally `Amount` and `CloseDate`) sequentially through each historical state. Each update triggers Salesforce to create an OpportunityHistory record automatically. This approach is technically accurate but multiplies API call volume by the number of stage transitions per opportunity and is only practical for moderate record volumes.

### Pricebook2 Assignment and Price Book Entry Matching

An Opportunity must have its `Pricebook2Id` set before any OpportunityLineItems are inserted. The `Pricebook2Id` on an Opportunity cannot be changed after line items exist without first deleting the line items.

PricebookEntry records link a Product2 to a specific Price Book with a specific `UnitPrice`. When inserting an OpportunityLineItem, the `PricebookEntryId` must reference a PricebookEntry that belongs to the **same Price Book** as the Opportunity's `Pricebook2Id`. If the Opportunity references the standard Price Book but the PricebookEntryId references a custom Price Book Entry, the insert fails with a field integrity error.

For migrations using a custom Price Book, the load sequence for pricing data is:
1. Ensure Product2 records exist (insert or upsert)
2. Create a Standard Price Book Entry for each product (required by Salesforce even if you never use the standard Price Book)
3. Create the custom Price Book Entry for each product with the correct `UnitPrice`
4. Load Opportunities referencing the custom `Pricebook2Id`
5. Load OpportunityLineItems referencing the custom Price Book Entry IDs

### OpportunitySplit Prerequisites

OpportunitySplit tracks how Opportunity revenue is divided among team members for forecast and compensation purposes. Before any OpportunitySplit records can be loaded:

1. **Feature must be enabled**: Setup > Opportunity Splits > Enable Opportunity Splits. This is an irreversible action in production.
2. **SplitType must be configured**: At least one SplitType (e.g., "Revenue Split") must exist and be Active. SplitType records are system-managed but their active/inactive state is configurable.
3. **OpportunityTeamMember must exist first**: Each split record references a `SplitOwnerId` (a User) and an `OpportunityId`. While OpportunityTeamMember is not a direct parent of OpportunitySplit in the schema, the best practice is to load team members before splits to ensure the user-opportunity relationship is established.
4. **Splits must sum to 100% per SplitType**: If the org enforces split percentage validation, loading splits that do not sum to 100% per opportunity per SplitType will fail validation.

---

## Common Patterns

### Pattern: Full Product Line Item Migration with Custom Price Book

**When to use:** The source system had its own product catalog and pricing that maps to Salesforce products. Opportunities had line items with unit prices and quantities.

**How it works:**
1. Export source product catalog. Map to Product2 fields: `Name`, `ProductCode`, `Description`, `IsActive`, and a `Legacy_Product_Id__c` External ID field.
2. Upsert Product2 records via Bulk API 2.0 using `Legacy_Product_Id__c` as the external ID.
3. Insert Standard Price Book Entries: for each Product2, create a PricebookEntry row with the standard Pricebook2Id (query via `SELECT Id FROM Pricebook2 WHERE IsStandard = true`) and a nominal `UnitPrice` (can be $0 if standard list price is unused).
4. Insert custom Price Book Entries: for each Product2, create a PricebookEntry row with the custom `Pricebook2Id` and the actual `UnitPrice` from the source export.
5. Upsert Opportunities with `Pricebook2Id` set to the custom Price Book Id.
6. Insert OpportunityLineItems: map source line items to `OpportunityId`, `PricebookEntryId`, `Quantity`, `UnitPrice`, and `TotalPrice`. Use `Opportunity.Legacy_Opportunity_Id__c` cross-reference notation in the CSV to avoid pre-resolving Salesforce IDs.

**Why not load line items with `Pricebook2Id` left blank on Opportunity:** Salesforce requires a Pricebook2Id on the Opportunity before OpportunityLineItems can be inserted. If the Opportunity has no Price Book, the line item insert fails with "FIELD_INTEGRITY_EXCEPTION: pricebook entry does not exist or is not available."

### Pattern: Stage History Approximation via Task Records

**When to use:** The source CRM has a stage history audit log and the business wants historical stage data preserved in Salesforce even though OpportunityHistory is not directly insertable.

**How it works:**
1. Export the stage history audit log from the source system. Each row should contain: Opportunity external ID, stage name, date of stage change, and the user who made the change.
2. For each stage history row, create a Task record: `WhatId` = Opportunity Salesforce ID (resolved via external ID cross-reference), `Subject` = "Historical Stage: <StageName>", `ActivityDate` = stage change date, `Description` = full context, `Status` = "Completed", `OwnerId` = user who made the change.
3. Load Tasks via Bulk API 2.0 after Opportunities are loaded (Tasks require a valid `WhatId`).
4. Optionally, load a custom object (e.g., `Opportunity_Stage_History__c`) that stores the data in a more structured, reportable format.

**Why not attempt OpportunityHistory insert:** The API returns `INVALID_TYPE_FOR_OPERATION: entity type Opportunity History does not support create` — this is not a permissions issue; it is a platform constraint.

### Pattern: Sequential Stage Updates for True History

**When to use:** Source system has fewer than 5 stage transitions per opportunity on average, and total opportunity count is under 50,000. Business requires the native Stage History related list to reflect historical stages.

**How it works:**
1. Load all Opportunities with the **earliest** historical StageName (not the current stage).
2. Build an ordered update CSV for each subsequent stage transition, sorted by transition date ascending per opportunity.
3. Issue a Bulk API 2.0 update job for each stage "wave" — opportunities that had a transition at a given point in time.
4. Each update to `StageName` on an Opportunity causes Salesforce to auto-generate an OpportunityHistory record.
5. After all stage updates, issue a final update to set `StageName` to the current stage.

**Why this is expensive:** For 10,000 opportunities with an average of 4 stage transitions, this requires 5 load operations (1 insert + 4 update waves) instead of 1. At 150M API rows per day, this is feasible for moderate volumes but requires careful job orchestration.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need historical stage data in native Stage History related list | Sequential update waves per stage transition | Each StageName update auto-generates OpportunityHistory row |
| Need historical stage data but volume is too high for update waves | Task records per stage transition | Preserves data in queryable, lightweight form without API multiplication |
| Opportunities had products in source system | Full Product2 → PBE → OLI sequence | Required by referential integrity and Price Book matching rules |
| Opportunities had no products / no line items | Skip Product2 and PBE steps; do not set Pricebook2Id unless required | Unnecessary steps add complexity without benefit |
| Revenue splits need to be migrated | Enable Splits, configure SplitType, load TeamMembers first, then Splits | Splits require feature flag + SplitType before any split record can exist |
| Source Opportunity stages don't match target org stages | Map source stages to target StageName values before load | StageName must match an existing Stage in the org's Sales Process exactly |
| Opportunity amounts must match source exactly | Load `Amount` directly; do not rely on line item rollup to compute it | If no line items exist, Amount is editable. If line items exist, Amount is calculated — load OLI UnitPrice × Quantity to drive the total |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Confirm prerequisites**: Verify Price Books exist and are active, confirm OpportunitySplits feature flag status, confirm SplitType configuration if splits are required, confirm all Opportunity StageName values in the source export match stage names in the target org's Sales Process.
2. **Design external IDs and CSV structure**: Create `Legacy_Opportunity_Id__c` on Opportunity, `Legacy_Product_Id__c` on Product2, and confirm `Pricebook2Id` resolution strategy. Prepare CSV files for each object in load order.
3. **Load Product2 and Price Book Entries**: Upsert Product2 records, then insert Standard Price Book Entries, then insert custom Price Book Entries (if applicable). Verify counts after each step before proceeding.
4. **Load Opportunities**: Upsert Opportunities with `Pricebook2Id` set. Confirm all Opportunities loaded successfully before proceeding to children.
5. **Load OpportunityLineItems**: Insert line items with `PricebookEntryId` referencing the same Price Book as the parent Opportunity's `Pricebook2Id`. Spot-check Amount totals against source.
6. **Load stage history approximation**: If using Task records, insert Tasks referencing Opportunity via `WhatId`. If using sequential updates, execute update waves in chronological order.
7. **Load OpportunityTeamMember then OpportunitySplit**: Insert team members first, then splits. Validate that split percentages sum to 100% per opportunity per SplitType before loading.

---

## Review Checklist

Run through these before marking opportunity pipeline migration complete:

- [ ] All StageName values in the source CSV match active stages in the target org's Sales Process
- [ ] Product2 records loaded and verified before Price Book Entries are inserted
- [ ] Standard Price Book Entry exists for every Product2 that has a custom Price Book Entry
- [ ] Every Opportunity has a valid `Pricebook2Id` set before OpportunityLineItems are loaded
- [ ] OpportunityLineItem `PricebookEntryId` references the same Price Book as the parent Opportunity
- [ ] OpportunityHistory insert was NOT attempted directly (use Task records or sequential updates instead)
- [ ] OpportunitySplits feature flag confirmed enabled before OpportunitySplit records are loaded
- [ ] SplitType configured and active before OpportunitySplit records are loaded
- [ ] OpportunityTeamMember records loaded before OpportunitySplit records
- [ ] Split percentages sum to 100% per opportunity per SplitType
- [ ] Post-migration validation: Opportunity Amount totals match source; OLI counts match source; team member coverage spot-checked

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **OpportunityHistory is not insertable** — Attempting to insert OpportunityHistory records via Bulk API 2.0 or SOAP API returns `INVALID_TYPE_FOR_OPERATION: entity type Opportunity History does not support create`. This is a hard platform constraint, not a permissions issue. Historical stage data must be preserved via Task records or sequential Opportunity updates.

2. **Opportunity Amount becomes read-only once line items exist** — When an Opportunity has at least one OpportunityLineItem, the `Amount` field becomes a roll-up of `TotalPrice` across all line items and cannot be set directly. If the source system's opportunity total does not match the sum of line item totals, the migration will produce an Amount discrepancy that cannot be corrected without deleting line items first.

3. **Pricebook2Id cannot be changed after line items are loaded** — Once an OpportunityLineItem exists on an Opportunity, the Opportunity's `Pricebook2Id` is locked and cannot be updated. If the wrong Price Book is assigned to an Opportunity, all its line items must be deleted, the Price Book updated, and the line items re-inserted. Always confirm `Pricebook2Id` before loading line items.

4. **Standard Price Book Entry is required before custom Price Book Entry** — A Product2 must have a PricebookEntry in the Standard Price Book before a PricebookEntry can be created for it in any custom Price Book. Attempting to insert a custom Price Book Entry without the corresponding Standard Price Book Entry fails with `FIELD_INTEGRITY_EXCEPTION`. This constraint applies even if the org never uses the Standard Price Book.

5. **StageName must exactly match an active Sales Process stage** — The `StageName` field on Opportunity is a picklist that is constrained by the Sales Process assigned to the Opportunity's Record Type. Loading a StageName value that is not in the assigned Sales Process (even if it exists as a picklist value elsewhere) causes an insert failure. Map and validate all source stage values against target org stages before any load begins.

6. **OpportunitySplit enabling is irreversible in production** — Once Opportunity Splits is enabled in Setup, it cannot be disabled. This also adds a required configuration burden: SplitType must be set up. Enable Splits in a sandbox first to verify the configuration before enabling in production.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `opportunity-pipeline-migration-template.md` | Fill-in-the-blank work template capturing load sequence, external ID mapping, Pricebook strategy, stage history approach, and post-migration validation plan |
| `check_opportunity_pipeline_migration.py` | stdlib Python checker that validates migration CSVs and metadata for common sequencing, Price Book, and split configuration issues |

---

## Related Skills

- `data-migration-planning` — use for multi-object migration architecture, tool selection, external ID strategy, validation rule bypass, and rollback planning; this skill focuses specifically on the Opportunity object family
- `data-import-and-management` — use for step-by-step Data Loader mechanics and field mapping operations
- `large-data-volumes` — use when Opportunity volume is in the tens of millions and query/index performance is the primary concern

---

## Official Sources Used

- OpportunityHistory Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunityhistory.htm
- OpportunityFieldHistory Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunityfieldhistory.htm
- Load Opportunity Products — https://help.salesforce.com/s/articleView?id=sf.products_opportunity_load.htm&type=5
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
