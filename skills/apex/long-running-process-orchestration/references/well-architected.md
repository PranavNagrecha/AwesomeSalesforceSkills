# Well-Architected Notes — Long-Running Process Orchestration

## Relevant Pillars

- **Reliability** — Multi-step processes that cross transaction boundaries create N failure points, one per step. Reliable orchestration requires explicit failure handling at each boundary (Finalizer), bounded retry with a maximum count, and a dead-letter or compensation path when retries are exhausted. Without Finalizer coverage, a step failure leaves process state ambiguous and potentially inconsistent.

- **Scalability** — Unbounded Queueable chains degrade org throughput because they consume queue capacity proportional to the number of in-flight process instances times the number of steps. Bounding chain depth with `MaximumQueueableStackDepth`, using Batch Apex for high-volume steps, and using Platform Events for decoupled fan-out keeps queue utilization predictable under load.

- **Operational Excellence** — A long-running process is operationally incomplete without observability. Each process instance must expose its current step, last error, retry count, and step timestamps on a queryable record so that operations teams can diagnose stuck instances, trigger manual recovery, and measure step latency over time.

- **Security** — State objects passed through Queueable constructors may carry record IDs or other sensitive data. These objects are serialized into the `AsyncApexJob.ExtendedStatus` context and potentially into Custom Object fields. Ensure that process instance records are access-controlled appropriately (sharing rules, field-level security) and that state payloads do not include sensitive field values that should not persist between transactions.

- **Performance** — Each step in a Queueable chain is queued individually. Under high concurrency, a long chain of small steps can starve other async jobs in the org. Design step boundaries at natural transaction commit points, not at every method call. Group multiple fast DML operations into a single step rather than splitting them across multiple Queueable jobs.

## Architectural Tradeoffs

**Queueable chain vs Platform Event state machine:** Queueable chains are simpler to implement and audit but are constrained by the single-child rule, stack depth limits, and the inability to pause for external events. Platform Event state machines require more infrastructure (Custom Object, event schema, trigger dispatch) but support external participants, arbitrary step timing, and easier fan-out. The hybrid pattern — chains within phases, events between phases — captures both benefits at the cost of additional design complexity.

**Checkpoint granularity vs DML volume:** Checking a Custom Object record at every step start and end provides the finest observability but adds 2 DML operations per step. For a 10-step process running on 1000 instances per hour, that is 20 000 additional DML rows per hour. Balance checkpoint frequency against DML governor exposure and storage.

**Retry at the step level vs retry at the process level:** Step-level retry (Finalizer re-enqueues the failed Queueable) is more precise but requires each step to be independently idempotent — re-running a step should be safe even if partial work was done. Process-level retry (restart from step 1) is simpler but may re-execute expensive or irreversible operations. Design for step-level idempotency wherever possible by using upsert with an external ID rather than unconditional insert.

## Anti-Patterns

1. **No process instance record — progress is invisible** — Running a multi-step orchestration without a Custom Object checkpoint record means operations teams have no way to see where an instance is, which step failed, or whether retries are occurring. This is an operational excellence failure that compounds over time as more process instances run concurrently. Every orchestration should have a trackable process instance record from the moment the process launches.

2. **Unbounded Queueable chains without depth cap** — Chaining Queueables without setting `MaximumQueueableStackDepth` leaves the process open to runaway execution if a termination condition bug allows the chain to continue past its intended end. In production orgs that run many concurrent business processes, a single runaway chain can degrade the org's async throughput for all other jobs.

3. **Publishing step-advance Platform Events inside a try block before DML completes** — As described in gotchas.md, a Platform Event published before DML commits is delivered even if the DML rolls back. This creates step-advance inconsistency where the state machine is ahead of the data. Step-advance events must be published after confirming all DML for that step succeeded.

4. **Relying on static variables for cross-step state** — Static class variables are reset between async transactions. A developer who stores process state in a static variable inside a Queueable class will find that the variable is null when the next chained Queueable runs. All state must travel through constructor parameters or be retrieved from a Custom Object record.

5. **Using `@future` methods for orchestration steps** — `@future` methods cannot chain to other `@future` methods, cannot attach Finalizers, have no retry mechanism, and cannot pass complex types. They are appropriate for fire-and-forget single operations but are architecturally unsuitable as steps in a multi-step process.

## Official Sources Used

- Apex Developer Guide — Queueable Apex: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
- Apex Developer Guide — Transaction Finalizers: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_finalizers.htm
- Apex Developer Guide — AsyncOptions Class: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_class_system_asyncoptions.htm
- Apex Developer Guide — Continuation Class (Async Callouts): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_continuation_overview.htm
- Platform Events Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
