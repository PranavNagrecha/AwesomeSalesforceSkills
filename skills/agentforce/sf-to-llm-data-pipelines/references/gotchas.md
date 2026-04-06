# Gotchas — SF-to-LLM Data Pipelines

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Bulk API v2 Result Cursor Expires After 10 Minutes of Inactivity

**What happens:** After a Bulk API v2 query job reaches `JobComplete`, Salesforce holds the result set available for download via a paginated cursor tracked through the `Sfdclocator` response header. If the consumer pauses for more than 10 minutes between successive GET requests to the results endpoint — for any reason, including downstream backpressure, rate-limit sleep, or a process crash — the cursor expires and the result set becomes unavailable. Subsequent requests to the results endpoint return a 404 or an error indicating the job results are no longer available.

**When it occurs:** Any pipeline that applies throttling or backpressure between result batch downloads is at risk. Common triggers: the embedding API rate limit is hit mid-download and the pipeline sleeps to wait for the rate limit window to reset; the vector store write is slow and blocks the download loop; the process crashes after downloading the first few batches and a partial-resume is attempted.

**How to avoid:** Separate the download phase from the processing phase. Download all result batches to local storage (disk or in-memory queue) as fast as possible, then process (embed and upsert) from local storage. Never interleave embedding or vector store writes with the Bulk API v2 result download loop. If a crash occurs mid-download, re-submit the entire Bulk API v2 job — do not attempt to resume from a partial cursor.

---

## Gotcha 2: `SystemModstamp` Is Updated by Workflow and Process Builder Evaluations Even When No Fields Change

**What happens:** `SystemModstamp` is updated whenever Salesforce evaluates any automation rule (Workflow Rule, Process Builder, Flow) on a record, even if the evaluation results in no field changes. A nightly scheduled Flow or a record-triggered automation that evaluates but takes no action against a record will advance `SystemModstamp`, causing that record to appear in the next incremental Bulk API v2 extraction as a "changed" record even though its data is identical to the previous extraction.

**When it occurs:** Orgs with active Workflow Rules or Scheduled-Path Flows that evaluate large object populations will see inflated incremental extraction volumes. A Flow with a scheduled path running against all open Cases nightly will touch every record's `SystemModstamp` nightly, effectively turning incremental extraction into a de-facto full extraction.

**How to avoid:** Before relying on `SystemModstamp` for incremental watermarks, audit the org for scheduled or record-triggered automations that run against the target object. If automation churn is high, add a deduplication check at the chunking layer: compare the hash of the extracted record's content fields against the hash stored in the previous run's metadata. Skip re-embedding records whose content hash has not changed, even if `SystemModstamp` was advanced.

---

## Gotcha 3: Bulk API v2 Processes Mixed-Encoding CSV That Breaks Standard CSV Parsers

**What happens:** Salesforce Bulk API v2 query results are returned as UTF-8 CSV, but certain field values — particularly long text areas, rich text, and case descriptions — may contain embedded newlines, commas, and double quotes within fields. RFC 4180 requires these to be enclosed in double-quotes with internal double-quotes escaped as `""`. Salesforce follows this spec, but many naive CSV parsers (including simple `split(",")` implementations and some versions of `pandas.read_csv` with default settings) fail to handle multi-line fields correctly, silently truncating or corrupting records that span multiple CSV rows.

**When it occurs:** Any object with Long Text Area or Rich Text Area fields is at risk. Common affected fields: `Case.Description`, `Case.Resolution__c`, `KnowledgeArticleVersion.Body`, `Task.Description`, custom long text fields on any object.

**How to avoid:** Use a spec-compliant CSV parser. In Python, the built-in `csv.DictReader` handles RFC 4180 multi-line fields correctly. Do not use `str.split(",")`, `pandas.read_csv` with `engine='python'` and default quoting, or any line-by-line text processing on Bulk API v2 result files. Always validate that the row count in the parsed result matches the `numberRecordsProcessed` field returned by the Bulk API v2 job status endpoint.

---

## Gotcha 4: Knowledge Article `Body` Returns Content for the Draft Version When PublishStatus Filter Is Omitted

**What happens:** `KnowledgeArticleVersion` has a `PublishStatus` field with values `Draft`, `Online`, and `Archived`. If the SOQL query omits the `WHERE PublishStatus = 'Online'` filter, the Bulk API v2 job returns all versions including drafts and archived articles. Draft articles may contain incomplete, unreviewed, or confidential content that should not be indexed in the external vector store. Archived articles may contain superseded information that produces incorrect LLM responses.

**When it occurs:** Every time the SOQL query against `KnowledgeArticleVersion` omits the `PublishStatus` filter. This is easy to miss because the REST API's Knowledge-specific endpoints apply this filter implicitly, but the Bulk API v2 SOQL path does not.

**How to avoid:** Always include `WHERE PublishStatus = 'Online'` in `KnowledgeArticleVersion` queries. If multilingual orgs are in scope, also filter by `Language` to avoid indexing non-English (or non-target-language) article versions alongside the primary language index, which degrades retrieval quality for single-language queries.

---

## Gotcha 5: External Vector Store Delete Requires the Original Record ID — Which You May Have Pseudonymized

**What happens:** When a GDPR Right-to-Erasure request is received, the team must delete all vector chunks associated with the individual from the external vector store. If the pipeline pseudonymized the Salesforce record ID before writing to the vector store (which is the correct PII approach), the external store has only the pseudonym — not the Salesforce ID. Without the pseudonym-to-ID mapping table, it is impossible to find and delete the individual's chunks. If the mapping table is lost, Right-to-Erasure compliance becomes unachievable without a full re-index.

**When it occurs:** Any pipeline that pseudonymizes record IDs must also maintain the reverse mapping. Teams that implement pseudonymization without planning the erasure workflow discover this gap only when the first erasure request arrives.

**How to avoid:** Treat the pseudonym mapping table as a first-class durable artifact, not an implementation detail. Store it in a system of record that supports access control and audit logging (e.g., a dedicated database table, not a local file or in-memory dict). The mapping must be retained as long as pseudonymized chunks exist in the external vector store. Deletion of a mapping entry is itself a step in the erasure procedure — only after the corresponding chunks are confirmed deleted from the vector store.

---

## Gotcha 6: Bulk API v2 Daily Byte Limit Is Shared Across All Connected Apps

**What happens:** The Bulk API v2 daily processed-records limit is an org-wide limit shared across all connected apps authenticating to the org. The limit varies by Salesforce edition: in Enterprise Edition, the base limit is approximately 200 MB of compressed data per 24-hour rolling period (the exact limit is documented in Salesforce's API limits help article and varies by release). An extraction pipeline running a large full-load job may consume the majority of the daily Bulk API v2 quota, causing other integration processes that use Bulk API v2 (data loaders, middleware sync jobs) to fail with `EXCEEDED_ID_LIMIT` errors for the remainder of the window.

**When it occurs:** Multi-tenant orgs where multiple teams or integrations share a single Salesforce org. Common in enterprise environments where the CRM org also has active data loader jobs, middleware sync (e.g., MuleSoft, Boomi), and the new extraction pipeline all running against the same object.

**How to avoid:** Before deploying the extraction pipeline, audit Bulk API v2 usage in the org via Setup > Apex Jobs > Bulk API Request Limits. Schedule the extraction job during off-peak hours when other Bulk API consumers are idle. For large full loads, consider spreading extraction across multiple nights (e.g., extract accounts on Monday, contacts on Tuesday) to stay within daily limits.
