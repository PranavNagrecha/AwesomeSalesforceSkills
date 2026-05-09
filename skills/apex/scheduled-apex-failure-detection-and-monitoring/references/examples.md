# Examples — Scheduled Apex Failure Detection And Monitoring

## Example 1: Try-Catch + Structured Log inside `execute()`

**Context:** A nightly Schedulable class that calls `Database.executeBatch(new NightlyAccountRollup(), 200)`. Today, if the call throws (e.g. concurrency limit), the schedule advances and no batch is enqueued — silent failure.

**Problem:** Without an explicit catch + log, the only signal is the absence of an `AsyncApexJob` row for the batch, which is hard to observe directly.

**Solution:**

```apex
public class NightlyAccountRollupSchedule implements Schedulable {

    public void execute(SchedulableContext sc) {
        Id traceId = ApplicationLogger.startTrace('NightlyAccountRollupSchedule');
        try {
            // Log "I started" before any platform call. If this row exists but
            // no batch row exists, we know the failure was in executeBatch.
            ApplicationLogger.info(traceId, 'schedule fired, enqueuing batch');

            Id jobId = Database.executeBatch(new NightlyAccountRollup(), 200);

            ApplicationLogger.info(traceId,
                'batch enqueued, AsyncApexJobId=' + jobId);
        } catch (Exception e) {
            // Catch *here* so we can log; re-throwing is optional. Re-throwing
            // marks the AsyncApexJob row 'Failed' (which is what most ops teams
            // actually want for visibility); swallowing keeps the schedule
            // 'Completed' but you must trust the log.
            ApplicationLogger.error(traceId,
                'schedule launch failed: ' + e.getTypeName() + ': ' + e.getMessage(),
                e.getStackTraceString());
            throw e;
        }
    }
}
```

**Why it works:** The "schedule fired" log entry is the witness that distinguishes "schedule never ran" from "schedule ran but `executeBatch` failed". Without it, the gap between `CronTrigger.PreviousFireTime` advancing and `AsyncApexJob` not appearing is invisible. Re-throwing makes the failure also visible on the `AsyncApexJob` row's `ExtendedStatus` and (if the batch class itself implements `RaisesPlatformEvents`) on `BatchApexErrorEvent`.

---

## Example 2: `BatchApexErrorEvent` Subscriber Trigger

**Context:** A `Database.Batchable` class whose `execute()` occasionally throws on malformed records. Today, the `AsyncApexJob` ends `Completed` (because the batch swallows individual record errors) or `Failed` (if uncaught), but neither path notifies anyone.

**Problem:** Without a subscriber on `BatchApexErrorEvent`, even uncaught batch exceptions only surface in `ExtendedStatus` — a field nobody is querying.

**Solution:**

Step 1 — Add the marker interface to the batch class:

```apex
public class NightlyAccountRollup
    implements Database.Batchable<SObject>,
               Database.RaisesPlatformEvents,
               Database.Stateful {

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, AnnualRevenue FROM Account WHERE Active__c = true'
        );
    }

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        // intentional shape: any uncaught exception here will produce a
        // BatchApexErrorEvent because of RaisesPlatformEvents.
        for (Account a : scope) {
            a.AnnualRevenue = recompute(a);
        }
        update scope;  // a DmlException here is what we want to capture
    }

    public void finish(Database.BatchableContext bc) {}

    private Decimal recompute(Account a) { /* ... */ return a.AnnualRevenue; }
}
```

Step 2 — Subscriber trigger:

```apex
trigger BatchApexErrorEventTrigger on BatchApexErrorEvent (after insert) {
    List<Application_Log__c> logs = new List<Application_Log__c>();
    List<Messaging.SingleEmailMessage> emails = new List<Messaging.SingleEmailMessage>();

    Set<Id> jobIds = new Set<Id>();
    for (BatchApexErrorEvent evt : Trigger.new) {
        jobIds.add(evt.AsyncApexJobId);
    }

    Map<Id, AsyncApexJob> jobs = new Map<Id, AsyncApexJob>([
        SELECT Id, ApexClass.Name, JobItemsProcessed, TotalJobItems, NumberOfErrors
        FROM AsyncApexJob
        WHERE Id IN :jobIds
    ]);

    String[] opsRecipients = OperationsConfig.getBatchFailureRecipients();

    for (BatchApexErrorEvent evt : Trigger.new) {
        AsyncApexJob job = jobs.get(evt.AsyncApexJobId);
        String className = job != null ? job.ApexClass.Name : 'unknown';

        logs.add(new Application_Log__c(
            Severity__c    = 'ERROR',
            Source__c      = 'BatchApexErrorEvent',
            Message__c     = className + ' phase=' + evt.Phase
                              + ' type=' + evt.ExceptionType
                              + ' msg=' + evt.Message,
            Stack_Trace__c = evt.StackTrace,
            External_Id__c = evt.AsyncApexJobId
        ));

        if (!opsRecipients.isEmpty()) {
            Messaging.SingleEmailMessage m = new Messaging.SingleEmailMessage();
            m.setToAddresses(opsRecipients);
            m.setSubject('[BatchApexError] ' + className + ' (' + evt.Phase + ')');
            m.setPlainTextBody(
                'Job: ' + evt.AsyncApexJobId + '\n' +
                'Class: ' + className + '\n' +
                'Phase: ' + evt.Phase + '\n' +
                'Type: ' + evt.ExceptionType + '\n' +
                'Message: ' + evt.Message + '\n\n' +
                'Stack:\n' + evt.StackTrace
            );
            emails.add(m);
        }
    }

    if (!logs.isEmpty()) insert logs;
    if (!emails.isEmpty()) Messaging.sendEmail(emails);
}
```

**Why it works:** `BatchApexErrorEvent` is published *automatically* by the platform — no polling, no scheduled watcher needed for this failure mode. The subscriber receives `AsyncApexJobId`, `Phase` (`START` / `EXECUTE` / `FINISH`), `ExceptionType`, `Message`, and `StackTrace`, which is enough for both logging and a useful notification. Idempotency comes from `External_Id__c = AsyncApexJobId` on the log object — re-publishes (which can happen) upsert into the same row.

---

## Example 3: `AsyncApexJob` Watcher Schedule

**Context:** A schedule that runs every 15 minutes and reports any failed, aborted, error-completed, or stuck-queued async jobs in the previous window. Catches the gaps `BatchApexErrorEvent` does not cover (Queueable failures, stuck jobs, schedule misfires, completed-with-errors).

**Problem:** `BatchApexErrorEvent` does not cover Queueable / Future / Schedulable failures, and does not surface "stuck in Queued" or "completed with NumberOfErrors > 0".

**Solution:**

```apex
public class AsyncApexJobWatcher implements Schedulable {

    @TestVisible
    private static final Integer LOOKBACK_MINUTES = 20;
    @TestVisible
    private static final Integer STUCK_QUEUED_HOURS = 2;

    public void execute(SchedulableContext sc) {
        Datetime windowStart = Datetime.now().addMinutes(-LOOKBACK_MINUTES);
        Datetime stuckThreshold = Datetime.now().addHours(-STUCK_QUEUED_HOURS);

        // 1. Failed or Aborted in the last window
        List<AsyncApexJob> failures = [
            SELECT Id, JobType, ApexClass.Name, Status, NumberOfErrors,
                   ExtendedStatus, CompletedDate, CreatedDate, MethodName
            FROM AsyncApexJob
            WHERE Status IN ('Failed', 'Aborted')
              AND CompletedDate >= :windowStart
        ];

        // 2. Completed but with errors (Batch can complete this way)
        List<AsyncApexJob> errorCompletions = [
            SELECT Id, JobType, ApexClass.Name, Status, NumberOfErrors,
                   ExtendedStatus, CompletedDate, MethodName
            FROM AsyncApexJob
            WHERE Status = 'Completed'
              AND NumberOfErrors > 0
              AND CompletedDate >= :windowStart
        ];

        // 3. Stuck in Queued / Holding longer than threshold
        List<AsyncApexJob> stuck = [
            SELECT Id, JobType, ApexClass.Name, Status, CreatedDate, MethodName
            FROM AsyncApexJob
            WHERE Status IN ('Queued', 'Holding', 'Preparing')
              AND CreatedDate <= :stuckThreshold
        ];

        if (failures.isEmpty() && errorCompletions.isEmpty() && stuck.isEmpty()) {
            return;
        }

        FailureNotifier.notify(failures, errorCompletions, stuck);
    }
}
```

The companion `FailureNotifier`:

```apex
public class FailureNotifier {

    public static void notify(List<AsyncApexJob> failures,
                              List<AsyncApexJob> errorCompletions,
                              List<AsyncApexJob> stuck) {
        // Idempotency: skip jobs already logged this run cycle.
        Set<Id> alreadyLogged = new Map<Id, Application_Log__c>([
            SELECT Id, External_Id__c FROM Application_Log__c
            WHERE Source__c = 'AsyncApexJobWatcher'
              AND CreatedDate = LAST_N_HOURS:1
        ]).keySet();

        List<Application_Log__c> logs = new List<Application_Log__c>();
        List<AsyncApexJob> toAlert = new List<AsyncApexJob>();

        for (AsyncApexJob j : failures) {
            if (alreadyLogged.contains(j.Id)) continue;
            logs.add(buildLog(j, 'FAILED_OR_ABORTED', j.ExtendedStatus));
            toAlert.add(j);
        }
        for (AsyncApexJob j : errorCompletions) {
            if (alreadyLogged.contains(j.Id)) continue;
            logs.add(buildLog(j, 'COMPLETED_WITH_ERRORS',
                'NumberOfErrors=' + j.NumberOfErrors
                + ' ExtendedStatus=' + j.ExtendedStatus));
            toAlert.add(j);
        }
        for (AsyncApexJob j : stuck) {
            if (alreadyLogged.contains(j.Id)) continue;
            logs.add(buildLog(j, 'STUCK_' + j.Status,
                'in ' + j.Status + ' since ' + j.CreatedDate.format()));
            toAlert.add(j);
        }

        if (!logs.isEmpty()) insert logs;
        if (!toAlert.isEmpty()) sendCustomNotification(toAlert);
    }

    private static Application_Log__c buildLog(AsyncApexJob j, String code, String detail) {
        return new Application_Log__c(
            Severity__c    = 'ERROR',
            Source__c      = 'AsyncApexJobWatcher',
            Message__c     = code + ' ' + j.JobType + ' '
                              + (j.ApexClass != null ? j.ApexClass.Name : '') + ': ' + detail,
            External_Id__c = j.Id
        );
    }

    private static void sendCustomNotification(List<AsyncApexJob> jobs) {
        // CustomNotificationType DeveloperName, recipients, etc. omitted for brevity.
        // See apex/apex-custom-notifications-from-apex for the canonical pattern.
    }
}
```

**Why it works:** The watcher covers *every* `JobType` (not just batch), distinguishes failure modes (`FAILED_OR_ABORTED` vs `COMPLETED_WITH_ERRORS` vs `STUCK_*`) so the runbook can branch, and dedupes via `External_Id__c = AsyncApexJob.Id` on the log object so the same failure isn't re-alerted on the next watcher tick.

---

## Example 4: Custom Notification on Failure (bell icon path)

**Context:** Operators want bell-icon notifications inside Salesforce when a critical batch fails, not just an email.

**Problem:** Email is easy to miss. The bell-icon Notification Tray is durable until cleared and works on mobile.

**Solution:**

```apex
public class FailureCustomNotifier {

    private static final String NOTIF_TYPE_DEV_NAME = 'Async_Apex_Failure';

    public static void publish(AsyncApexJob job, String detail) {
        CustomNotificationType notifType = [
            SELECT Id FROM CustomNotificationType
            WHERE DeveloperName = :NOTIF_TYPE_DEV_NAME
            LIMIT 1
        ];

        Set<String> recipientUserIds = OperationsConfig.getOpsUserIds();

        Messaging.CustomNotification n = new Messaging.CustomNotification();
        n.setNotificationTypeId(notifType.Id);
        n.setTitle('[Async failure] '
            + (job.ApexClass != null ? job.ApexClass.Name : job.JobType));
        n.setBody(detail);
        n.setTargetId(job.Id);  // tap navigates to AsyncApexJob detail (limited UI but parseable)

        try {
            n.send(recipientUserIds);
        } catch (Exception e) {
            // The Custom Notification API can fail (e.g. recipient set empty).
            // Don't let the watcher itself fail because notification publishing failed —
            // the log row was already inserted, so the failure is durable.
            ApplicationLogger.warn(null,
                'Custom Notification publish failed: ' + e.getMessage());
        }
    }
}
```

**Why it works:** Custom Notifications are durable until the user taps "clear", surface on desktop and mobile, and are not gated by Email Deliverability settings (which sometimes accidentally block alert emails). Wrapping `n.send()` in its own try-catch is essential — the watcher's primary job is to log the failure; notification publishing is best-effort.

---

## Anti-Pattern: Trusting Setup → Apex Jobs as the failure channel

**What practitioners do:** "We have monitoring — admins check Setup → Apex Jobs every morning."

**What goes wrong:** Setup → Apex Jobs (a) only renders recent rows from `AsyncApexJob`, (b) does not surface "schedule fired but `executeBatch` was never called", (c) has no alerting layer, (d) is checked when admins remember (which is never on weekends), and (e) does not cover Queueable / Future / Schedulable failures distinctly. By the time someone notices, the data has been wrong for days.

**Correct approach:** Treat Setup → Apex Jobs as a *forensics* tool, not a monitoring channel. Detection must be programmatic — via `BatchApexErrorEvent`, in-job logging, and an `AsyncApexJob` watcher schedule — and notifications must be pushed (email, Custom Notification, Slack via Platform Event) rather than pulled.
