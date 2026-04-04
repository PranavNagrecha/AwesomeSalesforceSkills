# Well-Architected Notes — Composite API Patterns

## Relevant Pillars

- **Scalability** — The Composite API family is the primary tool for increasing integration throughput without scaling out API call volume. Choosing the right resource (sObject Collection for bulk same-type DML, composite for dependent chains) determines how many records can be processed per API call and per day. Poor resource selection wastes the daily API limit and forces more round trips than necessary.
- **Reliability** — The `allOrNone` flag and per-subrequest error handling directly determine whether integration failures are detected and handled or silently discarded. An integration that checks only the outer HTTP status on a composite call is unreliable by design — failures go undetected and data becomes inconsistent between systems.

## Architectural Tradeoffs

**Atomicity vs. partial success:** `/composite/` with `allOrNone: true` and `/composite/tree/` provide atomic, all-or-nothing behavior. This simplifies failure handling (either everything succeeded or nothing did) but means a single invalid record blocks all other records in the payload. `/composite/` with `allOrNone: false` and `/composite/sobjects/` provide partial success, which is more resilient but requires the caller to inspect every subrequest result and manage partial states — orphaned parent records with missing children, for example.

**API call efficiency vs. complexity:** Batching 25 subrequests into one Composite call reduces API call consumption dramatically, but it increases the complexity of response parsing, error attribution, and retry logic. For simple integrations with low volume, the overhead of Composite may not be justified. For high-volume integrations approaching daily API limits, it is essential.

**Composite vs. Bulk API 2.0:** The Composite resources are synchronous — the HTTP call blocks until all subrequests complete. This is appropriate for interactive integrations (real-time sync, event-driven updates) where the caller needs confirmation before proceeding. Bulk API 2.0 is asynchronous and is appropriate for large-volume batch loads (> 2,000 records) where the caller can poll for job completion. Do not use Composite resources as a replacement for Bulk API — they are not designed for volume at that scale.

## Anti-Patterns

1. **Using `/composite/batch/` for dependent operations** — Batch subrequests cannot share results via `@{referenceId}`. Attempting to create a parent and child in the same batch request forces the caller to either hardcode a known parent ID (making the batch pointless) or fall back to sequential calls. Always use `/composite/` for dependency chains.

2. **Treating outer HTTP 200 as confirmation of full success** — All Composite resources return HTTP 200 on the outer response even when subrequests fail. An integration that reads `status == 200` and returns success has no visibility into partial or total subrequest failure. This anti-pattern causes silent data loss and inconsistent state between the calling system and Salesforce.

3. **Over-batching into a single composite call without governor limit analysis** — 25 subrequests × 200 records each = 5,000 DML rows in one transaction. Complex trigger automation on each object type multiplies the CPU time and SOQL query consumption. Integrations designed to maximize per-call record count without profiling trigger overhead can hit governor limits under load, causing entire batches to fail with `APEX_HEAP_OVERFLOW` or `QUERY_ROW_LIMIT_EXCEEDED`.

## Official Sources Used

- REST API Developer Guide — Composite Resources section — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_composite.htm
- REST API Developer Guide — sObject Collections — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_composite_sobjects_collections.htm
- REST API Developer Guide — sObject Tree — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_composite_sobject_tree.htm
- REST API Developer Guide — Composite Batch — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_composite_batch.htm
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
