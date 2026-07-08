# Well-Architected Notes — Batch Apex Patterns

## Relevant Pillars

### Scalability

Batch Apex is a scale-oriented tool for workloads that exceed a normal transaction.

Tag findings as Scalability when:
- a very large dataset must be processed safely
- direct list loading is used where QueryLocator would be safer
- a smaller async mechanism is being stretched beyond its intended volume
- the addressable set exceeds the 50-million-record `Database.QueryLocator` cap and should use a custom `Iterable`
- a fan-out design ignores the 5-concurrent-job cap and the 100-job Apex flex queue

### Governor Limits That Bound Large-Volume Design

The hard ceilings that a large-data-volume batch design must respect:

- **5** batch jobs queued or active concurrently; the Apex flex queue holds up to **100** more in `Holding`.
- **250,000** batch method executions per 24-hour period, or user licenses × **200**, whichever is greater.
- **50 million** records maximum from a `Database.QueryLocator`; a custom `Iterable` is not subject to this cap but falls under normal per-transaction SOQL limits.
- Scope size defaults to **200** and maxes at **2,000** when `start()` returns a `QueryLocator`; an `Iterable` scope has no upper bound.

### Performance

Scope size, query shape, and serialization overhead directly affect throughput and runtime.

Tag findings as Performance when:
- scope sizes are mismatched to the actual work
- `Database.Stateful` is carrying unnecessary weight
- callout payloads are too large per batch scope

### Reliability

Reliable batches are idempotent, monitored, and explicit about partial failures.

Tag findings as Reliability when:
- `execute()` is not safe to retry
- job monitoring is absent
- all-or-none semantics are used where per-record outcomes matter

## Architectural Tradeoffs

- **Batch vs Queueable:** Batch is more powerful for volume, but more operationally expensive.
- **Stateful vs stateless:** stateful helps summaries and retries, but increases overhead.
- **Large scope vs small scope:** larger scopes can improve throughput until they start causing CPU, lock, or callout trouble.

## Anti-Patterns

1. **Using Batch where Queueable would do** — ceremony without gain.
2. **Heavy state in `Database.Stateful`** — hidden serialization costs.
3. **No `AsyncApexJob` monitoring or summary path** — support cannot see what happened.

## Official Sources Used

- Apex Developer Guide — Batch Apex lifecycle, behavior, and governor limits (concurrency, flex queue, 24-hour execution ceiling, QueryLocator 50M cap, scope size): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface.htm
- Apex Reference Guide — `Database.Batchable` interface (`start`/`execute`/`finish` signatures, QueryLocator vs Iterable return): https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_database_batchable.htm
- Apex Reference Guide — `Database.executeBatch` scope parameter
- Salesforce Well-Architected Overview — scalability, performance, and reliability framing
