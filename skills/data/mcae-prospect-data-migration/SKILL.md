---
name: mcae-prospect-data-migration
description: "Use when importing or migrating prospect records into MCAE (Marketing Cloud Account Engagement / Pardot) via the CSV list import tool, including field mapping for default and custom fields and handling of cross-BU prospect moves. NOT for CRM (Lead/Contact) data migration, not for backfilling engagement history such as opens, clicks, form fills, or page view data, and not for bulk API prospect creation via Apex."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "I need to import a list of prospects into MCAE from a CSV file exported from our old CRM"
  - "How do I migrate prospect records from one MCAE business unit to another without losing data?"
  - "My custom prospect fields are not mapping correctly during the MCAE list import"
  - "Can I import historical email opens and click data when migrating to MCAE?"
  - "What fields does MCAE support during CSV prospect import and how do I map them?"
tags:
  - mcae
  - pardot
  - prospect-import
  - data-migration
  - csv-import
  - custom-field-sync
  - list-import
  - engagement-history
inputs:
  - "Source CSV file with prospect records (must include Email column as the unique key)"
  - "List of custom prospect fields already configured in MCAE and mapped via Salesforce Connector"
  - "Target MCAE Business Unit identifier and active Salesforce Connector status"
  - "Confirmation that custom fields are bidirectionally mapped in Salesforce Connector before import"
outputs:
  - "Imported prospect records in the target MCAE Business Unit with default and custom fields populated"
  - "Field mapping decisions documented for each source column"
  - "Clear scope statement confirming that engagement history was not imported and must be rebuilt natively"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# MCAE Prospect Data Migration

Use this skill when importing prospect records into Marketing Cloud Account Engagement (MCAE, formerly Pardot) from a CSV source — whether from a legacy CRM, a marketing tool, or another MCAE Business Unit. This skill covers the list import mechanism, default and custom field mapping, connector prerequisites, and the hard limits on what data can and cannot be carried over.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the target MCAE Business Unit has an active Salesforce Connector. Custom field import requires the connector to be configured and the fields to be bidirectionally mapped before the import runs — importing custom field values into unmapped fields silently drops the data.
- The email address is the sole matching key for MCAE prospect records. Duplicate emails in the source CSV will cause MCAE to merge or conflict records. Deduplicate the source CSV on email before proceeding.
- Engagement history — email opens, link clicks, form submissions, page views, and file downloads — is generated natively by MCAE tracking infrastructure. It is NOT importable via CSV. There is no supported mechanism for backfilling historical engagement data into MCAE, even via the API. Set clear expectations with stakeholders before beginning any migration project.
- MCAE limits: the list import CSV can hold up to 100,000 records per file. Larger datasets must be split into multiple files and imported sequentially.

---

## Core Concepts

### 1. CSV List Import as the Import Mechanism

MCAE provides a list-based CSV import UI (Prospects > Import Prospects, or via the Lists module) as the primary mechanism for bulk prospect creation and update. There is no supported SFTP or bulk API import path that bypasses field mapping. The CSV must include an `Email` column. MCAE matches incoming rows to existing prospects by email address; rows with a new email create a new prospect, rows with an existing email update that record (subject to sync rules).

Default MCAE fields are available in the field mapping screen without any prerequisite setup. The mapping screen allows each CSV column to be assigned to one default or custom prospect field, or to be ignored. Unmapped columns are silently dropped — they do not cause import failures.

### 2. Custom Field Sync Requires Salesforce Connector Configuration First

Custom prospect fields in MCAE are backed by custom fields on the Salesforce Lead and/or Contact objects. Before a custom field appears in the MCAE import field mapping screen, the following must be true:

1. The custom field must exist on the Salesforce Lead or Contact object (or both).
2. The field must be created in MCAE (Admin > Configure Fields > Prospect Fields).
3. The field must be mapped bidirectionally in the Salesforce Connector configuration (Admin > Connectors > Salesforce > Map Fields).

If any of these steps are incomplete, the custom field does not appear in the import field mapping UI and any CSV data for that field is dropped. This is the most common silent data loss failure in MCAE prospect imports.

### 3. Engagement History Is Natively Generated — It Cannot Be Imported

MCAE engagement history (email opens, link clicks, form submissions, landing page views, file downloads, and custom redirect clicks) is recorded by MCAE's tracking infrastructure when a prospect interacts with a tracked asset. This data is attached to a visitor activity record and cannot be fabricated or imported via CSV, API, or any supported mechanism.

This means:
- Migrating from a legacy ESP that tracked opens and clicks produces MCAE prospect records with zero historical engagement. Scores built on engagement history start at zero.
- Historical engagement data from the source system cannot be used to pre-seed MCAE scores or grades.
- Prospect scores must be rebuilt from scratch through live MCAE activity after import.

This is a hard architectural boundary — not a limitation that can be worked around with custom development within MCAE.

### 4. Cross-BU Migrations Require Salesforce Support

Moving prospect records from one MCAE Business Unit to another — for example, when an organization consolidates two BUs or migrates a regional BU into a parent BU — requires a case with Salesforce Support. There is no self-service mechanism. Engagement history does not carry over across BUs even when Support performs the migration. The destination BU receives prospect records with field values intact but a blank engagement history.

---

## Common Patterns

### Pattern 1: Importing Prospects From a Legacy CRM via CSV

**When to use:** When a prospect list is being migrated from a legacy CRM (HubSpot, Eloqua, Marketo, spreadsheet) into MCAE for the first time, with a mix of default and custom fields.

**How it works:**
1. Export the source system records to CSV. Ensure the column headers are clean and match the intended MCAE field names where possible.
2. Deduplicate on the Email column. Remove rows with blank email. MCAE rejects rows with no email.
3. Confirm the Salesforce Connector is active and all custom fields are mapped bidirectionally (see Core Concept 2).
4. In MCAE: Prospects > Import > Import Prospects. Upload the CSV.
5. On the field mapping screen, assign each column to the appropriate MCAE default or custom field. Mark any column as "Do not import" if no matching field exists.
6. Set the list assignment for the import (existing list or create a new one). This is how the imported prospects are tagged for downstream campaigns.
7. Submit. Monitor the import status; MCAE sends an email notification when complete with a success/error count.
8. Spot-check imported records in MCAE Prospects view. Verify custom field values were populated.

**Why not the alternative:** Attempting to use the Pardot API to create prospects programmatically bypasses the list-import field mapping UI but requires each field to be set explicitly in the API payload — and still cannot import engagement history. The list import UI is the correct path for bulk CSV-sourced migration.

### Pattern 2: Documenting Engagement History Loss and Setting Stakeholder Expectations

**When to use:** Any time a migration project involves prospect records that carry engagement history in the source system (open rates, click rates, lead scores based on activity).

**How it works:**
1. Identify which fields in the source system are derived from engagement activity (open count, last clicked date, score, grade, activity-based segments).
2. Document in the migration plan that these values cannot be imported into MCAE.
3. Define the cut-over date. All engagement tracking restarts from zero in MCAE on that date.
4. Advise stakeholders to suppress any MCAE score-gated automations for a defined warm-up period after migration, because imported prospects will have score = 0 regardless of their historical engagement level.
5. Plan for score rebuilding: run a re-engagement campaign against the imported list shortly after migration to generate initial MCAE engagement signals.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Importing prospects with only default fields (email, first name, last name, company) | CSV list import, no connector prerequisite needed | Default fields are always available in the mapping UI |
| Importing prospects with custom field values | Verify Salesforce Connector active + bidirectional field mapping before import; then CSV list import | Custom fields are invisible in the mapping UI until connector prerequisites are met |
| Stakeholder wants historical open/click data imported | Clearly document this is not possible; plan re-engagement campaign post-import | Engagement history is natively generated; no import path exists |
| Moving prospects from one MCAE BU to another | Open Salesforce Support case; do not attempt self-service CSV workaround | No self-service mechanism; support-assisted migration preserves field values but not engagement history |
| Source CSV has more than 100,000 rows | Split into multiple files of ≤100,000 rows each; import sequentially | MCAE list import file size limit |
| Duplicate emails in source CSV | Deduplicate before import; choose a merge/update strategy | MCAE uses email as the sole unique key; duplicates cause unexpected record merges or update conflicts |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm prerequisites** — Verify the Salesforce Connector is active in the target MCAE Business Unit. Confirm all custom fields required in the migration are created in MCAE, exist on the Salesforce Lead/Contact object, and are bidirectionally mapped in the Connector field mapping configuration. Do not proceed until this is verified.
2. **Prepare and validate the source CSV** — Ensure the CSV includes an `Email` column with no blanks. Deduplicate on email. Remove columns for engagement metrics (open count, click count, last activity date) that cannot be imported and document them as out of scope. Split the file into chunks of ≤100,000 rows if needed.
3. **Scope the engagement history gap with stakeholders** — Formally document that historical opens, clicks, form submissions, page views, and derived scores cannot be migrated. Agree on a post-migration re-engagement plan and confirm score-gated automations will be temporarily suppressed after cut-over.
4. **Run the import** — Navigate to Prospects > Import > Import Prospects in MCAE. Upload the CSV, map each column to the appropriate field (default or custom), assign the prospects to a target list, and submit. Do not navigate away during processing.
5. **Verify the import results** — Review the import completion email for success and error counts. Spot-check 5–10 imported records in the MCAE Prospects view and confirm custom field values are populated correctly. If custom field values are blank, check connector field mapping and re-import a corrected test row.
6. **Document scope and cut-over** — Record the cut-over date, the fields imported, the fields excluded (engagement metrics), and the list(s) assigned. Hand this documentation to the campaign team as the baseline for post-migration engagement tracking.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Salesforce Connector is active and all required custom fields are bidirectionally mapped
- [ ] Source CSV is deduplicated on Email and contains no blank Email rows
- [ ] Source CSV contains no more than 100,000 rows per file
- [ ] Engagement history fields (opens, clicks, scores derived from activity) are excluded from the CSV and documented as out of scope
- [ ] All CSV columns are mapped or explicitly marked "Do not import" in the mapping UI
- [ ] Post-import spot-check confirms custom field values are present on imported records
- [ ] Stakeholders have been informed of the engagement history limitation and a re-engagement plan exists

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Custom field values silently dropped when connector mapping is missing** — If a custom field is not yet mapped in the Salesforce Connector, the field does not appear in the import mapping UI. MCAE does not warn the user. The CSV column is simply treated as unmapped and ignored, resulting in blank custom field values on every imported record with no error in the import log.
2. **Engagement history is permanently unimportable — no API workaround exists** — Practitioners sometimes attempt to use the Pardot API v5 VisitorActivity endpoint to create activity records for imported prospects. This endpoint is read-only. There is no supported write path for visitor activity or engagement history data in MCAE, at any access tier.
3. **Account merges and BU moves don't carry engagement history** — When Salesforce Support migrates prospects between Business Units, the field values on prospect records are transferred but the engagement history (VisitorActivity records) remains in the source BU and is not accessible in the destination BU. Marketing teams often discover this after migration when re-engagement segments return zero results.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Imported prospect list | Prospects visible in the MCAE Prospects view assigned to the designated import list, with default and custom field values populated |
| Migration scope document | Written record of which fields were imported, which were excluded (engagement metrics), the cut-over date, and the post-migration re-engagement plan |
| Field mapping log | CSV column to MCAE field mapping decisions recorded for repeatability and troubleshooting |

---

## Related Skills

- `admin/mcae-pardot-setup` — covers Salesforce Connector setup, field-level sync rules, and prospect sync configuration that must be in place before a custom field import can succeed
- `apex/mcae-pardot-api` — covers Pardot API v5 for programmatic prospect creation and querying; relevant if post-import automation or validation via API is needed
