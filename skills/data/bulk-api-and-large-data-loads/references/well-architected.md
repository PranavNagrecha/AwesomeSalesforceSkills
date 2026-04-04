# Well-Architected Notes — Bulk API and Large Data Loads

## Relevant Pillars

- **Reliability** — Bulk API 2.0 jobs are asynchronous and can fail at the batch level or the record level independently. A well-architected bulk pipeline retrieves all three result endpoints after every job, implements a retry loop for failed and unprocessed records, and archives source data until full success is confirmed. Without explicit retry logic, partial failures silently reduce data completeness.

- **Operational Excellence** — Bulk jobs must be observable. This means: polling until a terminal state, logging `numberRecordsProcessed` and `numberRecordsFailed` from the job status response, alerting on non-zero failed or unprocessed counts, and tracking job IDs for audit purposes. A pipeline that submits a job and does not monitor it creates invisible operational debt.

- **Performance** — Choosing the wrong API tier (REST Composite vs. Bulk API 2.0) is a common performance anti-pattern. Using synchronous REST for >2,000 records exhausts API call limits and creates unnecessary latency. Conversely, using Bulk API for trivial <100 record operations adds unnecessary async overhead. The decision boundary documented in this skill (>2,000 records → Bulk API 2.0) is the official Salesforce guidance from the Large Data Volumes Best Practices document.

- **Security** — Bulk API 2.0 uses standard OAuth 2.0 bearer token authentication, consistent with other Salesforce REST APIs. The running user's profile and permission sets govern which records can be created, updated, or deleted — bulk jobs are not elevated-privilege operations. The `hardDelete` operation bypasses the Recycle Bin and is irreversible; it should be restricted to integration users with explicit `Bulk API Hard Delete` permission.

## Architectural Tradeoffs

**Parallel vs. serial throughput:** Parallel mode is significantly faster but introduces lock contention risk on trigger-heavy objects. Serial mode eliminates lock errors but serializes all batch processing, which can extend a multi-hour load into a multi-day load at high volumes. The correct tradeoff depends on object complexity and load window constraints. Default to parallel; switch to serial only after diagnosing lock errors in production data.

**Atomic vs. partial success:** Bulk API 2.0 does not provide atomicity across records. Successfully processed records are committed immediately and are not rolled back when other records in the same job fail. This is intentional for performance at scale, but means migrations must plan for partial state: some records exist in Salesforce before the full load is confirmed. Applications that query the object during a bulk load may see incomplete data.

**Synchronous vs. asynchronous error visibility:** Synchronous REST returns errors immediately per record. Bulk API 2.0 defers error visibility until after job completion — a multi-hour delay for large jobs. Pipelines must poll for completion and retrieve results before reporting success or triggering downstream processes.

## Anti-Patterns

1. **Treating JobComplete as all-records-succeeded** — `JobComplete` means Salesforce attempted all batches. Individual records may be in `failedResults` or `unprocessedRecords`. Integrations that do not retrieve these endpoints will silently drop failed records with no error surfaced. Every production bulk pipeline must retrieve all three result endpoints unconditionally.

2. **Using Bulk API 2.0 for sub-2,000 record operations** — The async overhead of job creation, upload, polling, and result retrieval adds latency and complexity for operations that synchronous REST Composite handles in a single round trip. Use the right tier for the volume.

3. **Not retaining the source CSV until full confirmation** — If a bulk job fails mid-load and the source data is not retained, the caller cannot reconstruct which records to resubmit. The Salesforce documentation explicitly advises: "Don't delete your local CSV data until you've confirmed that all records were successfully processed." Archive source data per job until the retry loop exits with zero failures.

4. **Bypassing business logic assumptions** — Assuming bulk loads skip validation rules or triggers is a data integrity risk. Rules and triggers always fire on bulk records. Test with a pilot batch on a sandbox with production-equivalent configuration before running a full load.

## Official Sources Used

- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Salesforce Large Data Volumes Best Practices — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/
- Bulk API and Bulk API 2.0 Limits and Allocations — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_bulkapi.htm
