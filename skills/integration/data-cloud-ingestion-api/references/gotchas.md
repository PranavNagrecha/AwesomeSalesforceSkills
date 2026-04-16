# Gotchas — Data Cloud Ingestion API

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Schema Changes Are Largely Irreversible After Deployment

Once an Ingestion API schema is registered and data has been ingested using it, you cannot remove fields, change field data types, rename fields, or delete object definitions. Only additive changes (adding new fields) are supported. This is a fundamental constraint of the Ingestion API schema model, not a temporary limitation.

**Fix:** Treat initial schema design as a critical architecture decision. Review the schema with all stakeholders and data source owners before registration. Include all fields that may ever be needed, even if not immediately populated.

---

## Gotcha 2: Bulk Ingestion Replaces the Entire Dataset

A bulk ingestion job does not append or update individual records — it replaces the complete dataset for the specified object with the contents of the uploaded files. If you upload a partial file (e.g., delta records only), the prior complete dataset is deleted and replaced with only the partial records. This produces silent data loss with no warning.

**Fix:** For bulk ingestion, always upload the complete current snapshot of the dataset per job. For incremental updates, use streaming ingestion with upsert semantics.

---

## Gotcha 3: Streaming Is Asynchronous — 202 Does Not Mean Data Is Available

The streaming endpoint returns HTTP 202 Accepted immediately, but data is not processed synchronously. Processing occurs asynchronously in micro-batches approximately every 3 minutes. Any process that queries Data Cloud immediately after a streaming API call will not see the newly ingested data — it is still queued for processing.

**Fix:** Use the validate endpoint (`/streaming/{objectName}/validate`) for synchronous payload format confirmation during development. For production, implement a monitoring pattern that queries Data Cloud Query API at least 5 minutes after ingestion to confirm data landed.

---

## Gotcha 4: Engagement-Category Objects Require a DateTime Field

OpenAPI schemas for objects with an Engagement category classification must include at least one field with `type: string, format: date-time`. Schema registration fails without this field. This is not obvious from the schema format specification alone — it is a Data Cloud business rule applied during schema validation.

**Fix:** Always include a DateTime field (e.g., `eventTimestamp`, `activityDate`) in Engagement-category object schemas before attempting registration.

---

## Gotcha 5: Connected App Scope Must Be `cdp_ingest_api`, Not Generic `api`

The generic Salesforce API OAuth scope (`api` — "Manage user data via APIs") is NOT sufficient for Ingestion API calls. The `cdp_ingest_api` scope must be explicitly added to the Connected App. OAuth tokens obtained with only the generic `api` scope will receive 401 Unauthorized responses on Ingestion API endpoints.

**Fix:** When creating the Connected App for Ingestion API, explicitly add the `cdp_ingest_api` (Data Cloud Ingest API) scope alongside `api`. Test the token by calling the `/services/data/v{version}/ssot/ingest/connectors` endpoint before attempting data ingestion.
