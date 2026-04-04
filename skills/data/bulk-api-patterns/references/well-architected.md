# Well-Architected Notes — Bulk API Patterns

## Relevant Pillars

### Scalability

Bulk API 2.0 is the primary mechanism for processing data at scale in Salesforce. The platform's async infrastructure handles internal batch creation and distribution automatically, allowing a single ingest job to process 150,000,000 records per org per day. The key scalability constraint is upload chunk sizing: each PUT must stay under 150 MB base64-encoded, which equates to roughly 100 MB of raw CSV. For extremely large datasets, the integration must split the source data into multiple chunks and upload them sequentially before signaling `UploadComplete`.

For query jobs, automatic PK chunking enables extraction of arbitrarily large result sets by splitting the SOQL query into sub-ranges and distributing them across the async infrastructure. Combined with locator-based pagination, this makes bulk export of tens of millions of records reliable and resumable.

Scalability anti-pattern: using synchronous REST Composite or Apex DML for operations that grow to thousands of records as data volumes increase over time. Integrations that work at current volumes can fail unexpectedly after data growth hits API call limits or governor limits. Design for the anticipated data volume ceiling, not the current volume.

### Reliability

Bulk API 2.0 partial success is the default behavior. A `JobComplete` state does not mean all records were written — it means Salesforce finished processing attempts. Reliability requires:

1. Retrieving all three result endpoints (`successfulResults`, `failedResults`, `unprocessedRecords`) after every terminal state.
2. Implementing an integrity check: the sum of all three counts must equal the total records uploaded.
3. Automating retry logic: failed and unprocessed records must be submitted as new jobs after root-cause remediation.
4. Preserving the source CSV until all records are confirmed as either successfully processed or explicitly triaged.

Jobs in `Failed` or `Aborted` state are not automatically retried by Salesforce. The caller is responsible for detecting these terminal failure states and deciding whether to abort or resubmit.

## Architectural Tradeoffs

**v2.0 vs v1.0 simplicity vs capability:** Bulk API 2.0 reduces integration complexity significantly — no WSDL, no manual batch creation, unified result endpoints, automatic PK chunking. The tradeoff is loss of serial concurrency mode and support for non-CSV content types. Accept this tradeoff in all new implementations. The complexity cost of maintaining Bulk API v1 integrations outweighs the serial mode benefit in most cases; lock contention can usually be managed at the data layer by sorting CSV by parent ID before upload.

**Multipart vs standard create:** Multipart job creation eliminates the UploadComplete PATCH at the cost of a 100,000-character payload cap. Use multipart for predictably small nightly integrations (under ~5,000 records of typical width) where reliability through simplicity outweighs the size limit. Use standard create + upload + PATCH for anything that may grow or already exceeds the character limit.

**Locator pagination reliability:** Query job locators are stable for the lifetime of the job. This makes locator-based downloads resumable — the integration can save the last successful locator and restart from that page without re-processing earlier pages. This is a meaningful reliability advantage over approaches that depend on SOQL offset pagination, where large offsets can time out on objects with millions of records.

## Anti-Patterns

1. **Declaring job success on `JobComplete` without checking all three result endpoints** — `JobComplete` is a processing-complete signal, not a data-integrity signal. Treating it as success without retrieving `failedResults` and `unprocessedRecords` means record-level failures and batch-timeout losses are invisible. This creates a silent data drift between source and target systems that only surfaces downstream, often much later.

2. **Attempting to use serial concurrency mode in Bulk API 2.0** — Developers who need to prevent lock contention sometimes try to configure `concurrencyMode: Serial` in a Bulk API 2.0 job. This field is reserved and has no effect in v2.0. The correct response to lock contention in v2.0 is to sort the CSV by parent ID (grouping related records into the same internal batch) and defer sharing calculation during the load window. If serial mode is truly required, use Bulk API v1 — but document the dependency so it can be revisited when the lock-prone trigger architecture is refactored.

3. **Ignoring `lineEnding` and `columnDelimiter` job creation fields** — Omitting these fields and relying on defaults (`LF`, `COMMA`) without verifying the actual CSV format creates fragile integrations that break silently when source systems change their export format or when the pipeline runs on a different OS. Always inspect the CSV and explicitly declare the format at job creation time.

## Official Sources Used

- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Bulk API and Bulk API 2.0 Limits and Allocations — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_bulkapi.htm
- Salesforce Large Data Volumes Best Practices — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_introduction.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
