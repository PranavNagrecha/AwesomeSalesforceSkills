# Well-Architected Notes — REST API Patterns

## Relevant Pillars

### Reliability

REST integrations must handle partial failure, transient errors, and API throttling without data loss or silent corruption. Key reliability concerns:

- Composite requests with `allOrNone: false` can partially succeed. The integration must inspect every subrequest result and apply compensating logic for any failures rather than assuming the full batch succeeded.
- Paginated queries must follow `nextRecordsUrl` to completion. A loop that stops early silently exports an incomplete data set.
- Token expiry and 401 responses must be handled with a refresh-and-retry path, not just an error log.
- HTTP 429 and 503 throttling responses require back-off with `Retry-After` header respect, not immediate retry hammering.

### Scalability

The REST API is designed for record-level and small-batch operations. Scalability failures occur when REST is used outside its designed volume range:

- The daily API limit scales with org edition and user license count but is finite. High-frequency polling integrations consume this budget rapidly. Prefer event-driven patterns (Change Data Capture, Platform Events) to reduce polling-based API consumption.
- Composite and Composite Batch cap at 25 subrequests. sObject Tree caps at 200 records per call. Designs that need to exceed these limits belong on Bulk API 2.0.
- Concurrent long-running request limits (25 simultaneous requests > 20 seconds) are separate from the daily limit and can be exhausted by parallel batch scripts even when daily headroom remains.

## Architectural Tradeoffs

**REST Composite vs. multiple single-record calls:**
Composite reduces HTTP overhead and enables server-side reference wiring, but introduces result-parsing complexity. The tradeoff is appropriate when operations are logically related and must succeed or fail together, or when round-trip latency is a real constraint.

**`allOrNone: true` vs. `allOrNone: false` on Composite:**
`allOrNone: true` gives atomicity at the cost of all-or-nothing failure. `allOrNone: false` allows partial success but requires the caller to implement reconciliation for failed subrequests. Choose based on whether partial record creation is a worse outcome than full rollback.

**REST vs. Bulk API for medium volumes (2,000–10,000 records):**
REST Composite and sObject Tree can handle up to a few thousand records per integration cycle with multiple calls, but the API limit budget is consumed record-by-record. For regular large-volume syncs, Bulk API 2.0 is more efficient and less likely to exhaust daily limits. REST is better suited for real-time, low-latency, single-record or small-batch operations.

**Polling vs. event-driven:**
REST-based polling (repeated SOQL queries for changed records) consumes API limit budget proportionally to polling frequency. For change detection, prefer Change Data Capture or Platform Events to shift the trigger to the platform and eliminate unnecessary API calls when there is no new data.

## Anti-Patterns

1. **Ignoring `nextRecordsUrl`** — Stopping after the first page of a SOQL query silently discards records beyond the batch size. There is no error raised; the integration proceeds with incomplete data. Always loop until `done: true`.

2. **Treating outer HTTP 200 as full success for Composite calls** — The Composite envelope HTTP status only reflects whether the composite request itself was parseable and executed. Individual subrequest failures are embedded in the response body. This anti-pattern leads to silent data loss in production integrations.

3. **Hard-coding old API versions** — Pinning to a specific old version in code without a configuration mechanism means version upgrades require code changes. As Salesforce retires old versions, the integration breaks silently at retirement date. Always configure the API version externally and default to a version within the last four releases.

4. **Using REST for bulk data movement** — REST sObject CRUD and Composite are optimized for low-latency, small-batch operations. Using REST to insert tens of thousands of records in a loop burns through the daily API limit, generates high concurrency, and is significantly slower than Bulk API 2.0 for the same data volume.

## Official Sources Used

- REST API Developer Guide — resource reference, request/response semantics, Composite resources, pagination, error format
  https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm

- Integration Patterns — synchronous vs. asynchronous pattern selection, API limit considerations, event-driven vs. polling tradeoffs
  https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html

- Salesforce Well-Architected Overview — reliability and scalability pillar framing, anti-pattern structure
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
