# LLM Anti-Patterns — Scheduled Apex Failure Detection And Monitoring

Common mistakes AI coding assistants make when generating or advising on Scheduled Apex failure detection and monitoring. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Asserting that uncaught async exceptions email the user

**What the LLM generates:** "If the batch fails, Salesforce will email the user who scheduled it." Accompanied by no instrumentation in the generated batch class — just a `Database.Batchable` body that may throw freely.

**Why it happens:** Synchronous Apex *does* email the user and Setup → Apex Exception Email recipients on uncaught exceptions. The model conflates the two paths because the Apex Developer Guide treats them in adjacent sections.

**Correct pattern:**

```apex
// Async Apex does NOT auto-email on uncaught exception. Either:
// (a) catch + log + (optionally) re-throw, or
// (b) implement Database.RaisesPlatformEvents and subscribe to BatchApexErrorEvent.
public class NightlyJob implements Database.Batchable<SObject>,
                                   Database.RaisesPlatformEvents {
    // ...
}
```

**Detection hint:** Search generated Apex for `Database.Batchable` or `Schedulable` classes that have neither try-catch in `execute()`, nor `Database.RaisesPlatformEvents`, nor an accompanying watcher. Also flag any text claiming "Salesforce will email on async failure".

---

## Anti-Pattern 2: Generating a batch class that catches and swallows in `execute()` with no log

**What the LLM generates:**

```apex
public void execute(Database.BatchableContext bc, List<Account> scope) {
    try {
        // work
    } catch (Exception e) {
        System.debug(e);  // <— invisible after debug logs roll
    }
}
```

**Why it happens:** Pattern-matching on "always catch exceptions in async" without remembering that `System.debug` is not a durable log. Debug logs roll off, are gated by trace flags, and do not reach operators.

**Correct pattern:**

```apex
public void execute(Database.BatchableContext bc, List<Account> scope) {
    try {
        // work
    } catch (Exception e) {
        ApplicationLogger.error(
            'NightlyJob.execute',
            e.getTypeName() + ': ' + e.getMessage(),
            e.getStackTraceString()
        );
        throw e;  // re-throw so AsyncApexJob.Status='Failed' and BatchApexErrorEvent fires
    }
}
```

**Detection hint:** Regex `catch\s*\([^)]*\)\s*\{\s*System\.debug` inside any class implementing `Schedulable` or `Database.Batchable`.

---

## Anti-Pattern 3: Implementing `Database.RaisesPlatformEvents` on a Queueable or Schedulable

**What the LLM generates:**

```apex
public class MyQueueable implements Queueable, Database.RaisesPlatformEvents {
    public void execute(QueueableContext qc) { /* ... */ }
}
```

The user is told "now Salesforce will publish a platform event on failure."

**Why it happens:** The model knows the marker interface exists for async failure reporting and applies it uniformly across async types without checking that the platform only honors it for Batch.

**Correct pattern:**

```apex
// Database.RaisesPlatformEvents is BATCH ONLY. For Queueable, use try-catch + log.
public class MyQueueable implements Queueable {
    public void execute(QueueableContext qc) {
        try {
            // ...
        } catch (Exception e) {
            ApplicationLogger.error('MyQueueable', e.getMessage(), e.getStackTraceString());
            // Optionally re-throw to mark AsyncApexJob.Status='Failed'.
        }
    }
}
```

**Detection hint:** Grep for `Database\.RaisesPlatformEvents` in any class that does not also `implements Database.Batchable`.

---

## Anti-Pattern 4: Watcher SOQL that only checks `Status = 'Failed'`

**What the LLM generates:**

```apex
List<AsyncApexJob> failed = [
    SELECT Id, ApexClass.Name, ExtendedStatus
    FROM AsyncApexJob
    WHERE Status = 'Failed'
];
```

**Why it happens:** The model treats `Status = 'Failed'` as the canonical failure indicator, missing that batches can complete with errors and that stuck-queued jobs are also failures from an SLA perspective.

**Correct pattern:**

```apex
// Cover four failure modes, not one.
List<AsyncApexJob> failed = [
    SELECT Id, JobType, ApexClass.Name, Status, NumberOfErrors,
           ExtendedStatus, CompletedDate, CreatedDate
    FROM AsyncApexJob
    WHERE (Status IN ('Failed', 'Aborted')
            AND CompletedDate >= :Datetime.now().addMinutes(-20))
       OR (Status = 'Completed'
            AND NumberOfErrors > 0
            AND CompletedDate >= :Datetime.now().addMinutes(-20))
       OR (Status IN ('Queued', 'Holding', 'Preparing')
            AND CreatedDate <= :Datetime.now().addHours(-2))
];
```

**Detection hint:** Watcher SOQL containing `WHERE Status = 'Failed'` without an `OR` for `Completed` + `NumberOfErrors > 0` or for stuck-queued.

---

## Anti-Pattern 5: `BatchApexErrorEvent` subscriber with no idempotency

**What the LLM generates:**

```apex
trigger BAE on BatchApexErrorEvent (after insert) {
    for (BatchApexErrorEvent e : Trigger.new) {
        Messaging.SingleEmailMessage m = new Messaging.SingleEmailMessage();
        // populate
        Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{m});
    }
}
```

**Why it happens:** Platform events look like a transactional insert event, and the model pattern-matches against ordinary trigger logic. It misses that platform events can deliver at-least-once and that an external side effect (email) needs deduplication.

**Correct pattern:** Upsert a log row keyed by `AsyncApexJobId` and only send the email when the upsert created a new row, or look up an existing log row by `External_Id__c = e.AsyncApexJobId` and skip notification on hit.

**Detection hint:** Any `BatchApexErrorEvent` trigger that calls `Messaging.sendEmail`, `Messaging.CustomNotification.send`, or an outbound HTTP call without a prior dedup check by `AsyncApexJobId`.

---

## Anti-Pattern 6: Watcher schedule whose body itself can throw without protection

**What the LLM generates:** A `Schedulable` watcher whose `execute()` does heavy SOQL and DML inline with no try-catch — relying on the watcher itself never failing.

**Why it happens:** The watcher is *the* failure-detection mechanism in the model's mental model, so the model implicitly trusts it not to fail. In practice, the watcher hits its own governor limits in busy orgs (Gotcha 7).

**Correct pattern:** The watcher's `execute()` is wrapped in try-catch that writes to the log object (so the watcher's own failures are durable), and the heavy work (notifications, external HTTP) is enqueued into a Queueable rather than running inline in the synchronous Schedulable governor context. Additionally, an *external* uptime check confirms the watcher itself ran (e.g. external monitor pings a `/services/apexrest/heartbeat` endpoint that returns the most-recent watcher run timestamp).

**Detection hint:** A `Schedulable` class with `Watcher` / `Monitor` in the name whose `execute()` body has no try-catch, or which performs its own DML / HTTP inline.

---

## Anti-Pattern 7: Generating a "monitor" that uses `System.debug` as the alerting surface

**What the LLM generates:** A monitoring class that logs failures with `System.debug(LoggingLevel.ERROR, ...)` and stops there, sometimes accompanied by "configure your debug logs to capture errors."

**Why it happens:** The model knows debug logs have severity levels and confuses log capture with alerting.

**Correct pattern:** Failures must be persisted to a queryable artifact (custom log object, Big Object, or external sink) and pushed to a notification channel (email, Custom Notification, or Platform Event subscribed by a Slack/Pagerduty bridge). Debug logs are debugging telemetry, not alerts — they are gated by trace flags, roll off after hours, and require an admin to actively look at them.

**Detection hint:** Any "monitoring" or "watcher" class whose only output on failure is `System.debug(...)`.
