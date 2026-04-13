# Gotchas — Analytics External Data

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Live Datasets Do Not Materialize — Every Query Hits the External System

**What happens:** Teams configure a Live Dataset expecting it to behave like a refreshed materialized dataset — fast, consistent, and independent of the external system's availability. Instead, every time a dashboard loads or a SAQL query runs, CRM Analytics issues a live query to the external system (Snowflake, BigQuery, etc.). If the external system is slow, rate-limited, or unavailable, the dashboard fails or times out. There is no cached copy inside CRM Analytics.

**When it occurs:** Any time a Live Dataset is used as if it were a materialized dataset. Common in orgs where a Remote Connection was created and someone added a Live Dataset for convenience without reading the performance implications.

**How to avoid:** Explicitly decide — before any configuration — whether the use case requires a Live Dataset or a materialized Data Connector dataset. For dashboards accessed by many users simultaneously, benchmark Snowflake or BigQuery response times under concurrent load before committing to a Live Dataset. If freshness requirements allow any lag (even 15 minutes), a Data Connector with a scheduled refresh will produce more reliable dashboard performance.

---

## Gotcha 2: InsightsExternalData Metadata JSON Schema Must Be Created Before Data Rows

**What happens:** Integration developers attempt to upload CSV data rows (`InsightsExternalDataPart` records) before creating the parent `InsightsExternalData` header record with a valid `MetadataJson` field. The API rejects the part records or allows them but then fails the entire job at processing time with a schema validation error.

**When it occurs:** When developers model the External Data API like a bulk upload (send all the data, configure later) or when they construct the schema after noticing field types are wrong. Also common when copying patterns from Bulk API 2.0 jobs, which have a different sequencing model.

**How to avoid:** Enforce a strict three-step sequence in any integration that uses the External Data API:
1. Create the `InsightsExternalData` record with `MetadataJson` and `Action = None`.
2. Confirm the record was created successfully and capture its `Id`.
3. Upload all `InsightsExternalDataPart` records referencing that `Id`.
4. Only then PATCH the `InsightsExternalData` record to set `Action = Process`.

Never proceed to step 3 without a confirmed step 1 ID.

---

## Gotcha 3: Remote Connection Is a Configuration Object, Not a Data Upload Mechanism

**What happens:** After creating a Remote Connection in Data Manager (to Snowflake, BigQuery, etc.), practitioners assume data is now flowing into CRM Analytics automatically. The Remote Connection stores credentials and connection details only — it does not pull or copy any data. Dashboards built without a Recipe, Dataflow, or Live Dataset on top of the Remote Connection show no data or fail to load.

**When it occurs:** During initial setup when the practitioner sees a "connected" status on the Remote Connection and interprets it as data sync being active.

**How to avoid:** After creating a Remote Connection, always create a downstream artifact that actually moves or references data:
- For materialized data: create a Recipe or Dataflow input node that reads from the Remote Connection and writes to a CRM Analytics dataset.
- For live querying: create a Live Dataset that references the Remote Connection and a specific table or view.
The Remote Connection alone does neither.

---

## Gotcha 4: Data Connector Recipes Default to Full Refresh — Incremental Load Requires Explicit Configuration

**What happens:** A Recipe pulling from Snowflake or BigQuery re-downloads the entire source table on every scheduled run, even if only a small percentage of rows changed. For large tables this causes long refresh windows, excessive Snowflake credit consumption, and potential timeout failures before the refresh completes.

**When it occurs:** Any time a Recipe is created using the default settings without configuring an incremental load filter on the input node.

**How to avoid:** Add a filter on the Recipe input node anchored to a watermark field (e.g., `LastModifiedDate >= [last successful run timestamp]`). Store the watermark in a CRM Analytics dataset or an external parameter. This pattern requires the source table to have a reliable update timestamp column — confirm this before designing the Recipe.

---

## Gotcha 5: External Data API Chunk Size Limit Is 10 MB Compressed, Not Raw

**What happens:** A developer splits a large CSV into 10 MB raw chunks and uploads them as `InsightsExternalDataPart` records. The parts are rejected or cause a processing failure because the per-part limit applies to the gzip-compressed size of the chunk, not the raw CSV size. Depending on compression ratio, a raw 10 MB CSV chunk may compress to 2–3 MB, meaning raw chunk sizes can be larger — but submitting raw (uncompressed) data that exceeds limits causes failures.

**When it occurs:** When developers read the API limit as a raw file size limit rather than a compressed payload limit, or when they send uncompressed CSV data without gzip encoding.

**How to avoid:** Always gzip-compress CSV data before uploading `InsightsExternalDataPart` records. Design chunk splitting logic around the compressed output size (target under 10 MB post-compression). Validate chunk sizes programmatically before upload rather than relying on the API to catch oversized parts.

---

## Gotcha 6: Live Dataset SAQL Support Is a Subset of Full SAQL

**What happens:** A developer writes a SAQL query against a Live Dataset using constructs (certain aggregation functions, cross-dataset joins, or SAQL-specific syntax) that work against materialized CRM Analytics datasets but are not supported by the Live Dataset query translation layer. The query fails at runtime or returns incorrect results.

**When it occurs:** When developers assume Live Datasets are fully equivalent to materialized datasets from a query perspective. The query translation layer converts SAQL to the external warehouse's SQL dialect, and some SAQL constructs have no direct equivalent.

**How to avoid:** Test every SAQL query intended for a Live Dataset against the actual Live Dataset before building dashboard components. Consult the CRM Analytics Live Dataset documentation for the supported SAQL construct list. If a required construct is unsupported, reconsider whether a materialized Data Connector dataset is the correct approach.
