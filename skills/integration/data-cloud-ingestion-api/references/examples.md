# Examples — Data Cloud Ingestion API

## Example 1: Schema Registration Fails — Missing DateTime Field on Engagement Object

**Scenario:** A developer uploaded an OpenAPI YAML schema for a web event object categorized as Engagement type. Schema registration failed with a validation error.

**Problem:** Engagement-category objects require a field with `type: string, format: date-time`. The schema was missing this field.

**Solution:**
Add the required DateTime field before re-uploading:
```yaml
properties:
  eventTimestamp:
    type: string
    format: date-time
```
Re-register the schema after adding the field.

**Why this works:** Data Cloud uses the DateTime field for event sequencing in the Engagement data model. It is mandatory for Engagement-category schemas.

---

## Example 2: Bulk Ingestion Deletes Historical Records — Full-Replace Semantics

**Scenario:** A data team ran nightly bulk jobs with delta files (only new/changed records since the previous day). After three months, historical purchase history in Data Cloud showed only the current month's records.

**Problem:** Bulk ingestion replaces the entire dataset for that object with the uploaded files. Uploading only delta records deleted all prior history from Data Cloud.

**Solution:**
1. Switch to full snapshot exports for bulk ingestion — each job must include the complete current dataset
2. For incremental-only updates, use streaming ingestion with upsert semantics instead of bulk

**Why this works:** Bulk is designed for full snapshots. Streaming supports upsert semantics for incremental updates.

---

## Example 3: Schema Field Removal Not Supported After Deployment

**Scenario:** After six months in production, an architect wanted to remove an unused field from the Ingestion API schema.

**Problem:** Field removal is not supported after schema deployment. The Ingestion API schema is additive-only — no field removal, renaming, or data type changes after initial deployment.

**Solution:**
1. Leave the unused field in the schema (it causes no functional harm)
2. Document it as deprecated in the YAML comments
3. Prevent future occurrences through pre-deployment schema review with all stakeholders

**Why this works:** The schema contract is fixed at deployment. Pre-deployment review is the only prevention for unwanted fields.
