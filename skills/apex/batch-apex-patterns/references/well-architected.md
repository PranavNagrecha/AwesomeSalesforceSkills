# Well-Architected Notes — Batch Apex Patterns

## Relevant Pillars

### Scalability

Batch Apex is a scale-oriented tool for workloads that exceed a normal transaction.

Tag findings as Scalability when:
- a very large dataset must be processed safely
- direct list loading is used where QueryLocator would be safer
- a smaller async mechanism is being stretched beyond its intended volume

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

- Apex Developer Guide — Batch Apex lifecycle and behavior
- Apex Reference Guide — `Database.Batchable` and `Database.executeBatch`
- Salesforce Well-Architected Overview — scalability, performance, and reliability framing
