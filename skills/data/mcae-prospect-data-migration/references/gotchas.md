# Gotchas — MCAE Prospect Data Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Engagement History Is Not Importable via CSV, API, or Any Supported Mechanism

**What happens:** When practitioners import prospects into MCAE from a legacy marketing platform, the imported records have zero engagement history in MCAE — no opens, no clicks, no form submissions, no page views. MCAE prospect scores start at zero for every imported record regardless of how engaged that contact was in the source system. This catches teams off guard because they assume importing a record also imports the associated activity.

**When it occurs:** Every time prospects are imported from an external source into MCAE for the first time. It also applies to BU-to-BU migrations performed by Salesforce Support — engagement history from the source BU does not carry to the destination BU.

**How to avoid:** Explicitly scope engagement history as out of migration before the project starts. Remove engagement metric columns from the source CSV. Suppress score-gated automation rules during a post-migration warm-up window (typically 30–90 days). Plan a re-engagement campaign to generate initial MCAE signals for imported prospects. Document the engagement history boundary in the migration sign-off so stakeholders cannot retroactively claim this was not communicated.

---

## Gotcha 2: Custom Field Values Are Silently Dropped When Connector Mapping Is Incomplete

**What happens:** If a custom field is not yet created in MCAE or not yet mapped in the Salesforce Connector field mapping configuration, that field does not appear in the import mapping UI. The CSV column cannot be assigned to a field. MCAE treats the column as "Do not import" with no warning, no error, and no import log entry indicating data was lost. The import completes successfully with the correct record count, but every imported record has a blank value for that custom field.

**When it occurs:** Any import that includes custom field columns when the Salesforce Connector field mapping is not fully configured. This is the most common source of silent data loss in MCAE prospect imports. Teams often discover it only after spotting unexpected blank fields on imported records.

**How to avoid:** Before running any import involving custom fields, verify the full setup chain: (1) custom field exists on the Salesforce Lead or Contact object, (2) custom field is created in MCAE Admin > Configure Fields > Prospect Fields, (3) custom field is bidirectionally mapped in Admin > Connectors > Salesforce > Map Fields. Run a small test import of 5–10 records before the full migration and verify custom field values in the MCAE Prospects view.

---

## Gotcha 3: Cross-BU Prospect Migrations Require Salesforce Support and Do Not Carry Engagement History

**What happens:** Organizations with multiple MCAE Business Units sometimes attempt to self-service a BU-to-BU migration by exporting prospects from the source BU as a CSV and importing them into the destination BU. This produces prospect records in the destination BU with profile field values intact, but the engagement history from the source BU — all the VisitorActivity records, tracked emails, form submissions, and page views — remains in the source BU and is inaccessible from the destination BU.

Additionally, if the source BU had prospect-to-Account or prospect-to-Opportunity associations managed through the Salesforce sync, those associations must be re-verified after the migration because the destination BU's Salesforce Connector will create new sync relationships for the imported prospects.

**When it occurs:** Any cross-BU consolidation, regional BU merger, or parent/child BU restructuring. Also occurs when an account is transferred between Salesforce orgs that each have their own MCAE BU.

**How to avoid:** Open a Salesforce Support case for any BU-to-BU migration rather than attempting a self-service CSV approach. Clearly communicate to stakeholders before the migration that engagement history will not transfer. Plan the same post-migration warm-up strategy (score suppression, re-engagement campaign) as for any external prospect import.

---

## Gotcha 4: Email Address Is the Sole Deduplication Key — Duplicate Emails Cause Unexpected Merges

**What happens:** MCAE uses the prospect email address as its sole unique identifier. When a CSV import includes two rows with the same email address, MCAE processes them as updates to the same prospect record. The second row overwrites values written by the first row for any mapped fields. The result depends on row order in the CSV, which is unpredictable if the source CSV was sorted or deduplicated incorrectly. Teams sometimes discover that duplicate rows caused field value overwriting only after noticing inconsistencies in imported records.

Additionally, if the import CSV contains an email address that already exists in MCAE (from a previous import or from a CRM-synced record), MCAE updates the existing prospect rather than creating a new one. This can inadvertently overwrite field values on active prospect records if the CSV contains stale data from the source system.

**When it occurs:** Any import from a source system that was not deduplicated on email before export, or any import that includes email addresses already present in the destination MCAE BU.

**How to avoid:** Deduplicate the source CSV on the Email column before upload. Remove rows with blank email — MCAE rejects these, but they also indicate a data quality problem in the source. If updating existing prospects is not the intent, cross-reference the source CSV against the current MCAE prospect list before importing and remove overlapping records.

---

## Gotcha 5: The 100,000-Row Limit Per CSV File Is Not Surfaced as an Error — It Silently Truncates

**What happens:** MCAE's list import accepts CSV files up to 100,000 rows. If a CSV exceeds this limit, MCAE does not reject the file or report an import error. Instead, it processes only the first 100,000 rows and stops. The import completion notification reports success with 100,000 records imported and does not indicate that additional rows were dropped. This is easy to miss when importing large datasets.

**When it occurs:** Any import where the source CSV contains more than 100,000 prospect records.

**How to avoid:** Always check the record count in the source CSV before importing. If the count exceeds 100,000, split the file into multiple files and import them sequentially. Name the files clearly (e.g., `prospects_import_part1_of_3.csv`) to track progress. Verify the total imported count against the expected count after all parts complete.
