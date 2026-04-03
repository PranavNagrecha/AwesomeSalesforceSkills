# Well-Architected Notes — Async Apex

## Relevant Pillars

### Scalability

Async Apex is often the mechanism that makes a design scale past a single transaction. Queueable, Batch, and scheduled dispatch patterns help distribute work into governor-safe units.

Tag findings as Scalability when:
- the workload can exceed synchronous governor limits
- a trigger or controller tries to process too much in one transaction
- a team chooses Batch because of record volume, not habit

### Performance

Performance improves when heavy work moves out of the user transaction and into background processing with the right chunk size or queue depth.

Tag findings as Performance when:
- the user is waiting on work that should happen after commit
- batch scope size is mismatched to the actual API or DML load
- a scheduler is doing heavy work inline instead of dispatching a worker

### Reliability

Async work fails differently from synchronous work. Monitoring, retries, and partial-success design decide whether failures are actionable or silent.

Tag findings as Reliability when:
- a Queueable or Batch has no durable error reporting
- async fan-out creates unpredictable job counts
- partial success is needed but the async worker still uses all-or-none behavior

## Architectural Tradeoffs

- **Queueable vs Batch:** Queueable is simpler and better for application-level async work; Batch is better when volume or fresh limits per scope are the actual need.
- **Legacy future vs modernization:** `@future` is still valid for narrow cases, but modern designs usually benefit from Queueable visibility and composition.
- **Schedule worker vs schedule dispatcher:** Inline schedulers look simple initially and become expensive operationally later.

## Anti-Patterns

1. **Enqueueing jobs in a loop** — operationally noisy and often limit-prone.
2. **Using Batch for small transactional after-save work** — too much framework overhead for a Queueable problem.
3. **Treating `@future` as the default async primitive** — loses monitoring, state flexibility, and cleaner composition.

## Official Sources Used

- Apex Developer Guide — async Apex behavior and scheduling guidance
- Apex Reference Guide — `Queueable`, `Database.Batchable`, and related API reference
- Salesforce Well-Architected Overview — scalability, performance, and reliability framing
