# Well-Architected Notes — Apex Transaction Finalizers

## Relevant Pillars

- **Reliability** — Transaction Finalizers are a direct reliability mechanism. They guarantee that compensation logic (retry, failure logging, lock release) executes even when the primary Queueable transaction fails catastrophically. This maps to the Well-Architected reliability principle of designing for failure: async operations should have a defined recovery path, not just a hope that they succeed.

- **Operational Excellence** — Logging failures to a queryable custom object (rather than relying on transient `ApexLog` debug entries) supports observability, SLA reporting, and manual reprocessing workflows. Finalizers enable operations teams to see async failures without requiring admin access to debug logs.

- **Performance** — Finalizers run in a separate Apex transaction with fresh governor limits. They do not extend or slow the parent Queueable's transaction. However, they do consume an additional async slot and contribute to the org's concurrent Queueable job count. On high-volume orgs, design the Finalizer to be lightweight and exit quickly on SUCCESS paths.

## Architectural Tradeoffs

**Retry in Finalizer vs. retry via polling job:**
A Finalizer-driven retry is immediate and self-contained but adds job-chain depth. A polling Schedulable that finds failed `AsyncApexJob` records and re-enqueues them is more operationally visible but introduces latency. For SLA-sensitive integrations, Finalizer retry is preferred. For non-urgent batch corrections, polling is simpler to operate.

**DML logging in Finalizer vs. Platform Event:**
DML inside the Finalizer is synchronous, durable, and simple — but it adds a DML statement to the Finalizer's budget and can fail if validation rules or triggers reject the error record. Publishing a Platform Event avoids DML failure risk but adds latency and requires a subscriber. For most cases, direct DML with a `try/catch` fallback is the right tradeoff.

**Combining retry and logging in one Finalizer:**
Because only one `System.enqueueJob()` is allowed, if you need both async retry and async logging you must combine them into a single Queueable and use the one enqueue slot for that combined job. Alternatively, do synchronous DML logging inside the Finalizer and use the enqueue slot for retry only.

## Anti-Patterns

1. **No retry ceiling** — Attaching a Finalizer that unconditionally re-enqueues the parent on failure creates an infinite retry loop that consumes Queueable flex queue slots indefinitely. Always pass and check a retry counter; enforce a `MAX_RETRIES` constant.

2. **Relying on `System.debug` for failure visibility** — Debug logs are transient, size-limited, and require admin access to retrieve. A Finalizer that only calls `System.debug` on failure provides no durable operational signal. Write to a custom object or publish a Platform Event for production observability.

3. **Attaching the Finalizer late in `execute()`** — If `System.attachFinalizer()` is called after code that might throw, the Finalizer may never be registered. Always call `attachFinalizer` as the first statement in `execute()`, before any business logic.

## Official Sources Used

- Apex Developer Guide — Transaction Finalizers: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_finalizers.htm
- Apex Developer Guide — Queueable Apex: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
