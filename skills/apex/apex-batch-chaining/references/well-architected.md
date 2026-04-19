# Well-Architected Notes — Apex Batch Chaining

## Relevant Pillars

- **Reliability** — Chains that do not guard against Flex Queue saturation silently drop work, causing data inconsistency and pipeline failures that are difficult to diagnose. A reliable chain validates queue depth before every enqueue call and has a visible abort path when capacity is unavailable.
- **Performance Efficiency** — Batch job scope size directly affects how long each step occupies one of the 5 concurrent execution slots. A chain of many small-scope jobs can starve other org processes. Each step should process the largest scope that fits comfortably within governor limits to minimize total elapsed time.
- **Operational Excellence** — Chained pipelines without job-ID capture and status monitoring are operationally blind. Every chain step should log the returned `AsyncApexJob` Id and downstream error counts so that on-call teams can diagnose mid-chain failures without manual queue inspection.

## Architectural Tradeoffs

**Simplicity vs. Maintainability:**
A direct `finish()` chain (Job A calls `Database.executeBatch(new JobB())`) is the simplest possible implementation. It has no extra classes and is easy to understand. The cost is that routing logic is scattered across every `finish()` method — adding a step or changing order requires editing multiple classes. The Queueable coordinator pattern costs one extra class but centralizes all routing.

**Batch Chunking vs. Queueable Flexibility:**
Batch Apex provides automatic record chunking, retry on scope failure, and governor limit isolation per chunk. Queueable provides none of these — it runs a single execution context. Use Batch for steps that process large record sets; use Queueable only as a coordinator or for lightweight orchestration logic between batch steps.

**Synchronous State vs. Persisted State:**
Passing state via constructor parameters is clean and synchronous but limited to serializable primitive and SObject types. For complex state (e.g., maps of error counts by record type), persist to a staging SObject or Custom Setting and query it in the next step's `start()`. This adds a DML write/read pair but is more resilient to governor limits on object graph serialization.

## Anti-Patterns

1. **Blind enqueue in finish()** — Calling `Database.executeBatch` without checking Flex Queue depth. Reliable architectures always gate enqueue on a capacity check. Without this guard, the chain silently drops work under load.
2. **Testing the full chain in one test method** — Treating `Test.stopTest()` as an end-to-end chain runner. This leads to false-green tests that never actually cover downstream job logic. Each chain link must have its own isolated test.
3. **Using System.scheduleBatch() for immediacy** — Scheduling a batch with a 1-minute delay inside `finish()` instead of calling `Database.executeBatch`. This introduces unnecessary latency, creates CronTrigger entries, and can conflict with scheduled job limits (max 100 scheduled jobs per org).
4. **No terminal condition on recursive chains** — A chain that re-enqueues itself without a clear exit condition will saturate the Flex Queue and degrade org performance for all batch consumers.

## Official Sources Used

- Using Batch Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface.htm
- Queueable Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
- FlexQueue Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_FlexQueue.htm
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
