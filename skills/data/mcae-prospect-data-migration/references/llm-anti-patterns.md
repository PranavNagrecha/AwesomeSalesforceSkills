# LLM Anti-Patterns — MCAE Prospect Data Migration

Common mistakes AI coding assistants make when generating or advising on MCAE prospect data migration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming Engagement History Can Be Imported via CSV

**What the LLM generates:** Instructions to add columns like `Email Opens`, `Email Clicks`, `Last Activity Date`, or `Engagement Score` to the migration CSV and map them to MCAE prospect fields during import. The LLM presents this as a valid way to preserve engagement history from the source system.

**Why it happens:** LLMs generalize from CRM import patterns (Salesforce Data Loader, HubSpot import) where most field types can be imported. The LLM does not know that MCAE engagement history is stored as VisitorActivity records — not as prospect fields — and that there is no importable field type that corresponds to engagement events.

**Correct pattern:**

```
Engagement history (opens, clicks, form fills, page views, custom redirect clicks) is
generated natively by MCAE tracking infrastructure and cannot be imported via CSV,
the Pardot API, or any supported mechanism.

For a prospect migration:
- Exclude all engagement metric columns from the source CSV.
- Document the engagement history gap in the migration scope.
- Suppress score-gated automation rules during the post-migration warm-up period.
- Plan a re-engagement campaign to rebuild MCAE engagement signals.
```

**Detection hint:** Look for CSV column headers or MCAE custom field names containing words like "opens", "clicks", "activity", "history", "score" in the context of a migration plan. These indicate the anti-pattern.

---

## Anti-Pattern 2: Advising That Custom Fields Are Available in the Import UI Without Connector Prerequisites

**What the LLM generates:** Instructions to create a custom prospect field in MCAE Admin and then immediately use it in the import field mapping UI — without mentioning that the Salesforce Connector must also be configured with a bidirectional field mapping for that field.

**Why it happens:** LLMs often conflate "creating a field in the system" with "making the field available everywhere." They are not aware that MCAE custom prospect fields require a three-step setup chain (Salesforce field creation, MCAE field creation, Connector mapping) before they appear in the import UI.

**Correct pattern:**

```
To make a custom prospect field available in the MCAE import field mapping UI:

Step 1: Create the custom field on the Salesforce Lead and/or Contact object.
Step 2: In MCAE Admin > Configure Fields > Prospect Fields, add the custom field
        and link it to the Salesforce field from Step 1.
Step 3: In MCAE Admin > Connectors > Salesforce > Edit > Map Fields,
        confirm the field appears and set the sync direction to bidirectional.

Only after all three steps will the custom field appear in the import mapping UI.
If any step is incomplete, the CSV column is silently dropped during import.
```

**Detection hint:** Any migration instruction that says "create the custom field in MCAE and then map it in the import" without mentioning Salesforce Connector configuration is missing the prerequisite.

---

## Anti-Pattern 3: Suggesting the Pardot API v5 VisitorActivity Endpoint Can Create Engagement Records

**What the LLM generates:** Code or instructions that attempt to POST to the Pardot API v5 `/api/v5/visitorActivities` endpoint to create historical engagement records for imported prospects. The LLM presents this as a way to backfill engagement history programmatically.

**Why it happens:** LLMs recognize that a `/visitorActivities` endpoint exists in the Pardot API and incorrectly infer that it supports create operations. The endpoint is read-only. LLMs also generalize from other Salesforce APIs (e.g., Data Loader, Bulk API) where custom objects can be written to freely.

**Correct pattern:**

```python
# The Pardot API v5 VisitorActivity endpoint is READ-ONLY.
# There is no supported POST, PUT, or PATCH operation for visitor activities.

# Correct usage — query only:
# GET /api/v5/visitorActivities?fields=id,type,prospectId,createdAt

# Do NOT attempt:
# POST /api/v5/visitorActivities  ← not supported, will return 404 or 405
# PATCH /api/v5/visitorActivities/{id}  ← not supported

# There is no supported mechanism to create or backfill MCAE engagement
# history via any API, CSV import, or configuration option.
```

**Detection hint:** Any code or instruction containing `POST` to a visitor activity endpoint, or any statement that engagement data "can be imported via the API," is incorrect.

---

## Anti-Pattern 4: Treating MCAE Prospect Score as a Writable Field That Reflects Imported Values

**What the LLM generates:** Instructions to import a "score" column into MCAE and map it to the prospect score field, with the claim that imported prospects will then have non-zero scores that reflect their prior engagement.

**Why it happens:** MCAE exposes a `score` field on prospect records. LLMs assume that because the field is readable, it is also writable during import. They do not know that prospect score in MCAE is calculated and managed by the scoring engine — it is not a simple numeric field that can be set to an arbitrary value and used by automation rules.

**Correct pattern:**

```
MCAE prospect score is calculated by the MCAE scoring engine based on tracked
activity events (email opens, clicks, form submissions, page views). It is not a
writable field in the sense that an imported value will be used by automation rules.

Even if a "score" column is present in the import CSV and maps to a custom field,
the automation engine reads from the system-calculated score, not from a custom field.

For imported prospects: accept that scores start at zero. Design a post-migration
warm-up plan rather than attempting to set scores via import.
```

**Detection hint:** Instructions that include a "Score" column in the migration CSV or claim that imported prospects will have non-zero scores based on imported data.

---

## Anti-Pattern 5: Claiming a Self-Service CSV Import Is Equivalent to a Support-Assisted BU Migration

**What the LLM generates:** Instructions to export all prospects from the source MCAE Business Unit as a CSV and import them into the destination BU, presented as a complete BU migration strategy.

**Why it happens:** LLMs generalize from other Salesforce data migration patterns where a CSV export/import cycle is a valid migration approach. They are not aware that cross-BU prospect migrations have MCAE-specific requirements — engagement history cannot transfer via CSV, Salesforce Connector sync relationships must be re-established, and Salesforce Support has a dedicated BU migration process that handles more of the relationship data.

**Correct pattern:**

```
For cross-BU prospect migrations in MCAE:

1. Do NOT use a CSV export/import as the migration strategy.
   CSV import creates new prospect records in the destination BU but:
   - Drops all engagement history (VisitorActivity records)
   - Does not transfer prospect-to-CRM record sync relationships
   - Does not preserve list membership history

2. Open a Salesforce Support case requesting a BU migration.
   Support has a migration process that preserves more of the prospect data structure.

3. Communicate to stakeholders before any BU migration:
   - Engagement history will not transfer regardless of method
   - Post-migration warm-up and score suppression is required

Self-service CSV import is appropriate for importing prospects from external systems
(legacy CRM, ESP, spreadsheet). It is not appropriate for BU-to-BU migrations.
```

**Detection hint:** Any BU migration plan that relies solely on CSV export/import without mentioning Salesforce Support involvement or without acknowledging the engagement history loss.

---

## Anti-Pattern 6: Not Deduplicating the Source CSV Before Import

**What the LLM generates:** Import instructions that skip deduplication, or that assume MCAE will handle duplicate rows gracefully by creating separate records.

**Why it happens:** LLMs familiar with CRM tools that support multiple records for the same email address assume MCAE follows the same model. MCAE uses email address as the sole unique key, meaning duplicate rows in the CSV result in update conflicts, not separate records.

**Correct pattern:**

```
Before any MCAE prospect import:

1. Deduplicate the source CSV on the Email column.
   Keep one row per unique email address. Decide which row wins
   (e.g., most recent activity date from the source system).

2. Remove rows with blank Email values.
   MCAE rejects these rows silently; they indicate a data quality problem.

3. Cross-reference the source CSV against existing MCAE prospects
   if updates to existing records are not intended.

Deduplication is mandatory — it is not optional cleanup.
```

**Detection hint:** Any import plan that does not explicitly mention deduplication on the Email column before upload.
