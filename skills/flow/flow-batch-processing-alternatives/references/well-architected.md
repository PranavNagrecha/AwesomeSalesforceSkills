# Well-Architected Notes — Flow Batch Alternatives

## Relevant Pillars

- **Scalability** — the load-bearing decision is not "Flow or Apex" but where the
  transaction boundary sits. `per-interview cost × batch size` against the
  per-transaction limit is the whole scaling model; both engines obey it and
  neither escapes it.
- **Reliability** — partial-failure handling is the largest gap in Flow-only
  jobs. Flow has no finalizer and the next scheduled run is not a retry, so
  anything that must be known to have completed needs either an explicit
  chunk-level log or Apex.
- **Operational Excellence** — a long-running job with no progress signal, no off
  switch, and no per-chunk log is unmaintainable regardless of which engine runs
  it. Those three artifacts are the deliverable, not the flow.

## Architectural Tradeoffs

- **Lower batch size vs bulkify:** lowering the batch size buys governor headroom
  at a proportional cost in throughput and transaction overhead. It is correct
  when per-interview work is irreducible (a callout, a per-record invocable, an
  expensive formula) and a waste when the cost is a query that could have been
  hoisted. Diagnose which before reaching for the lever.
- **Platform Event fan-out vs serial scheduled runs:** fan-out buys independent
  failure domains and per-chunk retry; serial runs are far simpler to reason
  about and to monitor. Choose fan-out for the failure isolation, not for speed —
  and remember the subscriber needs bulkifying too.
- **Checkpoint control record vs Start-element batch size:** the control record
  gives an off switch, a progress counter, and a resume point that the platform
  does not provide; the batch size field gives governor headroom with no moving
  parts. Recurring work wants the field. A one-shot backfill wants the record.
- **Flow with an Invocable Apex splitter vs full Apex:** keeping the orchestration
  in Flow preserves admin ownership and a readable, disableable surface; moving
  everything to Apex gets finalizers and `QueryLocator` streaming. The hybrid —
  scheduled flow as the trigger, invocable action as the entry point — usually
  beats either extreme.
- **Fewer long jobs vs more short jobs:** the org allows 5 concurrent batch jobs
  with 100 more Holding, so parallelism is capped. Sizing the transaction via
  `executeBatch` scope is the available lever; splitting into more jobs mostly
  moves work into the flex queue.

## Hygiene

- Every high-volume flow's analysis states `per-interview cost × batch size`
  explicitly.
- The org's scheduled flows are inventoried against the shared daily interview
  ceiling before another is added.
- The processed flag is set after the work succeeds, never before.
- Every chunk writes a log row: chunk id, count, outcome, timestamp.
- There is an off switch that does not require deactivating the flow.
- Setup-object DML is isolated from non-setup DML in a separate transaction.
- Batch size changes are accompanied by a runtime-version check.
- The escalation to Apex names a capability, not a record count.

## Related

- `flow/flow-bulkification` — hoisting queries and DML out of the per-record path,
  which is the fix that batch sizing is often a substitute for.
- `flow/flow-and-platform-events` — the fan-out mechanics and the subscriber's own
  200-message batch.
- `flow/flow-large-data-volume-patterns` — LDV query and index behaviour.
- `flow/flow-record-locking-and-contention` — what spreading a job across business
  hours costs.
- `apex/apex-transaction-finalizers` — the retry semantics Flow does not have.
- `standards/decision-trees/async-selection.md` — the formal choice between
  `@future`, Queueable, Batch, Schedulable, Platform Events, and Scheduled Flow.
  Cite the branch that resolved the decision rather than re-deriving it.

## Official Sources Used

- Per-Transaction Apex Governor Limits — 100 SOQL synchronous / 200 asynchronous, 50,000 query rows, 150 DML statements, 10,000 DML rows, 10,000 ms / 60,000 ms CPU, 6 MB / 12 MB heap — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Using Batch Apex — up to 5 batch jobs queued or active concurrently, up to 100 Holding in the flex queue; scope default 200 and maximum 2,000 for a QueryLocator; 250,000 batch method executions per 24 hours or user licenses × 200, whichever is greater; `Database.Stateful` retains instance but not static member variables; start/execute/finish can each make up to 100 callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface.htm
- Transaction Finalizers — `System.Finalizer`, `System.attachFinalizer`, `ParentJobResult.SUCCESS` / `UNHANDLED_EXCEPTION`, five successive re-enqueues of a failed Queueable — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_finalizers.htm
- Improve Performance with Batching for Scheduled Flows (Summer '26) — batch size settable from 1 to 200 on the Start element; requires runtime version 63.0 or later; previous behaviour was a default batch of 200 — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_scheduled_flow_batching.htm&release=262&type=5
- Schedule-Triggered Flow Considerations — 250,000 schedule-triggered flow interviews per 24 hours, or user licenses × 200, whichever is greater — https://help.salesforce.com/s/articleView?id=platform.flow_considerations_trigger_schedule.htm&type=5
- Platform Event Allocations — publishing 250,000/hour (Enterprise, Performance, Unlimited) and 50,000/hour (Developer); the delivery allocation does not apply to Apex triggers, flows, or Process Builder — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
- Platform Events Maximum Batch Size Is 200 (flow subscribers) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_mgmt_platform_events_max_batch_size.htm&release=234&type=5
- Salesforce Well-Architected — Resilient — https://architect.salesforce.com/docs/architect/well-architected/resilient/resilient
