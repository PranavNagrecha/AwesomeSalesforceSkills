# Well-Architected Notes — Apex Queueable Patterns

## Relevant Pillars

### Reliability

Reliability is the primary pillar for this skill. Queueable chains that lack Finalizer-based error handling leave no guaranteed cleanup path when jobs fail. A production Queueable that performs side effects — callouts, DML, Platform Events — without a Finalizer cannot guarantee compensating action or failure notification. The Finalizer interface is the platform-provided mechanism for reliable failure handling in async Apex, and its absence is a reliability gap. Tag findings as Reliability when:

- Queueables perform irreversible operations without a Finalizer attached.
- Retry logic exists only in `catch` blocks inside `execute()` and not in the Finalizer.
- Failure records, notifications, or compensating transactions are entirely absent.

### Scalability

Scalability concerns arise when Queueable chains are unbounded. An infinite or uncapped chain degrades the org's async job queue, delays other jobs, and can trigger platform-level throttling. The `AsyncOptions.MaximumQueueableStackDepth` API and the `System.AsyncInfo.getCurrentQueueableStackDepth()` check are the canonical scalability controls for chained Queueables. Tag findings as Scalability when:

- Chains have no depth cap.
- Fan-out logic inside `execute()` tries to enqueue multiple children (violates the single-child rule and limits throughput design options).
- Queueable is used where Batch Apex is the more appropriate scaled tool.

### Performance

Performance is secondary but relevant for state passing. Passing large SObject collections through Queueable constructor fields increases serialization overhead and heap pressure. Prefer ID sets with re-query in the next job. Tag findings as Performance when:

- Large collections are serialized across chain links unnecessarily.
- The Finalizer is performing heavy computation that should be deferred to another Queueable.

---

## Architectural Tradeoffs

**Queueable vs. Batch Apex for sequential processing:** Queueable chaining gives finer control per step and lower framework overhead for small workloads. Batch Apex gives fresh governor limits per scope and query locator support for very large data volumes. The crossover point is approximately 10 000+ records or scenarios where each processing unit needs guaranteed limit headroom regardless of prior steps.

**Finalizer vs. `try/catch` for error handling:** `try/catch` handles caught exceptions from within the same transaction. The Finalizer handles all failure modes — caught, uncaught, and platform-initiated termination — in a separate transaction. For production-grade Queueables, both are appropriate; they serve different failure modes.

**Inline retry vs. Finalizer retry:** Retrying within `execute()` by re-enqueueing from a `catch` block fails if the original exception causes transaction rollback before the re-enqueue. The Finalizer retry pattern enqueues the retry after the parent transaction has ended, making it unconditionally safe.

---

## Anti-Patterns

1. **Unbounded chaining without depth control** — A Queueable that always re-enqueues itself without a termination guard or depth cap is a production reliability risk. It saturates the async queue, delays other jobs, and is hard to stop without deploying a kill-switch class. Use `AsyncOptions.MaximumQueueableStackDepth` and check depth before chaining.

2. **Relying on `catch` alone for async error recovery** — Wrapping `execute()` body in a large `try/catch` and writing failure logic there does not handle platform-termination scenarios (out of CPU, heap exceeded, system limits). The Finalizer interface exists specifically for this gap. Any Queueable with significant side effects should use both.

3. **Passing SObject graphs through constructor state** — Serializing full SObject records with all populated fields across chain links increases heap usage in every job in the chain and causes deserialization errors if field sets change between deployments. Pass IDs only and re-query at the start of each `execute()`.

---

## Official Sources Used

- Apex Developer Guide — Queueable Apex: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
- Apex Developer Guide — Transaction Finalizers: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_finalizers.htm
- Apex Reference Guide — AsyncInfo Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_AsyncInfo.htm
- Apex Developer Guide — Execution Governors and Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
