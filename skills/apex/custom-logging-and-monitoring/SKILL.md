---
name: custom-logging-and-monitoring
description: "Use when designing or implementing a custom logging framework in Apex: log sObject schema, log level gating, retention policies, batch purge jobs, and forwarding logs to external monitoring systems (Splunk, Datadog, etc.). NOT for built-in debug logs or Developer Console (use debug-logs-and-developer-console), NOT for exception capture and error propagation (use error-handling-framework), NOT for Event Monitoring (use security skills)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I build a custom logging framework in Apex that persists log records"
  - "my debug logs are disappearing and I need a persistent log solution"
  - "how do I implement log levels like DEBUG INFO WARN ERROR in Apex"
  - "how do I forward Apex logs to Splunk or Datadog from Salesforce"
  - "how do I purge old log records automatically to stay within storage limits"
tags:
  - logging
  - apex-framework
  - monitoring
  - log-levels
  - platform-events
  - retention
inputs:
  - "Log retention requirements (how long to keep logs)"
  - "Log levels required (DEBUG/INFO/WARN/ERROR)"
  - "External monitoring system target (Splunk, Datadog, or none)"
  - "Whether logs must survive transaction rollback"
outputs:
  - "Log sObject schema with required fields"
  - "LoggerService Apex class with level-gating singleton pattern"
  - "Batch purge job for retention policy enforcement"
  - "Platform Event configuration for rollback-safe log transport"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Custom Logging and Monitoring

Use this skill when designing or implementing a custom Apex logging framework that persists log records to a Salesforce custom object, supports log level filtering, enforces retention policies via batch deletion, and optionally forwards structured log data to external monitoring platforms (Splunk, Datadog, New Relic) via REST or Platform Events.

This skill is distinct from `error-handling-framework` (which covers exception capture and Platform Event transport for error propagation). This skill covers the **operational monitoring layer**: the LoggerService singleton, log level gating, the Log sObject schema, batch purge jobs, and external forwarding.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine whether logs must survive transaction rollback. If yes, use Platform Events to transport log records — PE inserts survive transaction rollback even when the triggering transaction rolls back.
- Identify the minimum log level to persist in production (typically WARN or ERROR to manage storage).
- Estimate log volume per hour to size storage consumption and set retention appropriately.
- Confirm whether external forwarding (Splunk, Datadog) is required and what protocol they support (REST HTTP, syslog, or platform event consumer).

---

## Core Concepts

### Log sObject Schema

A minimal but complete Log sObject (`Log__c`) needs these fields:

| Field | Type | Purpose |
|---|---|---|
| `Level__c` | Picklist: DEBUG, INFO, WARN, ERROR | Enables level-based filtering in reports/queries |
| `Source__c` | Text(255) | Class name and method that generated the log |
| `Message__c` | Long Text Area(32768) | The log message content |
| `Correlation_Id__c` | Text(50), External ID | Links async job logs together (batch ID, Queueable chain) |
| `Transaction_Id__c` | Text(50) | Groups all log records from a single Apex transaction |
| `Retention_Date__c` | Date, Indexed | Cutoff date for batch purge queries |

The `Retention_Date__c` field stores the date after which the record may be deleted. A scheduled batch job queries `WHERE Retention_Date__c < TODAY` and deletes expired records.

### LoggerService Singleton with Level Gating

A singleton pattern prevents instantiating the logger repeatedly within a transaction:

```apex
public class LoggerService {
    private static LoggerService instance;
    private static LoggingLevel minimumLevel = LoggingLevel.WARN; // configurable via Custom Metadata
    private List<Log__c> buffer = new List<Log__c>();

    public static LoggerService getInstance() {
        if (instance == null) instance = new LoggerService();
        return instance;
    }

    public void log(LoggingLevel level, String source, String message) {
        if (level.ordinal() < minimumLevel.ordinal()) return; // level gate
        buffer.add(new Log__c(
            Level__c = level.name(),
            Source__c = source,
            Message__c = message,
            Retention_Date__c = Date.today().addDays(getRetentionDays(level))
        ));
    }

    public void flush() {
        if (!buffer.isEmpty()) {
            Database.insert(buffer, false); // partial success — do not throw on log failure
            buffer.clear();
        }
    }
}
```

Call `LoggerService.getInstance().flush()` at the end of each trigger execution or before returning from an @AuraEnabled method.

### Platform Events for Rollback-Safe Logging

When a transaction rolls back (e.g., a Savepoint is released, or an unhandled exception causes rollback), DML to `Log__c` is rolled back too. For scenarios where you need to capture logs even when the transaction fails, use Platform Events:

```apex
// Publish a Log PE — this survives transaction rollback
Log_Event__e logEvent = new Log_Event__e(
    Level__c = 'ERROR',
    Source__c = 'PaymentProcessor.process',
    Message__c = 'Payment gateway timeout: ' + ex.getMessage()
);
EventBus.publish(logEvent);
// Even if the surrounding transaction rolls back, this PE is published
```

The PE subscriber trigger inserts the `Log__c` record in a new transaction.

### Batch Purge Job for Retention Enforcement

```apex
public class LogPurger implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id FROM Log__c WHERE Retention_Date__c < TODAY'
        );
    }

    public void execute(Database.BatchableContext bc, List<SObject> records) {
        Database.delete(records, false);
    }

    public void finish(Database.BatchableContext bc) {}
}
```

Schedule with: `System.schedule('LogPurger Daily', '0 0 1 * * ?', new LogPurgerSchedulable());`

---

## Common Patterns

### Level-Gated Logger with Custom Metadata Configuration

**When to use:** Production orgs where DEBUG logs would consume too much storage.

**How it works:** Store the minimum log level in a Custom Metadata record (`Logger_Config__mdt.Minimum_Level__c`). The LoggerService reads this at instantiation and gates all log() calls below the threshold. Change the threshold without a deployment by editing the Custom Metadata record.

### External Log Forwarding to Splunk/Datadog

**When to use:** Org uses a centralized monitoring platform and wants Salesforce logs alongside other application logs.

**How it works:**
1. Create a Platform Event `Log_Event__e` with the same fields as `Log__c`.
2. The PE subscriber trigger inserts `Log__c` records AND publishes a Platform Event to an external event stream (e.g., via Change Data Capture or a scheduled batch that POSTs to the SIEM REST API).
3. Use Named Credentials to store the Splunk HEC endpoint and token.

**Why PE for forwarding:** PEs provide an ordered, durable event stream. External consumers can subscribe via the Streaming API or the org can use a batch job to forward recent Log__c records via REST callout.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Log must survive transaction rollback | Platform Event publish + PE subscriber trigger | PE publishes even when parent transaction rolls back |
| Normal operation logging | Direct DML to Log__c at flush() | Simpler; acceptable for non-rollback scenarios |
| High-volume DEBUG logging in prod | Level gate at WARN or ERROR | Storage cost and query performance |
| Retention enforcement | Scheduled batch purger on Retention_Date__c | Automated; no manual intervention |
| External SIEM forwarding | Named Credential + batch REST callout | OAuth-managed credentials; callout outside main transaction |

---

## Recommended Workflow

1. **Design the Log sObject schema.** Include Level, Source, Message, Correlation_Id, Transaction_Id, and Retention_Date fields. Mark Retention_Date as indexed.
2. **Create Custom Metadata for logger configuration.** Store minimum log level and retention days per level. This allows tuning without deployment.
3. **Implement LoggerService singleton** with level gating, buffered inserts, and a flush() method. Use `Database.insert(buffer, false)` to prevent log failures from interrupting business logic.
4. **Implement rollback-safe logging via Platform Events** for error scenarios where the transaction may rollback. Publish PE in catch blocks.
5. **Implement LogPurger batch job.** Query `WHERE Retention_Date__c < TODAY` and schedule it to run nightly.
6. **If external forwarding required:** Configure Named Credential for the SIEM endpoint. Implement a scheduled batch job that queries recent `Log__c` records and POSTs to the SIEM REST API using the Named Credential.
7. **Test rollback survival.** Write a test that generates a log, rolls back a savepoint, and confirms the PE-based log record still exists.

---

## Review Checklist

- [ ] Log sObject includes Level, Source, Message, Correlation_Id, Retention_Date fields
- [ ] LoggerService uses singleton pattern with level-gating against Custom Metadata config
- [ ] `Database.insert(buffer, false)` used — log failures do not interrupt business logic
- [ ] Error logs in catch blocks use Platform Events for rollback-safe capture
- [ ] Batch purge job created and scheduled to run on Retention_Date__c < TODAY
- [ ] External forwarding uses Named Credentials (not hardcoded tokens)
- [ ] Log volume estimated against storage limits and retention period set accordingly

---

## Salesforce-Specific Gotchas

1. **Direct DML log inserts are rolled back with the transaction** — If the transaction containing your log DML rolls back, the log records disappear. For error logs specifically, use Platform Events which survive rollback.
2. **LoggingLevel enum ordinal comparison for level gating** — `LoggingLevel.ERROR.ordinal() > LoggingLevel.DEBUG.ordinal()` is true. Use ordinal comparison for efficient level gating, not string comparison.
3. **Large text fields slow down SOQL on Log__c** — Do not filter or ORDER BY on `Message__c` (Long Text Area). Use `Level__c`, `Source__c`, and `Retention_Date__c` (indexed fields) for queries. Report filters on Message__c will be slow for high-volume log tables.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Log sObject schema | Custom object definition with all required fields |
| LoggerService class | Singleton Apex class with level gating, buffering, and flush |
| LogPurger batch class | Batch Apex class for retention-based deletion |
| Logger_Config__mdt | Custom Metadata type for configurable log level and retention settings |

---

## Related Skills

- error-handling-framework — exception capture, AuraHandledException, rollback-safe PE transport for errors
- debug-logs-and-developer-console — built-in debug log management (not persistent logging)
- platform-events-apex — Platform Event patterns used by rollback-safe logging
