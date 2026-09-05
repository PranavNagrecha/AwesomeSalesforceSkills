# Well-Architected Notes — Apex Transaction Finalizers

## Relevant Pillars

- **Reliability** — Transaction Finalizers are a direct reliability mechanism. They give an async operation a defined recovery path instead of a hope that it succeeds. The platform's own framing is a list of what you had before them: "Poll the status of AsyncApexJob using a SOQL query and re-enqueue the job if it fails" and "Fire BatchApexErrorEvents when a batch Apex method encounters an unhandled exception" (Apex Developer Guide v67.0 L16288-16290). A Finalizer replaces the poll with a callback.

- **Operational Excellence** — Logging failures to a queryable object rather than to a transient debug log supports observability, SLA reporting, and manual reprocessing. The Finalizer's own failures, by contrast, surface only as `Error processing finalizer for queueable job id: {0}` in the log (guide L16578-16587), so the monitoring design must alert on the *absence* of a dead-letter row for a failed `AsyncApexJob`, not just on its presence.

- **Performance** — The Finalizer runs in its own Apex and Database transaction (guide L16297) and does not extend the parent Queueable. It also does not cost a daily async execution: "Using a finalizer doesn't count as an extra execution against your daily Async Apex limit" (guide L16298). The retry it enqueues does. Budget the Finalizer as a synchronous unit of work — "Synchronous governor limits apply for the Finalizer transaction" except for heap, `System.enqueueJob` count, and `@future` count (guide L16298-16303).

## Architectural Tradeoffs

**Finalizer retry vs. polling job.** A Finalizer-driven retry is immediate and self-contained but capped: five consecutive re-enqueues, with the counter reset by any success (guide L16293-16295). A Schedulable that scans `AsyncApexJob` for failures is slower and more operationally visible, and has no such cap. Use the Finalizer for SLA-sensitive integrations, the poller for anything that must survive an outage longer than five attempts, and both when the failure mode is unknown — the poller then only ever picks up what the Finalizer's ceiling handed off.

**One class or two.** Fusing `Queueable` and `Finalizer` into one class is explicitly supported (guide L16296) and is the only practical way to buffer log lines produced *during* the job, because the framework snapshots the Finalizer instance at the end of Queueable execution (guide L16358-16359). The cost is two `execute` overloads in one file and both `getJobId()` and `getAsyncApexJobId()` in scope. Two classes are safer to review; one class is the only option when the payload is produced by the work itself.

**DML logging in the Finalizer vs. Platform Event.** Direct DML is durable and simple, but a validation rule or a trigger on the error object can reject it, and there is no second Finalizer to catch that. `Database.insert(records, false)` — the form the guide's own logging example uses (guide L16435) — degrades to partial success instead of losing the whole trail. A Platform Event avoids the DML failure mode but needs a subscriber and does not give you a row to report on. UNVERIFIED (2026-09-05): the guide does not state how `EventBus.publish` counts against the Finalizer transaction's DML budget.

**Callout from the Finalizer vs. chaining a Queueable.** "Callouts are allowed in finalizer implementations" (guide L16357), and the guide gives the split as an example of the transaction boundary: "the Queueable can include DML, and the Finalizer can include REST callouts" (guide L16297-16298). Notifying a dead-letter endpoint directly from the Finalizer therefore leaves the single enqueue slot free for the retry — a materially better allocation than spending the slot on a notification Queueable.

**Managed-package considerations.** "We urge ISVs to exercise caution in using global Finalizers with state-mutating methods in packages. If a subscriber org's implementation invokes such methods in the global Finalizer, it can result in unexpected behavior" (guide L16538-16540). If the Finalizer ships in a managed package, keep the state-mutating surface (`addLog`, `note`) `public` to the package rather than `global`, or accept that subscriber code can rewrite what the Finalizer commits.

## Anti-Patterns

1. **Retry ceiling at or above the platform's.** A `MAX_RETRIES` of 5 or more never fires its own dead-letter branch: the platform fails the enqueue on the fifth consecutive failure first (guide L16293-16295, L16523). Set the ceiling to 3 or 4 so the failure record is written by code you control.

2. **Relying on `System.debug` for failure visibility.** Debug logs are transient, size-limited, and admin-gated. Write to a custom object — via `templates/apex/ApplicationLogger.cls` where the project already has it — or publish a Platform Event.

3. **Attaching the Finalizer late in `execute()`.** Anything that throws before `System.attachFinalizer` runs is uncovered, because attachment happens at runtime, not at compile time. Make it the first statement.

4. **Treating the Finalizer as a `finally` block.** It is not in the parent's transaction: the parent's DML is rolled back and unqueryable (guide L16297), while the Finalizer object's own fields do survive (guide L16358-16359). Code written on either half of that split alone is wrong.

5. **Using a Finalizer where a `try/catch` belongs.** A recoverable `DmlException` handled inline costs nothing; routing it through a Finalizer spends the single enqueue slot and a transaction to do what one `catch` would have done. Reserve the Finalizer for what `catch` cannot reach — `LimitException` and other uncatchable terminations.

6. **Marking Finalizer state `transient`.** The field is silently empty when `execute(FinalizerContext)` runs (guide L16360-16362), so the compensation logs nothing and looks like it worked.

## Official Sources Used

- Apex Developer Guide v67.0, Summer '26 — "Transaction Finalizers", L16284-16303 (separate Apex and Database transactions; no extra daily async execution; synchronous governor limits except heap / `enqueueJob` count / `@future` count; five consecutive re-enqueues with reset-on-success): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide v67.0 — "System.FinalizerContext Interface" and "Implementation Details", L16316-16363 (the four context methods; one finalizer per job; one async job enqueued per finalizer; callouts allowed; state mutation after attach supported; `transient` fields dropped)
- Apex Developer Guide v67.0 — "Logging Finalizer Example" and "Retry Queueable Example", L16364-16530 (the fused `Queueable, Finalizer` class shape; `System.attachFinalizer(this)`; `Database.insert(logRecords, false)`; the five-retry chaining-limit comment)
- Apex Developer Guide v67.0 — "Considerations", "Best Practices" and "Transaction Finalizers Error Messages", L16532-16587 (unexpected termination can skip the finalizer; ISV caution on global state-mutating finalizers; the exact attach-error and runtime-error strings)
- Apex Reference Guide v67.0 — "Finalizer Interface" L215544-215600 and "FinalizerContext Interface" L215610-215691 (method signatures: `public void execute(System.FinalizerContext)`, `public Id getAsyncApexJobId()`, `public String getRequestId()`, `public System.ParentJobResult getResult()`, `public Exception getException()`) — Apex Reference Guide, Version 67.0, Summer '26; UNVERIFIED (2026-09-05): the PDF filename under resources.docs.salesforce.com for this guide was not confirmed, so no URL is asserted here
- Apex Reference Guide v67.0 — "ParentJobResult Enum" L227217-227226 and `System.attachFinalizer` L238799-238812 (enum values SUCCESS / UNHANDLED_EXCEPTION; `public static void attachFinalizer(Object finalizer)` — an `Object` parameter, so a wrong type fails at runtime)
- Apex Developer Guide v67.0 — "Queueable Apex Limits" L16176-16195 and "Testing Queueable Jobs" L16121-16146 (50 `enqueueJob` calls per synchronous transaction, one per async transaction; `Test.startTest`/`Test.stopTest` runs queued async work synchronously)
- Apex Developer Guide v67.0 — "Versioned Behavior Changes" for sharing, L4870-4874 and L4961 (API v67.0+ classes without an explicit sharing declaration run `with sharing`; the guide still recommends declaring it explicitly)
- Salesforce Well-Architected — Resilient / Automated: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (framing for "design for failure" and for the retry-vs-poll tradeoff above)
