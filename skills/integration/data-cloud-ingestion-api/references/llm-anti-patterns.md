# LLM Anti-Patterns — Data Cloud Ingestion API

Common mistakes AI coding assistants make when generating or advising on Salesforce Data Cloud Ingestion API implementations.

---

## Anti-Pattern 1: Treating Bulk Ingestion as Incremental/Upsert

**What the LLM generates:** Bulk ingestion code that sends only new or changed records (delta) as a nightly job to update Data Cloud.

**Why it happens:** LLMs associate "bulk data job" with incremental upsert patterns from standard Bulk API experience.

**Correct pattern:** Data Cloud Bulk Ingestion uses full-replace semantics — each job replaces the entire dataset for the object. For incremental updates, use streaming ingestion with upsert semantics.

**Detection hint:** If bulk ingestion code sends only delta records (not a complete snapshot), it will silently delete all records not included in the file.

---

## Anti-Pattern 2: Assuming 202 Streaming Response Means Data Is Available Immediately

**What the LLM generates:** Code that calls the streaming ingestion endpoint and then immediately queries Data Cloud Query API for the newly ingested records.

**Why it happens:** LLMs model 202 Accepted as synchronous completion confirmation.

**Correct pattern:** Streaming ingestion is asynchronous. Data is processed in micro-batches approximately every 3 minutes. Queries immediately after a 202 response will not return the newly ingested data. Implement a delay or retry logic for post-ingestion validation.

**Detection hint:** If code queries Data Cloud immediately after a streaming API call without a delay, the validation will read stale data.

---

## Anti-Pattern 3: Designing Schema with Field Removal in the Change Plan

**What the LLM generates:** A schema versioning plan that includes field removals or data type changes in future versions.

**Why it happens:** LLMs apply standard API versioning patterns (add/remove/change fields across versions) without modeling the Ingestion API's additive-only constraint.

**Correct pattern:** Ingestion API schemas are additive-only after deployment. Field removal, type changes, and object deletion are not supported. Change plans must be additive only. Any field that might need removal should be omitted from the initial schema.

**Detection hint:** If a schema migration plan includes field removal or type change steps, it will fail at implementation time.

---

## Anti-Pattern 4: Using Generic `api` Scope Instead of `cdp_ingest_api`

**What the LLM generates:** Connected App configuration with only the standard `api` OAuth scope for Ingestion API authentication.

**Why it happens:** LLMs default to the standard Salesforce API OAuth scope which works for most Salesforce API integrations.

**Correct pattern:** The `cdp_ingest_api` scope must be explicitly added to the Connected App. Tokens obtained with only the `api` scope receive 401 Unauthorized responses on Ingestion API endpoints.

**Detection hint:** If the Connected App configuration does not include `cdp_ingest_api` in its OAuth scopes, Ingestion API calls will fail with 401.

---

## Anti-Pattern 5: Omitting DateTime Field from Engagement-Category Objects

**What the LLM generates:** An OpenAPI YAML schema for an Engagement-type object (web events, email clicks, purchases) without a date-time formatted field.

**Why it happens:** LLMs generate OpenAPI schemas based on field data types provided without knowing the Data Cloud-specific business rule requiring DateTime on Engagement objects.

**Correct pattern:** Any object with Engagement category classification in the Ingestion API schema must include at least one field with `type: string, format: date-time`. Omitting it causes schema registration to fail with a validation error.

**Detection hint:** If an OpenAPI schema for an Engagement-type object has no field with `format: date-time`, schema registration will fail.
