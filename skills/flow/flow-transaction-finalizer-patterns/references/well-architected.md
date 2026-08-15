# Well-Architected Notes — Flow Transaction Finalizer Patterns

## Relevant Pillars

- **Reliability** — the failure this domain exists to prevent is asymmetric
  knowledge: the outside world believing something the database rolled back, or
  the database committing something the outside world was never told about. Every
  pattern here is a choice about which side of that asymmetry you can tolerate.
- **Operational Excellence** — post-commit work has no user watching it. Whether
  it ran, and what happened, has to be recorded deliberately. The finalizer is
  valuable precisely because it is the only mechanism that records the failure
  case without being asked.
- **Scalability** — moving external effects off the user's transaction is what
  keeps interactive saves fast. The asynchronous path also buys the higher async
  governor ceilings, which is a secondary benefit rather than the reason.

## Architectural Tradeoffs

- **Post-commit execution vs post-outcome execution:** three Flow-native
  mechanisms give the first; none gives the second. If the requirement is "record
  whether it worked and act on the answer," the boundary of Flow has been reached
  and the honest answer is Apex. Building more fault paths does not close the
  gap.
- **Run Asynchronously path vs Platform Event:** the async path is simpler, stays
  inside one flow, and keeps the failure local. An event decouples the consumers,
  so adding a fourth subscriber does not touch the publisher — at the cost of a
  definition to maintain, at-least-once delivery to defend against, and a
  subscriber whose failure is invisible from the publisher. Choose the event for
  the coupling, not for the durability.
- **Async path vs scheduled path:** the async path has no time and cannot be
  given one; the scheduled path computes a run time from a date/time field and
  fails in ways that have no analogue in the async case. Use the offset when the
  offset is real.
- **Idempotency at the guard vs at the provider:** a local "already processed"
  record is cheap and has a race between the check and the callout leaving; a
  provider-side idempotency key closes that race but only if the provider offers
  one. Both together is the design that actually holds.
- **Retry in Flow vs retry in a finalizer:** a flag-and-reschedule loop in Flow
  has no attempt counter and no give-up condition, so a systematic failure retries
  forever on the org's scheduled-flow allocation. A finalizer knows the outcome
  and stops at five. Re-implementing the second badly in the first is the
  strongest argument for crossing over.

## Hygiene

- No external effect anywhere before commit.
- Callouts live in the Run Asynchronously path, not the immediate path.
- Every post-commit effect has a deterministic idempotency key derived from the
  record, never from the interview GUID or the current timestamp.
- Every fault path records and stops; none of them compensates.
- Every finalizer-based retry has an explicit give-up branch below the
  five-attempt ceiling and writes a record when it gives up.
- Async paths that depend on current state re-read the record and handle
  not-found.
- Setup-object DML is split from non-setup DML by kind, not by timing.

## Related

- `flow/flow-transactional-boundaries` — what commits when, in detail.
- `flow/flow-and-platform-events` — the publish and subscribe mechanics.
- `flow/flow-platform-events-integration` — publish-after-commit semantics and
  idempotency design.
- `flow/flow-interview-debugging` — instrumenting work nobody is watching.
- `flow/flow-batch-processing-alternatives` — when the async ceilings are also
  not enough.
- `apex/apex-transaction-finalizers` — the Apex side in full.
- `standards/decision-trees/async-selection.md` — the formal choice. Cite the
  branch that resolved it rather than re-deriving the table.

## Template Gap

`templates/apex/` has no canonical `QueueableWithFinalizer` shape. The
illustrative snippet in `references/examples.md` is deliberately in the skill
rather than the template directory. If a second skill needs the same idiom,
promote it to `templates/apex/` rather than copying it again.

## Official Sources Used

- Transaction Finalizers — `System.Finalizer`, `System.attachFinalizer`, `FinalizerContext.getAsyncApexJobId/getRequestId/getResult/getException`, `ParentJobResult.SUCCESS` / `UNHANDLED_EXCEPTION`; one finalizer per Queueable; a failed Queueable can be re-enqueued five times; the finalizer may enqueue a single asynchronous job; callouts are allowed — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_finalizers.htm
- Connect a Record-Triggered Flow to an External System Using an Asynchronous Path — runs after the original transaction for the triggering record is successfully committed; enables callouts; available on after-save record-triggered flows; no configurable time; subject to asynchronous per-transaction Apex limits; monitored on the Time-Based Workflow page — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_asynchronous_path.htm&release=234&type=5
- Scheduled Paths — https://help.salesforce.com/s/articleView?id=platform.flow_concepts_trigger_scheduled_path.htm&type=5
- Record-Triggered Flow Considerations — https://help.salesforce.com/s/articleView?id=platform.flow_considerations_trigger_record.htm&type=5
- Publish Platform Event Messages Using Apex — Publish After Commit counts as a DML statement; Publish Immediately draws on a separate 150-call allocation — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_publish_apex.htm
- Custom Error Element — displays a message and rolls back the transaction in a record-triggered flow — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_custom_error.htm&type=5
- Per-Transaction Apex Governor Limits — 100 SOQL / 10,000 ms CPU / 6 MB heap synchronous against 200 / 60,000 ms / 12 MB asynchronous — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Well-Architected — Resilient — https://architect.salesforce.com/docs/architect/well-architected/resilient/resilient
