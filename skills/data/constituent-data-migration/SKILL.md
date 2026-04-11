---
name: constituent-data-migration
description: "Use this skill when migrating constituent records (Contacts, Household Accounts, relationships, addresses, donations) into an NPSP org using the NPSP Data Importer. Triggers: importing contacts into NPSP, migrating nonprofit constituents, loading household data, bulk contact upload NPSP, constituent ETL. NOT for standard contact import, Nonprofit Cloud (NPC) migration, or generic Data Loader bulk loads."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "importing contacts into NPSP org and households are not being created correctly"
  - "migrating nonprofit constituent records from Excel or legacy CRM into Salesforce with household grouping"
  - "bulk uploading donors into NPSP and rollup fields are not populating after import"
tags:
  - npsp
  - constituent-data-migration
  - data-import
  - households
  - contact-matching
inputs:
  - "Source constituent data file (CSV or Excel) with Contact1, Contact2, household, address, and donation columns"
  - "NPSP org with Nonprofit Success Pack installed and Data Importer configured"
  - "Contact Matching Rules configuration (duplicate detection settings in NPSP Settings)"
  - "List of existing Account/Contact records to check for duplicates prior to import"
outputs:
  - "Populated npsp__DataImport__c staging records ready for NPSP processing"
  - "Validated household Account records with correct rollups and relationships"
  - "Migration run report showing imported, skipped, and failed rows"
  - "Duplicate detection report based on configured Contact Matching Rules"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Constituent Data Migration

Use this skill when loading constituent records — Contacts, Household Accounts, relationships, home addresses, and donations — into a Salesforce org running NPSP (Nonprofit Success Pack). This skill governs the correct tool selection, staging object design, and matching-rule configuration required to import constituent data without corrupting NPSP's Household Account model or triggering rollup failures.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm NPSP is installed and the org uses the Household Account model (not Person Accounts). NPSP and Person Accounts are incompatible.
- Identify which version of NPSP is active. The Data Importer UI and field API names differ slightly across releases. Use `npsp__DataImport__c` as the staging object in all versions.
- Clarify whether the source data includes household groupings or only individual contacts. Household grouping logic must be resolved in the staging file before import — NPSP uses Contact1/Contact2 column pairs on a single `npsp__DataImport__c` row to place two contacts in the same household.
- The most common wrong assumption: that standard Data Loader or the Salesforce Data Import Wizard can be used to import Contacts into NPSP. Both tools bypass NPSP Apex triggers entirely, leaving Household Account rollups stale and creating orphaned one-contact households.
- Key platform constraint: NPSP Data Importer processes `npsp__DataImport__c` records in batches via the `BDI_DataImport` Apex batch class. Batch sizes and timeouts apply. Very large loads (100k+ rows) should be chunked.

---

## Core Concepts

### The npsp__DataImport__c Staging Object

The `npsp__DataImport__c` object is the canonical entry point for all constituent data loading in NPSP. It is not a final destination — it is a staging area. Each row on this object can represent:

- **Contact1** — the primary contact in a household (required fields: `npsp__Contact1_Firstname__c`, `npsp__Contact1_Lastname__c`)
- **Contact2** — a second contact sharing the same household (optional; placed on the same row as Contact1)
- **Household Account** — auto-created or matched to an existing Account with Record Type = Household
- **Home Address** — a single address mapped to both contacts in the row
- **Org Account** — a separate non-household Account (employer) linked to Contact1 or Contact2
- **Donation** — an Opportunity linked to the household, created during the same import run

Populating a single `npsp__DataImport__c` row correctly avoids the need for multiple linked imports and ensures NPSP's processing logic handles relationship creation atomically.

### Contact Matching Rules and Duplicate Detection

Before inserting or updating Contacts, NPSP applies configurable Contact Matching Rules. These rules are set under **NPSP Settings > Data Import > Contact Matching**. The default rule matches on first name + last name + email. When a match is found, NPSP updates the existing Contact rather than creating a duplicate.

Matching rules must be reviewed and tuned before a migration run. If the rule is too loose, legitimate new contacts will be merged into wrong existing records. If too strict, duplicates will proliferate. Always run a pilot batch of 50–100 rows and inspect the results before full migration.

### Why Standard Import Tools Bypass NPSP Logic

Salesforce's standard Data Import Wizard and Data Loader insert Contact records directly into the `Contact` sObject via the standard API. This path does not invoke NPSP's `TDTM` (Table-Driven Trigger Management) Apex triggers. The consequences are:

1. **Stale rollups** — Household Account fields such as total giving, last gift date, and number of gifts are calculated by NPSP Apex triggers. Bypassing triggers leaves these fields blank or incorrect.
2. **Orphaned households** — NPSP expects one Household Account per contact group. Direct Contact inserts cause NPSP's after-insert trigger to fire and create a new one-contact household for every imported Contact, fragmenting existing household groupings.
3. **Missing relationships** — Household member relationships (npe4__Relationship__c) are not created for directly inserted Contacts.

These issues are extremely difficult to remediate post-import and often require a full data reload. Avoid direct Contact insertion entirely.

### NPSP-Aware APIs

If the NPSP Data Importer UI is not appropriate (e.g., you are driving an automated ETL pipeline), the correct alternative is to insert records directly into `npsp__DataImport__c` via Data Loader or the Bulk API, then invoke the NPSP Data Importer Apex batch class programmatically. This preserves NPSP trigger behavior because the import processing goes through the same `BDI_DataImport` code path.

---

## Common Patterns

### Pattern 1: Bulk Constituent Load from Excel via NPSP Data Importer

**When to use:** A nonprofit is migrating constituents from a legacy CRM or spreadsheet. Source data includes household pairs, home addresses, and historical donations.

**How it works:**
1. Map source columns to `npsp__DataImport__c` field API names. Use the Salesforce Data Import Field Mapping reference in NPSP Settings to confirm the correct field names.
2. For contacts in the same household, place both on a single row using Contact1 and Contact2 column pairs. Do not create two separate rows.
3. Map the home address to the Address fields on the staging record. NPSP will create an `npsp__Address__c` record and link it to both contacts in the household.
4. If historical donations should be imported in the same run, populate the Donation fields on the staging row. NPSP will create an Opportunity linked to the Household Account.
5. Upload the CSV to `npsp__DataImport__c` using Data Loader (to the staging object only, not to Contact directly).
6. Open the NPSP Data Importer UI (**App Launcher > NPSP Data Import**) and run the import job.
7. Review the import results screen. Rows in error status show the failure reason. Fix and re-import error rows.

**Why not the alternative:** Loading to `Contact` directly creates orphaned households and stale rollups that are very expensive to repair.

### Pattern 2: Programmatic ETL via BDI_DataImport Batch Class

**When to use:** A scheduled nightly sync needs to insert new donors from a donation platform into NPSP without manual UI steps.

**How it works:**
1. Write an Apex class or external ETL job that upserts rows into `npsp__DataImport__c` using external ID fields for deduplication.
2. After rows are staged, invoke the NPSP batch from Apex: `Database.executeBatch(new BDI_DataImport(false, batchSize), batchSize);`
3. Monitor batch job status in Apex Jobs. Check `npsp__DataImport__c.npsp__Status__c` field for each row's outcome after the batch completes.
4. Archive or delete processed rows from `npsp__DataImport__c` after successful import to keep the staging table clean.

**Why not the alternative:** Inserting directly into `Contact` bypasses all NPSP trigger management and produces data integrity failures at scale.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One-time bulk load from CSV or Excel | NPSP Data Importer UI + staging CSV to npsp__DataImport__c | Preserves trigger logic, provides import result report |
| Scheduled automated ETL pipeline | Upsert to npsp__DataImport__c, then invoke BDI_DataImport batch | Programmatic but still routes through NPSP processing |
| Small correction (5–10 records) | NPSP Data Importer UI with manual staging | Same tool, lower volume — do not use inline edit or Data Loader on Contact |
| Migrating from another NPSP org | Export to npsp__DataImport__c-compatible CSV, import via Data Importer | Maintains household and relationship integrity |
| Importing only donations (no new contacts) | NPSP Data Importer with Donation-only columns | Contact Matching Rules will match existing contacts; no new Contact rows created |
| Using Data Loader to directly insert Contacts | Do not do this | Bypasses NPSP triggers; corrupts household model |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm toolchain and NPSP configuration** — Verify NPSP is installed, identify the NPSP version, confirm the Household Account model is active, and review Contact Matching Rules in NPSP Settings before touching any data.
2. **Prepare and map the staging CSV** — Map source columns to `npsp__DataImport__c` field API names. Place Contact1 and Contact2 pairs on a single row for household members. Ensure address and donation fields are correctly mapped. Validate required fields are populated.
3. **Run a pilot batch** — Load a representative sample of 50–100 rows into `npsp__DataImport__c` and process through the NPSP Data Importer. Review results for duplicate matches, address creation, rollup values, and error rows before scaling up.
4. **Execute full migration in chunks** — Load the full dataset in chunks appropriate to org limits. Monitor the NPSP Data Importer results screen and `npsp__DataImport__c.npsp__Status__c` values. Document error rows and remediation steps.
5. **Validate post-import data quality** — After import, verify Household Account rollup fields (total giving, last gift date), confirm Address records were created, and spot-check a sample of Contact records for correct household assignment and relationship creation.
6. **Clean up staging records** — Archive or delete processed `npsp__DataImport__c` rows. Stale staging records with `npsp__Status__c = Imported` consume storage and can cause confusion in future import runs.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All Contact rows were loaded via `npsp__DataImport__c`, not directly to `Contact` via Data Loader or standard import
- [ ] Household pairs are on a single staging row using Contact1/Contact2 columns, not separate rows
- [ ] Contact Matching Rules were reviewed and tuned before the first import run
- [ ] Post-import: Household Account rollup fields (total giving, last gift date) are populated correctly
- [ ] Post-import: `npsp__Address__c` records were created and linked to both contacts in each household
- [ ] Post-import: No unexpected duplicate Contacts or orphaned one-contact households were created
- [ ] Processed `npsp__DataImport__c` staging rows have been archived or deleted

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Data Loader on Contact bypasses NPSP triggers** — Inserting or upserting Contact records via Data Loader or the standard Data Import Wizard invokes only standard Salesforce triggers. NPSP's `TDTM` trigger framework does not fire. The result is stale Household Account rollup fields, missing npe4__Relationship__c records, and orphaned single-contact households for every inserted Contact. This issue requires a full re-import to remediate.
2. **Contact2 fields are silently ignored if Contact1 is not populated** — If `npsp__Contact1_Firstname__c` or `npsp__Contact1_Lastname__c` is blank on a staging row, NPSP will skip the entire row, including any Contact2 data. Both contacts in a household pair must be on the same row and Contact1 fields must be populated first.
3. **Household Account naming is auto-generated and not directly settable** — NPSP auto-formats Household Account names (e.g., "Smith Household") based on the Household Naming Settings. If the source data includes an Account name that must be preserved, you cannot force it through the standard import path without customizing the Household Naming Format in NPSP Settings first.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Populated npsp__DataImport__c staging records | Rows in the staging object, ready to be processed by the NPSP Data Importer batch job |
| NPSP import results report | System-generated report showing imported, skipped, and failed rows; available in the Data Importer UI post-run |
| Post-import data quality spot-check results | Practitioner-validated sample of Contact, Account, Address, and Opportunity records confirming correct household assignment and rollup values |

---

## Related Skills

- `data/data-migration-planning` — Use before this skill to size the migration, define the extract format, and plan rollback strategy
- `data/large-scale-deduplication` — Use after this skill if post-import duplicate Contact or Account records need remediation
- `data/lead-data-import-and-dedup` — Related import skill for lead-model orgs (non-NPSP)
- `architect/npsp-vs-nonprofit-cloud-decision` — Use to decide whether to stay on NPSP or migrate to Nonprofit Cloud before beginning constituent migration work
