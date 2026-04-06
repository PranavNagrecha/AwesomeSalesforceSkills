# Well-Architected Notes — Record Locking and Contention

## Relevant Pillars

- **Reliability** — Lock contention causes transaction failures that are often transient and difficult to reproduce. A reliable system must handle lock failures gracefully with retry logic rather than surfacing raw errors to users or integration partners.
- **Scalability** — Locking problems are volume-dependent. A solution that works at 1,000 records may fail at 100,000. Scalable designs minimize lock scope, sort for consistent ordering, and use serial processing for skewed data.
- **Performance** — Every lock is a serialization point. Holding locks longer than necessary (e.g., expensive logic after FOR UPDATE) degrades throughput for all concurrent users. Performance-conscious designs minimize the lock-hold window.

## Architectural Tradeoffs

### Consistency vs. Throughput

FOR UPDATE provides strong consistency for read-modify-write patterns but serializes access and reduces throughput. Use it only when the race condition is real and consequential (e.g., inventory decrement, counter update). For most DML, implicit locking at DML time provides adequate consistency with minimal throughput cost.

### Serial vs. Parallel Processing

Serial Bulk API mode eliminates contention but increases total processing time. The tradeoff is acceptable when data skew makes parallel mode unreliable. The decision should be driven by the skew profile of the data, not applied as a blanket default.

### Retry Complexity vs. Failure Tolerance

Adding Queueable retry logic increases code complexity and introduces eventual consistency. This is justified only when lock contention is transient and the business process tolerates a short delay. For processes requiring immediate confirmation, reducing contention at the source is preferable to retrying after failure.

## Anti-Patterns

1. **Blanket FOR UPDATE on all queries** — increases lock scope and contention instead of reducing it. FOR UPDATE should be surgical, applied only to read-modify-write patterns.
2. **Ignoring parent-child lock escalation** — optimizing child-record DML without recognizing that the parent row is the real bottleneck. The fix is at the data-model or ordering level, not in the child DML code.
3. **Retrying in a synchronous loop** — catching UNABLE_TO_LOCK_ROW and retrying in a while loop burns CPU time and contends on the same lock window. Async retry with Queueable is the correct pattern.

## Official Sources Used

- Apex Developer Guide: Locking Statements — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_locking_statements.htm
- SOQL FOR UPDATE Reference — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_for_update.htm
- Salesforce Help: Record Locking — https://help.salesforce.com/s/articleView?id=000384498&type=1
- Designing Record Access for Enterprise Scale — https://architect.salesforce.com/design/decision-guides/record-access
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
