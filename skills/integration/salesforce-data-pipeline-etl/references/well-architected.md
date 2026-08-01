# Well-Architected Notes — Salesforce Data Pipeline / ETL

**Scalability:** volume extraction belongs to Bulk API 2.0 query jobs and the ongoing
delta to a streaming subscription. Paged SOQL for either consumes the org's shared 24-hour
API allocation and competes with every other integration. Take the branch in
`standards/decision-trees/integration-pattern-selection.md` explicitly — the axis is
record volume against freshness, and a requirement that sits on both branches needs both
mechanisms with a defined handover point.

**Reliability:** a timestamp watermark cannot represent deletion, because a deleted record
stops appearing rather than reappearing with a new timestamp. That is a correctness
defect, not a latency one, and it accumulates silently. Change events carry delete and
undelete explicitly, which is the main argument for streaming over polling once the
initial load is done. Checkpoint the replay id after processing rather than on receipt, and
treat a rejected replay id as an automatic trigger for re-snapshot rather than as a
retryable error.

**Operational Excellence:** the failure that matters is the run that succeeds while
dropping rows, which raises no error anywhere. An independent reconciliation — counts per
object per created-date bucket, alerting on drift rather than on job status — is the only
thing that finds it.

## Official Sources Used

- System fields — SystemModstamp is platform-maintained, LastModifiedDate is settable with Set Audit Fields — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/system_fields.htm
- Change Data Capture Developer Guide — change event header, change types, gap and overflow events, and event retention — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Bulk API 2.0 Developer Guide — query jobs and the queryAll operation for soft-deleted rows — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/queries.htm
- Pub/Sub API — durable subscription and replay id semantics — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/intro.html
- SOQL queryAll and IsDeleted — retrieving records from the Recycle Bin — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_queryall.htm
