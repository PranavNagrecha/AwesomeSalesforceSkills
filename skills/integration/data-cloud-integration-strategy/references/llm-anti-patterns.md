# LLM Anti-Patterns — Data Cloud Integration Strategy

## Anti-Pattern 1: Describing Streaming Ingestion as Real-Time

**What the LLM generates:** "Data Cloud Streaming Ingestion API sends data in real-time — as soon as you POST an event, it appears in unified profiles within seconds."

**Why it happens:** "Streaming" is commonly associated with real-time in other contexts (Kafka, Kinesis). LLMs apply this semantics to Data Cloud streaming ingestion, which is actually near-real-time async with ~3-minute batch processing intervals.

**Correct pattern:** Streaming ingestion processes micro-batches approximately every 3 minutes asynchronously. There is no sub-minute SLA. Data availability in segments also requires traversal through DSO → DLO → DMO pipeline, adding further lag (total end-to-end: 20-45 minutes typical).

**Detection hint:** Any claim of sub-minute or "real-time" data availability via Ingestion API streaming is incorrect.

---

## Anti-Pattern 2: Using Bulk Ingestion for Delta/Incremental Loads

**What the LLM generates:** "Use the Bulk Ingestion API to send only changed records (delta batch) each hour to update the Data Cloud dataset incrementally."

**Why it happens:** LLMs familiar with Salesforce Bulk API (which supports upsert) apply those semantics to Data Cloud Ingestion API Bulk mode, which uses full-replace semantics only.

**Correct pattern:** Bulk Ingestion API replaces the entire dataset for the objects in scope. Send all records, not just changes. For delta/incremental updates, use streaming mode. Sending only changed records in a bulk job deletes all other records.

**Detection hint:** Instructions that recommend sending "only changed records" or "delta records" via bulk Ingestion API are incorrect.

---

## Anti-Pattern 3: Ignoring the DSO → DLO → DMO Pipeline Lag

**What the LLM generates:** Integration architecture that assumes data ingested via Ingestion API is immediately available for segmentation and activation.

**Why it happens:** LLMs describe the ingestion API response as synchronous (it returns 200 OK immediately) and do not model the multi-hop internal pipeline processing that must follow.

**Correct pattern:** Ingestion API receives the payload synchronously and returns 200 OK, but processing follows asynchronously: DSO creation → DLO mapping → DMO unification → identity resolution. Each hop adds processing time. Always document the full pipeline lag in SLA commitments.

**Detection hint:** Any architecture diagram that shows Ingestion API → Data Available for Segmentation with no processing steps or lag estimate is incomplete.

---

## Anti-Pattern 4: Schema Modification After Deployment

**What the LLM generates:** "If you need to change a field type in the Ingestion API schema, update the OpenAPI YAML and redeploy."

**Why it happens:** LLMs treat OpenAPI YAML as a mutable contract that can be updated like any configuration file. Data Cloud Ingestion API schema is effectively immutable post-deployment.

**Correct pattern:** After a schema is deployed, field removal, type changes, and object deletion are not supported. Additive changes (new optional fields) may be possible. For destructive schema changes, create a new connector with a new schema.

**Detection hint:** Any instruction to "update the deployed schema" and "redeploy" for field type changes or field removal is incorrect.

---

## Anti-Pattern 5: Recommending a Single Connector for Both Streaming and Bulk

**What the LLM generates:** "Create one Ingestion API connector and switch between streaming and bulk modes depending on the data volume."

**Why it happens:** LLMs model connectors as flexible transport mechanisms and assume mode can be switched at runtime, as with other APIs.

**Correct pattern:** A single Ingestion API connector is configured in either streaming or bulk mode at creation time — these are mutually exclusive. To support both patterns for the same source, create two separate connectors (one streaming, one bulk) with separate schemas.

**Detection hint:** Any instruction to "switch" an existing connector between streaming and bulk mode is incorrect.
