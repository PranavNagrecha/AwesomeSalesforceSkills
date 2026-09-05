# Code Examples — Debug And Logging

A deployable transaction-logging slice: `LogService` (a thin facade over the canonical
`templates/apex/ApplicationLogger.cls`), a `Log_Event__e` platform event configured to publish
immediately so ERROR/FATAL records survive a rollback, the subscriber trigger that lands them in
`Application_Log__c`, a test class that proves the round trip with `Test.getEventBus().deliver()`,
the Apex exception-email fence, and the manifest.

## What This Builds

| Artifact | File | Why it exists |
|---|---|---|
| Canonical logger | `templates/apex/ApplicationLogger.cls` (do not copy — deploy as-is) | Buffered `Application_Log__c` writer, severity gated by `Logger_Setting__mdt` |
| Log store | `templates/apex/custom_objects/Application_Log__c.object-meta.xml` + `fields/` | Durable rows the logger writes |
| New field on the log store | `Limits_Snapshot__c` | Carries the `Limits` reading taken at log time |
| Facade | `LogService.cls` | Adds correlation id, `Limits` snapshot, and the publish-immediately escape hatch |
| Event | `Log_Event__e` (`publishBehavior` = `PublishImmediately`) | ERROR/FATAL survive the rollback that discards the DML log row |
| Subscriber | `LogEventTrigger.trigger` | Turns delivered events into `Application_Log__c` rows |
| Subscriber running user | `LogEventTriggerConfig.platformEventSubscriberConfig-meta.xml` | Without it the trigger runs as Automated Process and its debug log belongs to that entity |
| Exception fence | `apexEmailNotifications.notifications` | Unhandled-exception mail goes to a monitored address, not one developer's inbox |
| Test | `LogServiceTest.cls` | Asserts event fields and the subscriber's durable row |

## How To Read It

- `LogService` **delegates** to `ApplicationLogger` for INFO/WARN. It does not re-implement buffering,
  severity gating, or the `Logger_Setting__mdt` read — that is `ApplicationLogger`'s job.
- ERROR and FATAL go down the event path instead, because `EventBus.publish` on an event configured
  `PublishImmediately` publishes "when the publish call executes, regardless of whether the transaction
  succeeds" (Metadata API Developer Guide, `CustomObject.publishBehavior`, api_meta L42222–42229).
  A `Application_Log__c` insert in the same transaction is rolled back with everything else.
- The correlation id is `System.Request.getCurrent().getRequestId()` — a string that "uniquely identifies
  the request, and can be correlated with Event Monitoring logs" (Apex Developer Guide L16322–16327,
  described there for `FinalizerContext`; `System.Request` exposes the same request identity,
  Apex Reference Guide L228139–228215). `ApexLog.RequestIdentifier` is the matching field on the debug
  log itself — "Use this request identifier to correlate multiple debug logs triggered by the same
  request" (Object Reference, ApexLog, L31266+).
- The `Limits` snapshot is read at log time, not at flush time, because the numbers move.
  Method names from Apex Reference Guide, Limits Class (L220200–220290).
- Publish-immediate calls consume a **separate 150-call limit**, not the DML limit — "Maximum number of
  `EventBus.publish` calls for platform events configured to publish immediately: 150 / 150"
  (Apex Developer Guide L19598–19599). `LogService.flush()` reads the remaining headroom with
  `Limits.getPublishImmediateDML()` before publishing rather than assuming it has room.

---

## `force-app/main/default/classes/LogService.cls`

```apex
/**
 * LogService — thin facade over templates/apex/ApplicationLogger.cls.
 *
 * Adds three things ApplicationLogger deliberately does not carry:
 *   1. a stable per-transaction correlation id (System.Request.getCurrent().getRequestId())
 *   2. a Limits snapshot captured at the moment of the log call
 *   3. a publish-immediately platform-event path so ERROR/FATAL survive a rollback
 *
 * It does NOT re-implement buffering or severity gating. INFO and WARN are handed
 * straight to ApplicationLogger.log(), which reads Logger_Setting__mdt.
 *
 * Usage:
 *     LogService.info('OrderSync.run', 'Processing ' + orders.size() + ' orders');
 *     try {
 *         doWork();
 *     } catch (Exception e) {
 *         LogService.error('OrderSync.run', e);   // buffered as an event
 *         throw e;                                 // still fail loudly
 *     } finally {
 *         LogService.flush();                      // publishes; survives the rollback
 *     }
 */
public with sharing class LogService {

    /** Which sink a call is routed to. */
    public enum Sink { DURABLE, EVENT, BOTH }

    private static final String UNKNOWN_SOURCE = 'Unknown';
    private static final Integer MESSAGE_MAX = 32768;
    private static final Integer SOURCE_MAX = 255;

    @TestVisible private static String correlationId;
    @TestVisible private static List<Log_Event__e> pending = new List<Log_Event__e>();
    @TestVisible private static Integer droppedForHeadroom = 0;

    /**
     * Stable for the life of the transaction. The same value is stamped on every
     * event and on ApplicationLogger's Request_Id__c, so one query joins them.
     */
    public static String getCorrelationId() {
        if (correlationId == null) {
            correlationId = System.Request.getCurrent().getRequestId();
        }
        return correlationId;
    }

    /** Governor reading at the instant of the log call. Cheap: no SOQL, no DML. */
    public static String limitsSnapshot() {
        List<String> parts = new List<String>();
        parts.add('soql=' + Limits.getQueries() + '/' + Limits.getLimitQueries());
        parts.add('rows=' + Limits.getQueryRows() + '/' + Limits.getLimitQueryRows());
        parts.add('dml=' + Limits.getDmlStatements() + '/' + Limits.getLimitDmlStatements());
        parts.add('cpu=' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime());
        parts.add('heap=' + Limits.getHeapSize() + '/' + Limits.getLimitHeapSize());
        parts.add('pubNow=' + Limits.getPublishImmediateDML() + '/' + Limits.getLimitPublishImmediateDML());
        return String.join(parts, ';');
    }

    public static void info(String source, String message) {
        write(ApplicationLogger.Severity.INFOL, source, message, null, Sink.DURABLE);
    }

    public static void warn(String source, String message) {
        write(ApplicationLogger.Severity.WARN, source, message, null, Sink.DURABLE);
    }

    /** ERROR goes to the event path so it outlives a rollback. */
    public static void error(String source, Exception cause) {
        write(ApplicationLogger.Severity.ERROR, source, messageOf(cause), cause, Sink.EVENT);
    }

    public static void fatal(String source, Exception cause) {
        write(ApplicationLogger.Severity.FATAL, source, messageOf(cause), cause, Sink.EVENT);
    }

    public static void write(ApplicationLogger.Severity severity,
                             String source,
                             String message,
                             Exception cause,
                             Sink sink) {
        if (sink == Sink.DURABLE || sink == Sink.BOTH) {
            String annotated = safeMessage(message) + ' | corr=' + getCorrelationId()
                             + ' | ' + limitsSnapshot();
            ApplicationLogger.log(severity, source, annotated, cause);
        }
        if (sink == Sink.EVENT || sink == Sink.BOTH) {
            pending.add(buildEvent(severity, source, message, cause));
        }
    }

    /**
     * Publishes buffered events and flushes ApplicationLogger's DML buffer.
     * Call from a finally{} block, from Batchable.finish(), or from a Finalizer.
     */
    public static List<Database.SaveResult> flush() {
        ApplicationLogger.flush();
        List<Database.SaveResult> results = new List<Database.SaveResult>();
        if (pending.isEmpty()) {
            return results;
        }
        Integer headroom = Limits.getLimitPublishImmediateDML() - Limits.getPublishImmediateDML();
        if (headroom <= 0) {
            droppedForHeadroom += pending.size();
            System.debug(LoggingLevel.ERROR,
                'LogService.flush: publish-immediate limit exhausted; dropped '
                + pending.size() + ' event(s) for corr=' + getCorrelationId());
            pending.clear();
            return results;
        }
        List<Log_Event__e> batch = new List<Log_Event__e>();
        for (Log_Event__e evt : pending) {
            if (batch.size() >= headroom) {
                droppedForHeadroom++;
                continue;
            }
            batch.add(evt);
        }
        results = EventBus.publish(batch);
        // Collect first, log once: a debug line per error inside the loop is the
        // pattern this skill's checker flags, and it is no more informative.
        List<String> failures = new List<String>();
        for (Database.SaveResult sr : results) {
            if (sr.isSuccess()) {
                continue;
            }
            for (Database.Error err : sr.getErrors()) {
                failures.add(err.getStatusCode() + ' ' + err.getMessage());
            }
        }
        if (!failures.isEmpty()) {
            System.debug(LoggingLevel.ERROR, 'LogService.flush: ' + failures.size()
                + ' publish failure(s) for corr=' + getCorrelationId()
                + ' -> ' + String.join(failures, ' | '));
        }
        pending.clear();
        return results;
    }

    @TestVisible
    private static Log_Event__e buildEvent(ApplicationLogger.Severity severity,
                                           String source,
                                           String message,
                                           Exception cause) {
        Log_Event__e evt = new Log_Event__e();
        evt.Correlation_Id__c = getCorrelationId();
        evt.Severity__c = severity.name();
        evt.Source__c = source == null ? UNKNOWN_SOURCE : source.left(SOURCE_MAX);
        evt.Message__c = safeMessage(message);
        evt.Limits_Snapshot__c = limitsSnapshot().left(SOURCE_MAX);
        evt.Quiddity__c = String.valueOf(System.Request.getCurrent().getQuiddity());
        evt.Running_User_Id__c = UserInfo.getUserId();
        evt.Logged_At__c = System.now();
        if (cause != null) {
            evt.Exception_Type__c = cause.getTypeName();
            evt.Stack_Trace__c = safeTrace(cause);
            evt.Line_Number__c = cause.getLineNumber();
        }
        return evt;
    }

    private static String messageOf(Exception cause) {
        return cause == null ? 'null exception' : cause.getMessage();
    }

    private static String safeMessage(String message) {
        return (message == null ? '' : message).left(MESSAGE_MAX);
    }

    private static String safeTrace(Exception cause) {
        String trace = cause.getStackTraceString();
        return String.isBlank(trace) ? null : trace.left(MESSAGE_MAX);
    }
}
```

### `force-app/main/default/classes/LogService.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

API version 67.0 matches `templates/apex/ApplicationLogger.cls-meta.xml` and the debug-log header
example in the Apex Developer Guide (L38147). It is also the version at which
`EventBus.publish` began running with `AccessLevel.USER_MODE` rather than `SYSTEM_MODE`
(Apex Reference Guide L214529–214531) — see gotchas.md.

---

## `Log_Event__e` — the platform event

Shown in metadata format (fields inline), which is the shape the Metadata API Developer Guide
documents for `CustomObject` (api_meta L42457–42479). In source format, split each `<fields>` block
into `force-app/main/default/objects/Log_Event__e/fields/<FieldName>.field-meta.xml` wrapped in a
`<CustomField>` root — one field per file, same child elements.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Transaction log event. Publish-immediately so ERROR/FATAL survive a rollback.</description>
    <label>Log Event</label>
    <pluralLabel>Log Events</pluralLabel>
    <eventType>HighVolume</eventType>
    <publishBehavior>PublishImmediately</publishBehavior>
    <fields>
        <fullName>Correlation_Id__c</fullName>
        <externalId>false</externalId>
        <label>Correlation Id</label>
        <length>64</length>
        <type>Text</type>
        <unique>false</unique>
    </fields>
    <fields>
        <fullName>Severity__c</fullName>
        <externalId>false</externalId>
        <label>Severity</label>
        <length>10</length>
        <type>Text</type>
        <unique>false</unique>
    </fields>
    <fields>
        <fullName>Source__c</fullName>
        <externalId>false</externalId>
        <label>Source</label>
        <length>255</length>
        <type>Text</type>
        <unique>false</unique>
    </fields>
    <fields>
        <fullName>Message__c</fullName>
        <externalId>false</externalId>
        <label>Message</label>
        <length>32768</length>
        <type>LongTextArea</type>
        <visibleLines>5</visibleLines>
    </fields>
    <fields>
        <fullName>Exception_Type__c</fullName>
        <externalId>false</externalId>
        <label>Exception Type</label>
        <length>255</length>
        <type>Text</type>
        <unique>false</unique>
    </fields>
    <fields>
        <fullName>Stack_Trace__c</fullName>
        <externalId>false</externalId>
        <label>Stack Trace</label>
        <length>32768</length>
        <type>LongTextArea</type>
        <visibleLines>10</visibleLines>
    </fields>
    <fields>
        <fullName>Line_Number__c</fullName>
        <externalId>false</externalId>
        <label>Line Number</label>
        <precision>9</precision>
        <scale>0</scale>
        <type>Number</type>
        <unique>false</unique>
    </fields>
    <fields>
        <fullName>Limits_Snapshot__c</fullName>
        <externalId>false</externalId>
        <label>Limits Snapshot</label>
        <length>255</length>
        <type>Text</type>
        <unique>false</unique>
    </fields>
    <fields>
        <fullName>Quiddity__c</fullName>
        <externalId>false</externalId>
        <label>Quiddity</label>
        <length>80</length>
        <type>Text</type>
        <unique>false</unique>
    </fields>
    <fields>
        <fullName>Running_User_Id__c</fullName>
        <externalId>false</externalId>
        <label>Running User Id</label>
        <length>18</length>
        <type>Text</type>
        <unique>false</unique>
    </fields>
    <fields>
        <fullName>Logged_At__c</fullName>
        <externalId>false</externalId>
        <label>Logged At</label>
        <type>DateTime</type>
    </fields>
</CustomObject>
```

- `eventType` valid values are `HighVolume` and `StandardVolume`, and `StandardVolume` is deprecated —
  "Creating a platform event with this event type is supported and returns an error"
  (api_meta L42091–42097). Use `HighVolume`.
- `publishBehavior` defaults to `PublishImmediately` when the element is absent (api_meta L42227–42229).
  State it anyway: a reviewer reading the file should not have to know the default, and a later
  hand-edit that flips it to `PublishAfterCommit` is then a visible diff.
- UNVERIFIED (2026-09-05): the corpus does not enumerate which custom field types a platform event
  supports, so the `LongTextArea`, `Number`, and `DateTime` choices above rest on the general
  `CustomObject`/`CustomField` element tables, not on a platform-event-specific field-type list.
  Deploy to a scratch org before trusting them.

### The one new field on the existing log store

`force-app/main/default/objects/Application_Log__c/fields/Limits_Snapshot__c.field-meta.xml` —
an addition to `templates/apex/custom_objects/`, not a replacement for it.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Limits_Snapshot__c</fullName>
    <externalId>false</externalId>
    <label>Limits Snapshot</label>
    <length>255</length>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

---

## `force-app/main/default/triggers/LogEventTrigger.trigger`

```apex
/**
 * Subscriber for Log_Event__e. Lands delivered events as Application_Log__c rows.
 *
 * Partial-success insert on purpose: one malformed event must not discard the batch.
 * This trigger never throws — a thrown exception here would retry or discard the
 * whole batch of event messages, and losing the log is worse than losing one row.
 */
trigger LogEventTrigger on Log_Event__e (after insert) {
    List<Application_Log__c> rows = new List<Application_Log__c>();
    for (Log_Event__e evt : Trigger.new) {
        Application_Log__c row = new Application_Log__c();
        row.Severity__c = evt.Severity__c;
        row.Source__c = evt.Source__c;
        row.Message__c = evt.Message__c;
        row.Stack_Trace__c = evt.Stack_Trace__c;
        row.Exception_Type__c = evt.Exception_Type__c;
        row.Quiddity__c = evt.Quiddity__c;
        row.Request_Id__c = evt.Correlation_Id__c;
        row.Running_User__c = evt.Running_User_Id__c;
        row.Limits_Snapshot__c = evt.Limits_Snapshot__c;
        rows.add(row);
    }
    if (!rows.isEmpty()) {
        Database.insert(rows, false);
    }
}
```

### `force-app/main/default/triggers/LogEventTrigger.trigger-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexTrigger xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexTrigger>
```

### `force-app/main/default/platformEventSubscriberConfigs/LogEventTriggerConfig.platformEventSubscriberConfig-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventSubscriberConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <platformEventConsumer>LogEventTrigger</platformEventConsumer>
    <batchSize>200</batchSize>
    <masterLabel>LogEventTriggerConfig</masterLabel>
    <user>integration.user@example.com</user>
    <isProtected>false</isProtected>
</PlatformEventSubscriberConfig>
```

Shape and element names from api_meta L96473–96480. The `user` element is the reason this file exists:
"By default, the platform event trigger runs as the Automated Process entity … Debug logs for the
trigger execution are created by this user" (api_meta L96454–96462). Without it you cannot pull a
debug log for your own logging subscriber under your own username, and `Running_User__c` on the row
will be the Automated Process entity rather than the person who caused the log.

---

## `force-app/main/default/apexEmailNotifications/apexEmailNotifications.notifications`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexEmailNotifications xmlns="http://soap.sforce.com/2006/04/metadata">
    <apexEmailNotification>
        <email>platform-alerts@example.com</email>
    </apexEmailNotification>
    <apexEmailNotification>
        <user>release.manager@example.com</user>
    </apexEmailNotification>
</ApexEmailNotifications>
```

Each `apexEmailNotification` carries an email **or** a user, never both (api_meta L22445).
Deploying this type **deletes every notification already in the org** that is not in the file
(api_meta L22458–22461) — retrieve before you deploy. It is also not supported in
`destructiveChanges.xml`; to remove entries you deploy the list without them (api_meta L22468–22470).

---

## `force-app/main/default/classes/LogServiceTest.cls`

```apex
@IsTest
private class LogServiceTest {

    private class LogServiceTestException extends Exception {}

    @IsTest
    static void errorPublishesEventAndSubscriberWritesDurableRow() {
        Test.startTest();
        try {
            throw new LogServiceTestException('synthetic failure');
        } catch (LogServiceTestException e) {
            LogService.error('LogServiceTest.errorPublishes', e);
        }
        List<Database.SaveResult> results = LogService.flush();
        Test.getEventBus().deliver();
        Test.stopTest();

        System.assertEquals(1, results.size(), 'One event should have been published');
        System.assertEquals(true, results[0].isSuccess(), 'Publish should succeed');

        List<Application_Log__c> rows = [
            SELECT Severity__c, Source__c, Message__c, Exception_Type__c,
                   Stack_Trace__c, Request_Id__c, Limits_Snapshot__c, Quiddity__c
            FROM Application_Log__c
            WHERE Source__c = 'LogServiceTest.errorPublishes'
        ];
        System.assertEquals(1, rows.size(), 'Subscriber should have written exactly one row');
        Application_Log__c row = rows[0];
        System.assertEquals('ERROR', row.Severity__c, 'Severity should round-trip');
        System.assertEquals('LogServiceTest.LogServiceTestException', row.Exception_Type__c,
            'Exception type should be the inner class type name');
        System.assertEquals(true, row.Message__c.contains('synthetic failure'),
            'Message should carry the exception message');
        System.assertNotEquals(null, row.Request_Id__c, 'Correlation id must be stamped');
        System.assertEquals(true, row.Limits_Snapshot__c.contains('cpu='),
            'Limits snapshot should carry a CPU reading');
        System.assertNotEquals(null, row.Quiddity__c, 'Quiddity should be captured');
    }

    @IsTest
    static void infoWritesDurablyWithoutPublishing() {
        Test.startTest();
        LogService.info('LogServiceTest.info', 'breadcrumb');
        LogService.flush();
        Test.getEventBus().deliver();
        Test.stopTest();

        List<Application_Log__c> rows = [
            SELECT Message__c FROM Application_Log__c WHERE Source__c = 'LogServiceTest.info'
        ];
        System.assertEquals(1, rows.size(), 'INFO should take the direct DML path');
        System.assertEquals(true, rows[0].Message__c.contains('corr='),
            'INFO message should be annotated with the correlation id');
        System.assertEquals(true, rows[0].Message__c.contains('soql='),
            'INFO message should be annotated with the Limits snapshot');
    }

    @IsTest
    static void correlationIdIsStableAcrossCallsInOneTransaction() {
        String first = LogService.getCorrelationId();
        String second = LogService.getCorrelationId();
        System.assertEquals(first, second, 'Correlation id must not change mid-transaction');
        System.assertNotEquals(null, first, 'Request id should be available');
    }

    @IsTest
    static void bulkLoggingStaysWithinPublishImmediateHeadroom() {
        Integer ceiling = Limits.getLimitPublishImmediateDML();
        Test.startTest();
        for (Integer i = 0; i < 250; i++) {
            LogService.error('LogServiceTest.bulk', new LogServiceTestException('e' + i));
        }
        List<Database.SaveResult> results = LogService.flush();
        Test.getEventBus().deliver();
        Test.stopTest();

        System.assertEquals(true, results.size() <= ceiling,
            'flush() must never publish more events than the publish-immediate ceiling allows');
        System.assertEquals(true, LogService.droppedForHeadroom > 0,
            'Events beyond the ceiling should be counted as dropped, not silently lost');
    }
}
```

`Test.getEventBus().deliver()` is enclosed in the `Test.startTest()` / `Test.stopTest()` block, which
is what the Apex Reference Guide requires (TestBroker Class, L157701–157710). Without the `deliver()`
call the subscriber trigger never runs and the `Application_Log__c` assertions fail on an empty list.

---

## `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Application_Log__c</members>
        <members>Log_Event__e</members>
        <members>Logger_Setting__mdt</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Application_Log__c.Limits_Snapshot__c</members>
        <members>Log_Event__e.Correlation_Id__c</members>
        <members>Log_Event__e.Severity__c</members>
        <members>Log_Event__e.Source__c</members>
        <members>Log_Event__e.Message__c</members>
        <members>Log_Event__e.Exception_Type__c</members>
        <members>Log_Event__e.Stack_Trace__c</members>
        <members>Log_Event__e.Line_Number__c</members>
        <members>Log_Event__e.Limits_Snapshot__c</members>
        <members>Log_Event__e.Quiddity__c</members>
        <members>Log_Event__e.Running_User_Id__c</members>
        <members>Log_Event__e.Logged_At__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>ApplicationLogger</members>
        <members>LogService</members>
        <members>LogServiceTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>LogEventTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>LogEventTriggerConfig</members>
        <name>PlatformEventSubscriberConfig</name>
    </types>
    <types>
        <members>apexEmailNotifications</members>
        <name>ApexEmailNotifications</name>
    </types>
    <version>67.0</version>
</Package>
```

The `CustomObject` + `CustomField` + `ApexTrigger` + `PlatformEventSubscriberConfig` grouping is the
one the Metadata API guide prescribes when the subscriber config's referenced components do not yet
exist in the org — "If the referenced trigger and platform event don't exist in the org, include their
definitions in the package. Otherwise, the deployment fails" (api_meta L96494–96497).

## Deploy Order

1. `Application_Log__c` + its fields + `Limits_Snapshot__c`, and `Logger_Setting__mdt` with a `Default`
   record — `ApplicationLogger.getMinimumSeverity()` reads `Logger_Setting__mdt.getInstance('Default')`
   and falls back to `INFOL` when it is absent, so an org without the record logs more than you expect.
2. `Log_Event__e` and its fields. The event must exist before the trigger compiles.
3. `ApplicationLogger`, then `LogService`, then `LogEventTrigger`.
4. `LogEventTriggerConfig` — last, because it references the trigger by name.
5. `apexEmailNotifications` — **retrieve first**, then deploy the merged list.

A single `sf project deploy start` resolves this ordering itself; the list matters when you are
splitting the change across releases.

```bash
# Validate without saving anything (Metadata API Developer Guide, api_meta L3985)
sf project deploy start --dry-run -d "force-app/main/default" --target-org <alias>

# Deploy for real
sf project deploy start -d "force-app/main/default" --target-org <alias>
```

## Verification

```bash
# UNVERIFIED (2026-09-05): the `sf apex` command group is documented in the Salesforce CLI
# Command Reference, which is not in the grounding corpus. Only `sf project deploy start`
# and `sf project generate` appear there (api_meta L3985, L1318). Confirm flags with `sf apex --help`.
sf apex run test --tests LogServiceTest --result-format human --wait 10 --target-org <alias>
sf apex tail log --color --target-org <alias>
```

Org-side checks that do not depend on the CLI:

```sql
-- 1. The subscriber actually landed rows, and they carry a correlation id.
SELECT Severity__c, Source__c, Request_Id__c, Limits_Snapshot__c, CreatedDate
FROM Application_Log__c
WHERE CreatedDate = TODAY
ORDER BY CreatedDate DESC
LIMIT 50

-- 2. Join a durable row back to the debug log for the same request.
--    ApexLog.RequestIdentifier is the field to match on; ApexLog is read/delete only.
SELECT Id, Operation, Status, LogLength, DurationMilliseconds, Location, RequestIdentifier, StartTime
FROM ApexLog
WHERE RequestIdentifier = '<the Request_Id__c value from step 1>'
ORDER BY StartTime DESC

-- 3. Watch the log-volume ceiling. LogLength is bytes; 20 MB per log is the truncation point
--    and 1,000 MB across the org disables trace-flag edits (Apex Developer Guide L38115-38126).
SELECT Location, COUNT(Id) logs, SUM(LogLength) bytes
FROM ApexLog
WHERE StartTime = TODAY
GROUP BY Location
```

`ApexLog` supports `delete()`, `describeSObjects()`, `query()` and `retrieve()` only — "You can read
information about this object, as well as delete it, but you can't update or insert it"
(Object Reference, ApexLog). Deleting is how you claw back headroom once the org passes the 1,000 MB
mark.

Finally, run the package checker over the source tree before you deploy:

```bash
python3 skills/apex/debug-and-logging/scripts/check_debug_and_logging.py \
    --manifest-dir force-app/main/default
```
