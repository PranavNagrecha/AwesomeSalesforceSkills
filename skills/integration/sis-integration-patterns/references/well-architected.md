# Well-Architected Notes — SIS Integration Patterns

## Relevant Pillars

- **Reliability** — SIS integrations are mission-critical: enrollment records, grade results, and student credentials directly affect registration, financial aid disbursement, and degree audits. The integration must handle middleware downtime gracefully using CDC event replay (72-hour retention) or Bulk API 2.0 job resumption. A failed nightly batch must not leave Salesforce and the SIS in a divergent state.
- **Performance** — Nightly batch loads for institutions with 20,000–100,000+ students involve millions of record operations across multiple Education Cloud objects. Using Bulk API 2.0 (not REST single-record DML) and parallelizing independent object layers avoids hitting the 24-hour API call limit and prevents Apex CPU/heap governor exceptions. Watermark-based incremental loads reduce nightly job duration from hours to minutes after steady-state is reached.
- **Security** — Education Cloud objects store FERPA-protected academic records. Integration users must be assigned only the minimum required object and field permissions. FLS must block access to FERPA-sensitive fields (e.g., grades in `CourseOfferingPtcpResult`) from integration users who do not require them. Integration payloads and error logs must not expose student academic records to non-authorized systems or log aggregators.
- **Operational Excellence** — SIS integrations run unattended in production. Every Bulk API 2.0 job must emit its `numberRecordsFailed` count to a monitoring system. Failed records must be routed to an error queue with enough context (External ID value, error code, error message) for the integration team to triage and resubmit without re-running the full nightly batch.

## Architectural Tradeoffs

**Batch vs. near-real-time:**
Nightly batch (Pattern 1) is simpler to build and operate, but enrollment status changes made in Salesforce during business hours do not reach the SIS until the following morning. This is acceptable for most administrative workflows but fails for institutions that require same-day registration confirmation or real-time Financial Aid status checks in the SIS. CDC-based writeback (Pattern 2) adds middleware complexity but eliminates overnight lag for status changes.

**Bulk API 2.0 vs. REST Composite:**
Bulk API 2.0 is the only viable option for nightly loads of more than ~500 records per object. REST Composite sObject Collections supports up to 200 records per request and up to 25 sObject types per composite call, suitable for transactional writes (e.g., a student self-service add/drop that affects 3–5 records). Choosing REST for large batch loads consumes the org's 24-hour REST API call limit and introduces concurrency conflicts with other integrations.

**External ID encoding:**
A composite External ID encoding (e.g., `PIDM|TermCode`) is simpler to implement than a multi-field lookup but creates a dependency on a consistent encoding convention across the SIS and the middleware. If the SIS changes identifier formats (e.g., Banner migrates to a UUID-based identifier), all External ID fields and middleware transformations must be updated simultaneously.

## Anti-Patterns

1. **Using SOQL query-then-DML instead of External ID upsert** — Querying Salesforce record IDs before each DML operation doubles API call volume, introduces race conditions between concurrent integration processes, and fails to handle the case where a record is deleted between the query and the DML. Always use External ID upsert; pre-query only when External ID-based upsert is genuinely not possible.

2. **Loading parent and child Education Cloud objects in the same Bulk API 2.0 job** — Bulk API 2.0 does not guarantee intra-job record processing order. Mixing `AcademicTermEnrollment` (parent) and `CourseOfferingParticipant` (child) in one job causes nondeterministic `INVALID_CROSS_REFERENCE_KEY` failures for child records processed before their parents. Always use separate, sequentially-dependent jobs per object layer.

3. **Treating CDC events as full-record snapshots** — Change Data Capture events contain only the fields that changed, not the full record state. Middleware that reads all fields from a CDC payload without checking `changedFields` will write null values for unchanged fields to the SIS, corrupting SIS records. Always check `changedFields` and retrieve the full record via a follow-up SOQL query when full state is needed.

## Official Sources Used

- Education Cloud Developer Guide v66.0 — https://developer.salesforce.com/docs/atlas.en-us.edu_cloud_dev_guide.meta/edu_cloud_dev_guide/
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Integration Patterns and Best Practices — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
