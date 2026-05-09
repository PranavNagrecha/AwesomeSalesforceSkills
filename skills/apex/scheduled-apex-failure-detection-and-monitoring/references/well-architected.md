# Well-Architected Notes — Scheduled Apex Failure Detection And Monitoring

## Relevant Pillars

- **Reliability** — This is the primary pillar. Reliability requires the system to *know* when a critical async job has failed within a bounded time. Default platform behavior (uncaught exceptions in async go to debug log only, no email, no record) violates this directly. The skill's three layered mechanisms (in-job try-catch + log, `BatchApexErrorEvent` subscriber, `AsyncApexJob` watcher) are the reliability instrumentation that makes failures observable.
- **Operational Excellence** — Operational Excellence requires the team to be able to act on signals. A failure-detection design without a runbook reference, deduplication, and a clear notification channel produces noise and operator fatigue, which is the opposite of operational excellence. The skill's workflow step on "deduplicate by `AsyncApexJobId`" and "include a runbook link in every alert" is the operational-excellence half of the work.
- **Performance** — Indirect. A watcher schedule is itself code that runs every 15 minutes and consumes async governor budget. Designs should keep the watcher lean (Gotcha 7), but performance is not the dominant concern in this domain.
- **Scalability** — Indirect. As the org grows, `AsyncApexJob` query windows must stay narrow (use `CompletedDate >= :recent` and `LIMIT N`) so the watcher continues to run within governor limits.
- **Security** — Notifications carrying stack traces or record IDs must consider data exposure. If alerts route to Slack via a Platform Event bridge, the bridge endpoint requires named credentials and the message body should not embed PII from failing records. Generally, surface IDs and class names, not record contents.

## Architectural Tradeoffs

- **In-job try-catch vs let-it-throw.** Catching the exception and logging gives durable, structured failure records but moves the `AsyncApexJob.Status` from `Failed` to `Completed`, which can mask the problem from anyone reading Setup → Apex Jobs. Letting the exception propagate marks the job `Failed` (and triggers `BatchApexErrorEvent` for batches with `RaisesPlatformEvents`) but loses the full context unless the platform happens to capture it. The recommended compromise is catch → log → re-throw, which gives you both.
- **`BatchApexErrorEvent` subscriber vs `AsyncApexJob` watcher.** The event subscriber is push-based, low-latency, and free in terms of governor budget. The watcher is pull-based, has detection latency equal to the schedule frequency, and consumes a Schedulable slot. The event covers Batch only; the watcher covers everything. They are complementary, not alternatives — ship both.
- **Custom Notification (bell) vs email vs Platform Event for alerting.** Custom Notifications are durable until cleared and don't depend on email deliverability — but they're invisible to anyone outside Salesforce. Email is universal but easy to miss in a busy inbox. A Platform Event subscribed by an external bridge (Slack, Pagerduty) is the most reliable for ops teams, but introduces a second delivery hop that itself can fail. Critical jobs should layer at least two of the three.

## Anti-Patterns

1. **Setup → Apex Jobs as the monitoring channel.** The page is a forensics tool, not a monitor. It has no alerting, no historical depth beyond a short rolling window, and no signal for "schedule fired but enqueue failed". Treat any architecture document that says "ops checks Apex Jobs daily" as a reliability gap to close.

2. **Relying on `Status = 'Failed'` alone.** Misses Batch executions that complete with `NumberOfErrors > 0` (Gotcha 3), misses jobs that never enqueued (Gotcha 4), misses stuck `Queued`/`Holding` jobs. Watcher SOQL must explicitly cover all four states.

3. **Subscribing to `BatchApexErrorEvent` without idempotency.** Platform events deliver at-least-once. A subscriber that sends an email on every event without deduplicating by `AsyncApexJobId` will page operators multiple times for the same failure (Gotcha 6). Idempotency is non-optional.

4. **Putting the watcher logic inside the same class it watches.** A self-watching scheduled job dies when its host class throws — the body that was supposed to detect the failure is the body that crashed. The watcher must be a *separate* Schedulable, scheduled independently.

## Official Sources Used

- Apex Developer Guide — `BatchApexErrorEvent`: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface_BatchApexErrorEvent.htm
- Apex Developer Guide — `Database.RaisesPlatformEvents` interface: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_async_async_database_raises_platform_events.htm
- Apex Reference Guide — `AsyncApexJob` class: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_async_async_apex_job.htm
- SOAP API Object Reference — `AsyncApexJob` standard object: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_asyncapexjob.htm
- Salesforce Well-Architected — Reliability and Operational Excellence pillars: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
