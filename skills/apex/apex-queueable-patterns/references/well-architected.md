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

Each bullet names the claim it supports. Line numbers are into the plain-text
extractions of the Summer '26 (v67.0) PDFs used while authoring this package.

- **Apex Developer Guide v67.0 — Queueable Apex** (`apexdev` L15951-16214) —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm —
  supports: the job Id returned by `enqueueJob` is an `AsyncApexJob` Id
  (L15965-15967); non-primitive member variables are permitted (L15968-15970);
  `transient` members are nulled by serialization (L15975-15976); a rolled-back
  enqueuing transaction never processes the job (L15961); batch counters are
  always zero for Queueable (L16012-16013); 50 enqueues per synchronous
  transaction and 1 per asynchronous transaction (L16179-16181); no depth limit
  outside Developer and Trial editions, where the maximum stack depth is 5
  (L16182-16185); one child per parent (L16186-16188); `Database.AllowsCallouts`
  enables callouts including in chained jobs (L16164-16165); `Test.startTest` /
  `Test.stopTest` runs the job synchronously (L16123-16126).
- **Apex Developer Guide v67.0 — Detecting Duplicate Queueable Jobs**
  (`apexdev` L16215-16277) —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dedupe_queueable.htm —
  supports: `QueueableDuplicateSignature.Builder` with `addString` / `addId` /
  `addInteger` and `build()` (L16219-16226); the byte-size accessors
  `getSize` / `getRemainingSize` / `getMaxSize` (L16228-16232); the signature is
  released when the job is **dequeued**, not when it completes, so duplicates of
  a running job can still occur (L16250-16254); `DuplicateMessageException` is
  thrown, with the message text (L16253, L16262-16264).
- **Apex Developer Guide v67.0 — Transaction Finalizers**
  (`apexdev` L16278-16437) —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_finalizers.htm —
  supports: five consecutive re-enqueues by a finalizer, counter reset on a clean
  completion (L16291-16294); Queueable and Finalizer run in separate Apex and
  database transactions (L16296-16297); synchronous governor limits apply to the
  Finalizer except heap, `enqueueJob` count and `@future` count (L16297-16303);
  the four `FinalizerContext` methods (L16311-16344); one finalizer per job and
  one async job enqueued from it (L16353-16356); callouts allowed in a finalizer
  (L16356); the finalizer can fail to execute on unexpected termination
  (L16428-16430).
- **Apex Developer Guide v67.0 — Execution Governors and Limits**
  (`apexdev` L19528-19580, L17691-17700) —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm —
  supports: asynchronous SOQL 200 vs synchronous 100 (L19546); DML 150 both
  (L19553); heap 6 MB vs 12 MB and CPU 10,000 ms vs 60,000 ms (L19576-19578);
  `enqueueJob` 50 / 1 (L19573); `@future` allowance of 50 in a queueable context
  and 0 in batch and future contexts (L19568-19572); the 250,000-or-licences×200
  rolling 24-hour asynchronous cap shared by all async Apex (L17693-17700).
- **Apex Developer Guide v67.0 — Callout limits, `@IsTest(IsParallel=true)`,
  sharing versioned behaviour, static variable scope**
  (`apexdev` L35855-35866, L5957-5966, L4959-4967, L3738-3740) —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_limits.htm —
  supports: no callout after DML or other pending operations in the same
  transaction (L35860-35862); parallel tests cannot call `System.enqueueJob`
  (L5965); classes without an explicit sharing declaration run `with sharing`
  from API 67.0 and `without sharing` at 66.0 and earlier for an entry point
  (L4961-4967); a static variable is scoped to one transaction and reset across
  transaction boundaries (L3738-3740).
- **Apex Reference Guide v67.0 — `System.AsyncOptions`, `System.AsyncInfo`,
  `QueueableDuplicateSignature.Builder`, `System.enqueueJob`, `System.abortJob`,
  `Limits`, `QueueableContext`** (`apexrefguide` L201087-201225, L227230-227560,
  L238919-239030, L238661-238690, L220873-220895, L214950) —
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_AsyncOptions.htm —
  supports: the three `AsyncOptions` properties and their types (L201190-201222);
  the four `AsyncInfo` methods (L201087-201150); the three `enqueueJob` overloads
  and the 0-10 minute delay range ignored during testing (L238919-239030);
  `abortJob` stops a job but in-progress code runs to completion
  (L238661-238665); `Limits.getQueueableJobs` and `getLimitQueueableJobs`
  (L220873-220895); the `DuplicateMessageException` message text (L214950);
  `QueueableContext.getJobId()` is the only method on that interface
  (L227365-227392).
- **Object Reference for Salesforce v67.0 — `AsyncApexJob`**
  (`object_reference` L42262-42440) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf —
  supports: `JobType` picklist values including `Queueable` (L42360-42371);
  `Status` values and the footnote that `Holding` applies to batch jobs in the
  Apex flex queue (L42419-42429); `ExtendedStatus` carries the first error
  (L42305-42311); View Setup and Configuration is required to access the object
  and to enqueue asynchronous Apex outside system mode (L42269-42271).
- **Metadata API Developer Guide v67.0 — `ApexSettings`**
  (`api_meta` L110713-110726) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf —
  supports: `DefaultQueueableDelay`, the admin-controlled org-wide minimum delay
  in seconds, minimum 1 and maximum 600, applied only to jobs enqueued without an
  explicit delay parameter.
- **`standards/decision-trees/async-selection.md`** — Q1 (volume and duration),
  Q5 (state between invocations) and Q7 (work that must resume after failure) —
  supports the routing statement that this skill assumes Queueable has already
  been chosen; the choice itself belongs to `apex/async-apex`.
- **Salesforce Well-Architected — Overview**:
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html —
  supports the Reliability / Scalability / Performance framing at the top of this
  file.
