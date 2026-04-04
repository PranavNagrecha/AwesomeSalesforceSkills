---
name: error-handling-framework
description: "Use when designing or implementing a cross-cutting Apex error handling framework: custom exception hierarchies, rollback-safe logging via Platform Events, BatchApexErrorEvent processing, correlation ID threading, or a unified catch/log/rethrow utility class. Trigger keywords: 'error framework', 'centralized logging', 'rollback-safe log', 'BatchApexErrorEvent', 'correlation ID async', 'AuraHandledException boundary', 'Error_Log__c design'. NOT for individual try/catch block syntax help, basic DmlException handling, or choosing between synchronous and asynchronous execution models."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I log errors that survive a transaction rollback in Apex"
  - "designing a centralized error logging framework for our org"
  - "BatchApexErrorEvent not firing or not capturing stack trace"
  - "AuraHandledException thrown deep in service layer losing stack trace"
  - "correlation ID to link async job logs back to the originating transaction"
  - "custom exception hierarchy with error codes instead of string parsing"
  - "Error_Log__c custom object design for structured Apex logging"
tags:
  - error-handling-framework
  - platform-events
  - batch-apex-error-event
  - aura-handled-exception
  - correlation-id
  - custom-exceptions
  - structured-logging
  - rollback-safe-logging
inputs:
  - "entry points in scope: trigger, LWC/Aura controller, REST resource, Queueable, Batch, Scheduled"
  - "whether partial success (Database.SaveResult) is required or transactions must be all-or-nothing"
  - "existing logging mechanism in the org: Error_Log__c, external observability tool, or nothing"
  - "whether async jobs need correlation IDs back to originating records or transactions"
outputs:
  - "exception class hierarchy with typed error codes and base utility class design"
  - "Error_Log__c custom object field schema and Platform Event log publisher class"
  - "BatchApexErrorEvent subscriber handler with error extraction pattern"
  - "AuraHandledException wrapping strategy scoped to controller boundary"
  - "correlation ID threading pattern for Queueable and Batch contexts"
  - "code review findings against the error framework review checklist"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Error Handling Framework

Use this skill when Apex error handling needs to be a deliberate, reusable design — not individual try/catch blocks scattered across classes. The goal is a framework that survives transaction rollback, surfaces structured data for monitoring, enables error-type branching without string parsing, and threads correlation IDs across async boundaries.

---

## Before Starting

Gather this context before designing or reviewing a framework:

- What are all the Apex entry points that need coverage? Trigger handlers, Aura/LWC controllers, REST resources, Queueable implementations, Batch classes, and Scheduled jobs each have different failure contracts.
- Does the org have an existing `Error_Log__c` object, Platform Event for logging, or an external observability tool (Datadog, Splunk)? The framework integrates with or replaces what is already there.
- Is correlation ID linkage required? If async jobs (Batch, Queueable) need their log entries traceable back to originating records or the parent transaction, that threading must be explicit from the start — the platform does not provide it automatically.
- Is partial success required in bulk operations? The framework logging strategy differs depending on whether `Database.SaveResult[]` paths are in scope.
- What API version is the org targeting? `BatchApexErrorEvent` is available from API v44.0 onward.

---

## Core Concepts

### Concept 1: Log-via-Platform-Event Is the Only Rollback-Safe Logging Pattern

Standard DML (`insert errorLog;`) inside a failing transaction rolls back with the transaction. If a Batch `execute` method throws an uncaught exception, any `Error_Log__c` records inserted during that chunk are lost. Platform Events published via `EventBus.publish()` survive transaction rollback. The event publish is committed even if the surrounding transaction fails, because Platform Event delivery is independent of DML commit. This makes the pattern: catch the exception, build a log Platform Event payload, publish it with `EventBus.publish()`, and let a subscriber trigger insert the `Error_Log__c` record in a fresh transaction. The `Error_Log__c` write happens in the subscriber's independent transaction and cannot be rolled back by the caller's failure.

This is not just a performance optimization — it is the only architecturally correct way to guarantee log durability in Apex.

### Concept 2: BatchApexErrorEvent Fires Automatically on Batch Failures

From API v44.0 onward, Salesforce automatically publishes a `BatchApexErrorEvent` Platform Event whenever a Batch Apex `execute`, `start`, or `finish` method throws an unhandled exception. The event contains `AsyncApexJobId`, `ExceptionType`, `Message`, `StackTrace`, `DoesExceedJobScopeMaxLength`, `JobScope`, and `Phase`. An org subscribes to this event with an Apex trigger on `BatchApexErrorEvent`. This means batch error capture does not require custom try/catch inside every batch class — the platform produces the structured event automatically. Custom try/catch inside `execute` is still appropriate for expected, recoverable failures (e.g., integration timeouts on specific records), but the safety net for unhandled exceptions is automatic.

Important: `DoesExceedJobScopeMaxLength` is `true` when the set of record IDs in the failed scope exceeds the field character limit. In that case `JobScope` is truncated and the full scope must be retrieved separately via `AsyncApexJob` query if needed.

### Concept 3: AuraHandledException Must Stay at the Controller Boundary

`AuraHandledException` is a transport mechanism for delivering a human-readable error message to an Aura component or LWC — it is not a base class for domain exceptions. When thrown deep inside a service or selector class, it couples business logic to UI transport and suppresses the Apex stack trace: the platform treats `AuraHandledException` as a handled error and does not include the full server-side stack trace in the response. The correct pattern is: service classes throw typed domain exceptions; the Aura/LWC controller catches domain exceptions, logs them using the framework, and wraps the message into a new `AuraHandledException` constructed at the controller layer only. Every layer below the controller should remain unaware of `AuraHandledException`.

### Concept 4: Typed Exception Hierarchy with Error Code Enum

Branching on exception message strings (e.g., `if (e.getMessage().contains('REQUIRED_FIELD_MISSING'))`) is fragile and breaks on message text changes. A typed exception hierarchy backed by an error code enum lets callers branch on type or code. The pattern: define an `AppException` base extending `Exception`, add child classes per domain (`IntegrationException`, `ValidationException`, `ConfigurationException`), and embed an `ErrorCode` enum (`REQUIRED_FIELD_MISSING`, `DUPLICATE_VALUE`, `CALLOUT_TIMEOUT`, etc.). Callers catch the specific type or check `exception.code` without string parsing. The error code flows into the log record's `Error_Code__c` field for metric aggregation.

### Concept 5: Correlation ID Must Be Threaded Manually Through Async State

When a synchronous transaction enqueues a Queueable or starts a Batch job, there is no automatic link from the async job's log entries back to the originating record ID, user session, or transaction. `AsyncApexJob.ExtendedStatus` has a 255-character limit and is not designed for structured data. The correct pattern is to pass a `correlationId` String into the Queueable or Batch constructor, store it as an instance variable, include it in every `EventBus.publish()` call from that context, and populate `Correlation_Id__c` on the `Error_Log__c` record. The consumer of the log can then query by correlation ID to assemble the full execution trace across transaction boundaries.

---

## Common Patterns

### Pattern 1: Platform Event Log Publisher

**When to use:** Any Apex context that needs durable error logging — especially trigger handlers, batch `execute`, and queueable `execute` methods where the surrounding transaction may roll back.

**How it works:**

Define an `ErrorLog__e` Platform Event with fields: `Level__c` (Text: INFO, WARN, ERROR, FATAL), `Context__c` (Text: classname + method), `Message__c` (Text Area), `Stack_Trace__c` (Long Text Area), `Payload__c` (Long Text Area for JSON), `Correlation_Id__c` (Text).

In the `ErrorLogger` utility class:

```apex
public class ErrorLogger {
    public static void logException(
        String level,
        String context,
        Exception ex,
        String correlationId,
        String payloadJson
    ) {
        ErrorLog__e evt = new ErrorLog__e(
            Level__c       = level,
            Context__c     = context,
            Message__c     = ex.getMessage(),
            Stack_Trace__c = ex.getStackTraceString(),
            Correlation_Id__c = correlationId,
            Payload__c     = payloadJson
        );
        List<Database.SaveResult> results = EventBus.publish(new List<ErrorLog__e>{ evt });
        // SaveResult failure here means the PE limit was hit or field validation failed.
        // Log to System.debug as the absolute last resort — never DML here.
        for (Database.SaveResult sr : results) {
            if (!sr.isSuccess()) {
                System.debug(LoggingLevel.ERROR,
                    'ErrorLogger: failed to publish ErrorLog__e — ' + sr.getErrors());
            }
        }
    }
}
```

A trigger on `ErrorLog__e` then inserts `Error_Log__c` records in a fresh, independent transaction.

**Why not the alternative:** Inserting `Error_Log__c` directly in the catch block loses the log if the enclosing transaction rolls back.

### Pattern 2: Typed Domain Exception Hierarchy

**When to use:** Any service layer, selector, or integration class that needs to signal a specific failure type to its callers.

**How it works:**

```apex
public class AppException extends Exception {
    public enum ErrorCode {
        REQUIRED_FIELD_MISSING,
        DUPLICATE_VALUE,
        CALLOUT_TIMEOUT,
        INTEGRATION_AUTH_FAILURE,
        CONFIGURATION_MISSING,
        UNEXPECTED
    }
    public ErrorCode code { get; private set; }

    public AppException(ErrorCode code, String message) {
        this(message);
        this.code = code;
    }
}

public class IntegrationException extends AppException { }
public class ValidationException extends AppException { }
public class ConfigurationException extends AppException { }
```

Callers branch by type:

```apex
try {
    integrationService.callExternalAPI(payload);
} catch (IntegrationException ie) {
    if (ie.code == AppException.ErrorCode.CALLOUT_TIMEOUT) {
        // enqueue retry
    } else {
        // surface to user
        throw new AuraHandledException(ie.getMessage());
    }
} catch (AppException ae) {
    ErrorLogger.logException('ERROR', 'MyController.doWork', ae, correlationId, null);
    throw new AuraHandledException('An unexpected error occurred. Reference: ' + correlationId);
}
```

**Why not the alternative:** Catching `Exception` and parsing `getMessage()` for string keywords is fragile and produces inconsistent behavior when Salesforce changes system exception message text.

### Pattern 3: BatchApexErrorEvent Subscriber

**When to use:** Any org running Batch Apex jobs that need automatic capture of unhandled batch failures without wrapping every execute method in try/catch.

**How it works:**

```apex
trigger BatchApexErrorEventTrigger on BatchApexErrorEvent (after insert) {
    for (BatchApexErrorEvent evt : Trigger.new) {
        // Publish to ErrorLog__e so the same subscriber writes the Error_Log__c record.
        ErrorLog__e logEvt = new ErrorLog__e(
            Level__c       = 'ERROR',
            Context__c     = 'BatchApexErrorEvent:' + evt.Phase,
            Message__c     = evt.Message,
            Stack_Trace__c = evt.StackTrace,
            Payload__c     = JSON.serialize(new Map<String, Object>{
                'AsyncApexJobId' => evt.AsyncApexJobId,
                'ExceptionType'  => evt.ExceptionType,
                'DoesExceedJobScopeMaxLength' => evt.DoesExceedJobScopeMaxLength,
                'JobScope'       => evt.JobScope
            }),
            Correlation_Id__c = evt.AsyncApexJobId
        );
        EventBus.publish(logEvt);
    }
}
```

**Why not the alternative:** Adding `try/catch` to every batch `execute` method for unhandled failures is error-prone and relies on individual developers remembering to do it. The `BatchApexErrorEvent` safety net is automatic and catches even `NullPointerException` and `LimitException` failures that a developer may not anticipate.

### Pattern 4: Correlation ID Threading in Queueable and Batch

**When to use:** Any async job whose failures or logs need to be traceable back to an originating record, user action, or parent transaction.

**How it works:**

```apex
public class AccountSyncQueueable implements Queueable, Database.AllowsCallouts {
    private final String correlationId;
    private final List<Id> accountIds;

    public AccountSyncQueueable(List<Id> accountIds, String correlationId) {
        this.accountIds = accountIds;
        this.correlationId = correlationId;
    }

    public void execute(QueueableContext ctx) {
        try {
            // ... business logic ...
        } catch (IntegrationException ie) {
            ErrorLogger.logException('ERROR', 'AccountSyncQueueable.execute', ie,
                correlationId, JSON.serialize(accountIds));
        }
    }
}
```

The caller passes `correlationId`:

```apex
String corrId = UserInfo.getUserId() + ':' + String.valueOf(Datetime.now().getTime());
System.enqueueJob(new AccountSyncQueueable(accountIds, corrId));
```

**Why not the alternative:** Without an explicit correlation ID, logs from the async job have no link to the triggering event, making post-failure diagnosis require manual timestamp correlation across debug logs and log records.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need durable logging inside a transaction that may roll back | Publish `ErrorLog__e` Platform Event via `EventBus.publish()` | PE publish survives rollback; subscriber inserts log in fresh transaction |
| Batch job needs automatic unhandled error capture | Subscribe to `BatchApexErrorEvent` trigger | Platform publishes the event automatically from API v44+ |
| LWC controller needs to show a safe error message | Catch domain exception in controller, wrap message in `new AuraHandledException(msg)` at controller only | `AuraHandledException` thrown in service layer suppresses stack trace and couples transport to business logic |
| Service needs to signal specific failure type | Throw typed `AppException` subclass with `ErrorCode` enum | Enables catch-by-type branching without fragile string parsing |
| Async job logs need to be traceable to originating records | Pass `correlationId` into job constructor, include in every log event | Platform provides no automatic correlation across transaction boundaries |
| Integration HTTP call returns error body | Parse JSON error body for vendor error codes, map to `IntegrationException` with appropriate `ErrorCode` | Raw HTTP status code alone does not distinguish timeout from auth failure from quota exceeded |

---

## Recommended Workflow

1. **Inventory entry points and logging state** — list all Apex entry points (triggers, controllers, REST, Queueable, Batch, Scheduled), confirm API version is v44+ for `BatchApexErrorEvent`, and document what logging mechanism (if any) is already deployed.
2. **Design the Error_Log__c object and ErrorLog__e Platform Event** — agree on required fields: `Level__c`, `Context__c`, `Message__c`, `Stack_Trace__c`, `Payload__c`, `Correlation_Id__c`, `Error_Code__c`. Create the PE and a trigger on it that inserts `Error_Log__c` in the subscriber transaction.
3. **Implement the typed exception hierarchy** — define `AppException` with `ErrorCode` enum, add domain subclasses (`IntegrationException`, `ValidationException`, `ConfigurationException`). Document which codes map to which retry or escalation behavior.
4. **Implement `ErrorLogger` utility class** — single static method that accepts level, context, exception, correlationId, and optional payload JSON, then calls `EventBus.publish()`. Never do DML inside this class.
5. **Add `BatchApexErrorEvent` trigger** — subscribe to `BatchApexErrorEvent`, extract `AsyncApexJobId`, `ExceptionType`, `Message`, `StackTrace`, `Phase`, `JobScope`, and route through `ErrorLogger` so batch failures land in the same `Error_Log__c` store.
6. **Enforce AuraHandledException boundary** — review all Aura/LWC controllers and ensure `AuraHandledException` is constructed only at the controller layer. Service classes should throw `AppException` subclasses. Add this as a code review rule.
7. **Validate** — run the checker script, confirm `Error_Log__c` records appear after both synchronous failures and batch failures in a sandbox, and verify correlation IDs are populated on async log entries.

---

## Review Checklist

- [ ] `ErrorLog__e` Platform Event exists with Level, Context, Message, Stack_Trace, Payload, Correlation_Id fields.
- [ ] `Error_Log__c` is inserted by a trigger on `ErrorLog__e`, not by DML inside error-handling catch blocks.
- [ ] `ErrorLogger` utility uses `EventBus.publish()` exclusively — no DML, no `insert` statement inside it.
- [ ] `AppException` hierarchy defines an `ErrorCode` enum; callers branch by type or code, not by `getMessage()` string parsing.
- [ ] `AuraHandledException` is constructed only in Aura/LWC controller catch blocks, not in service or selector classes.
- [ ] `BatchApexErrorEvent` trigger exists and routes unhandled batch failures into the log store.
- [ ] All Queueable and Batch job constructors accept a `correlationId` parameter and propagate it to log events.
- [ ] Integration error parsing extracts vendor error codes from HTTP response bodies and maps them to `IntegrationException` with appropriate `ErrorCode`.

---

## Salesforce-Specific Gotchas

1. **Platform Event publish can fail silently if the subscriber hits limits** — `EventBus.publish()` returns `Database.SaveResult[]`. If publish succeeds but the subscriber trigger hits CPU or DML limits, the `Error_Log__c` insert fails and the error is lost. Monitor subscriber failures in Setup > Platform Events > Subscriptions and set up `BatchApexErrorEvent` to catch failures in the subscriber itself.
2. **`BatchApexErrorEvent.JobScope` is truncated when `DoesExceedJobScopeMaxLength` is true** — for large batch scopes the comma-separated ID list exceeds the field character limit. Always check `DoesExceedJobScopeMaxLength` before using `JobScope` and fall back to querying `AsyncApexJob` by `AsyncApexJobId` for the full scope.
3. **`AuraHandledException` thrown in service classes loses the Apex stack trace** — the platform treats it as an intentional, user-safe error and does not include server-side stack trace in the Lightning response. Developers who throw it in service layers to "pass the message up" end up unable to diagnose where the exception originated in production.
4. **Typed exceptions require explicit `code` assignment in the constructor** — Apex's generated `Exception` constructors do not call custom constructors. Always use the explicit `AppException(ErrorCode, String)` constructor form; calling `new IntegrationException('message')` without the error code leaves `code` null and breaks downstream branching.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Exception hierarchy design | `AppException` base class, `ErrorCode` enum, domain subclass list |
| `ErrorLog__e` Platform Event schema | Field names, types, and PE configuration |
| `Error_Log__c` field schema | Custom object design with all required fields |
| `ErrorLogger` utility class | Rollback-safe logging implementation |
| `BatchApexErrorEvent` trigger | Automatic batch failure capture pattern |
| Correlation ID threading plan | Which jobs need it, constructor signature, query pattern for log retrieval |
| Code review findings | Controller boundary violations, missing correlation IDs, DML in catch blocks |

---

## Related Skills

- `apex/exception-handling` — use for individual try/catch block guidance, DmlException semantics, `addError` in triggers, and bulk DML SaveResult patterns. This skill (error-handling-framework) covers the org-wide framework design; exception-handling covers the in-method mechanics.
- `apex/platform-events-apex` — use for Platform Event publish/subscribe mechanics, trigger ordering, high-volume events, and replay ID management when building the log subscriber.
- `apex/batch-apex-patterns` — use alongside this skill when the batch job design (scope size, stateful vs stateless, job chaining) needs review alongside the error capture strategy.
- `apex/async-apex` — use when the right remediation for a failure is moving work to Queueable rather than retrying synchronously.
- `lwc/error-handling-in-lwc` — use for the LWC-side pattern of receiving structured error responses from Apex and surfacing them in the UI component.
