# Well-Architected Notes — Bulk API Patterns

## Relevant Pillars

### Scalability

Bulk API 2.0 is the primary mechanism for processing data at scale in Salesforce. The platform's async infrastructure handles internal batch creation and distribution automatically, up to 150,000,000 records per rolling 24 hours across ingest jobs. The key scalability constraint is job size: a job takes at most 150 MB after base64 encoding, roughly 100 MB of raw CSV. For larger datasets, the integration splits the source into several jobs and reconciles each one.

For query jobs, automatic PK chunking enables extraction of arbitrarily large result sets by splitting the SOQL query into sub-ranges and distributing them across the async infrastructure. Combined with locator-based pagination, this makes bulk export of tens of millions of records reliable and resumable.

Scalability anti-pattern: using synchronous REST Composite or Apex DML for operations that grow to thousands of records as data volumes increase over time. Integrations that work at current volumes can fail unexpectedly after data growth hits API call limits or governor limits. Design for the anticipated data volume ceiling, not the current volume.

### Reliability

Bulk API 2.0 partial success is the default behavior. A `JobComplete` state does not mean all records were written — it means Salesforce finished processing attempts. Reliability requires:

1. Retrieving `successfulResults` and `failedResults` after every terminal state, plus `unprocessedrecords` for `Failed` or `Aborted` jobs.
2. Implementing an integrity check: the counts must equal the total records uploaded.
3. Automating retry logic: failed and unprocessed records must be submitted as new jobs after root-cause remediation.
4. Preserving the source CSV until all records are confirmed as either successfully processed or explicitly triaged.

Jobs in `Failed` or `Aborted` state are not automatically retried by Salesforce. The caller is responsible for detecting these terminal failure states and deciding whether to abort or resubmit.

## Architectural Tradeoffs

**v2.0 vs v1.0 simplicity vs capability:** Bulk API 2.0 reduces integration complexity significantly — no WSDL, no manual batch creation, unified result endpoints, automatic PK chunking. The tradeoff is loss of serial concurrency mode and support for non-CSV content types. Accept this tradeoff in all new implementations. The complexity cost of maintaining Bulk API v1 integrations outweighs the serial mode benefit in most cases; lock contention can usually be managed at the data layer by sorting CSV by parent ID before upload.

**Multipart vs standard create:** Multipart job creation eliminates the UploadComplete PATCH at the cost of a 100,000-character payload cap. Use multipart for predictably small integrations (100,000 characters is roughly 1,500 rows at 60 characters each) where reliability through simplicity outweighs the size limit. Use standard create + upload + PATCH for anything that may grow or already exceeds the character limit.

**Locator pagination reliability:** A query job's locator does not change as long as the job exists. This makes locator-based downloads resumable — the integration can save the last successful locator and restart from that page without re-processing earlier pages. This is a meaningful reliability advantage over approaches that depend on SOQL offset pagination, where large offsets can time out on objects with millions of records.

## Anti-Patterns

1. **Declaring job success on `JobComplete` without checking all three result endpoints** — `JobComplete` is a processing-complete signal, not a data-integrity signal. Treating it as success without retrieving `failedResults` (and `unprocessedrecords` when a job ends `Failed`) leaves record-level failures and unprocessed rows invisible. This creates a silent data drift between source and target systems that only surfaces downstream, often much later.

2. **Attempting to use serial concurrency mode in Bulk API 2.0** — Developers who need to prevent lock contention sometimes try to configure `concurrencyMode: Serial` in a Bulk API 2.0 job. The guide describes this field as for future use; only parallel mode is supported. The correct response to lock contention in v2.0 is to sort the CSV by parent ID (grouping related records into the same internal batch) and defer sharing calculation during the load window. If serial mode is truly required, use Bulk API v1 — but document the dependency so it can be revisited when the lock-prone trigger architecture is refactored.

3. **Ignoring `lineEnding` and `columnDelimiter` job creation fields** — Omitting these fields and relying on defaults (`LF`, `COMMA`) without verifying the actual CSV format creates fragile integrations that break silently when source systems change their export format or when the pipeline runs on a different OS. Always inspect the CSV and explicitly declare the format at job creation time.

## Official Sources Used

Read for this revision (2026-10-19):

- Bulk API 2.0 and Bulk API Developer Guide (`api_asynch.txt`): v2 versus v1 comparison (ingest from API 41.0, content types, automatic versus manual PK chunking, big objects) (L177-201); 150 MB per job (L602); upload completed automatically for multipart jobs (L814-815); 10,000-record internal batches, 150,000,000 daily, 5-minute batches, 20 retries then job Failed (L1242-1247); Prepare CSV Files: UTF-8, base64 growth, delimiters, lineEnding, quoting, no trimming, empty values ignored on update, `#N/A`, 32,000-character header (L1280-1318); dateTime formats (L1454-1460); `concurrencyMode` for future use (L1668-1670); multipart for 100,000 characters or less (L1726); upload request limit (L1782-1787); `sf__Id`, `sf__Created`, `sf__Error` (L2113-2161); unprocessed records for failed or aborted jobs at `.../unprocessedrecords/` (L2188-2190); lock contention guidance (L2694-2708); query results `locator`, `maxRecords`, `Sforce-Locator` string `null`, do not guess locators (L3336-3506); PK chunking header in v1 (L7313-7356); job info counters (L1992-1997).
- Salesforce Developer Limits and Allocations Quick Reference (`salesforce_app_limits_cheatsheet.txt`): 2,000-record guidance and 15,000 shared batches per rolling 24 hours (264 L293-303); 24-hour open job and 7-day results (264 L340-342, L386-389); 150 MB per job for Bulk API 2.0 (264 L391). Values unchanged from the 262 edition, which had them at L729-818.
- REST API Developer Guide (`api_rest.txt`): regular composite requests limited to 25 subrequests, composite graphs 500 (L6288).
- Best Practices for Deployments with Large Data Volumes (`salesforce_large_data_volumes_bp.txt`): consider Bulk API 2.0 query for results over one million rows (L913-915).

Listed in the original version and not re-read (same guides as PDFs above, or framing only):

- Bulk API 2.0 Developer Guide (atlas) — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
