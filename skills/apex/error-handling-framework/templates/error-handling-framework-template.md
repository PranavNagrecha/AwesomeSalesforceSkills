# Error Handling Framework — Work Template

Use this template when designing, implementing, or reviewing an Apex error handling framework for an org. Fill in each section before writing code.

---

## Scope

**Skill:** `apex/error-handling-framework`

**Request summary:** (describe what the user or task requires — e.g., "design org-wide error logging," "add rollback-safe logging to existing batch jobs," "review controller error handling for AuraHandledException boundary violations")

---

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding.

**Entry points in scope:**
- [ ] Trigger handlers
- [ ] Aura/LWC controllers (`@AuraEnabled` methods)
- [ ] REST resources (`@RestResource`)
- [ ] Queueable implementations
- [ ] Batch Apex classes
- [ ] Scheduled Apex
- [ ] Invocable methods (`@InvocableMethod`)

**API version:** ______ (must be v44+ for BatchApexErrorEvent)

**Existing logging mechanism:**
- [ ] None currently deployed
- [ ] `Error_Log__c` custom object exists — describe current fields: ______
- [ ] Platform Event for logging already exists — PE API name: ______
- [ ] External observability tool (Datadog, Splunk, etc.) — describe integration: ______

**Partial success required?**
- [ ] Yes — `Database.SaveResult[]` paths are in scope
- [ ] No — all-or-nothing transactions only

**Correlation ID required?**
- [ ] Yes — async jobs need linkage to originating records
- [ ] No — synchronous contexts only

**Known constraints:**
- Org edition / limits relevant to Platform Events:
- Existing exception classes or patterns to preserve:
- Deployment sequencing constraints (packages, namespaces):

---

## Design Decisions

### Exception Hierarchy

List the `AppException` subclasses needed for this org's domains:

| Class Name | Domain | ErrorCodes it uses |
|---|---|---|
| `ValidationException` | record validation, field rules | REQUIRED_FIELD_MISSING, DUPLICATE_VALUE |
| `IntegrationException` | external API callouts | CALLOUT_TIMEOUT, INTEGRATION_AUTH_FAILURE |
| `ConfigurationException` | missing custom metadata or settings | CONFIGURATION_MISSING |
| (add rows as needed) | | |

### Error_Log__c Object Schema

Confirm required fields are present or planned:

| Field API Name | Type | Notes |
|---|---|---|
| `Level__c` | Picklist | INFO, WARN, ERROR, FATAL |
| `Context__c` | Text(255) | ClassName.methodName |
| `Message__c` | Text Area(32768) | Exception message |
| `Stack_Trace__c` | Long Text Area(131072) | Full Apex stack trace |
| `Payload__c` | Long Text Area(131072) | JSON context payload |
| `Correlation_Id__c` | Text(255) | Async job ID or user-generated ID |
| `Error_Code__c` | Text(100) | AppException.ErrorCode enum value |

### Platform Event Schema (ErrorLog__e)

Mirrors Error_Log__c fields. Confirm matching fields exist on the PE definition.

### Correlation ID Strategy

For each async entry point in scope, describe how the correlation ID is sourced:

| Entry Point | Correlation ID Source | Threading Mechanism |
|---|---|---|
| Queueable | caller generates before `System.enqueueJob()` | passed in constructor |
| Batch started by code | caller generates before `Database.executeBatch()` | passed in constructor |
| Batch started by Flow | `$Record.Id + NOW()` from Flow | `@InvocableMethod` parameter |
| Trigger handler | `Trigger.operationType + UserInfo.getUserId()` | passed to service method |

---

## Approach

**Pattern(s) from SKILL.md that apply:**
- [ ] Platform Event Log Publisher (rollback-safe logging)
- [ ] Typed Domain Exception Hierarchy
- [ ] BatchApexErrorEvent Subscriber
- [ ] Correlation ID Threading in Queueable and Batch
- [ ] AuraHandledException Boundary Enforcement

**Reason for pattern selection:** (explain which entry points and failure modes drove the choice)

---

## Implementation Checklist

Work through these in order:

- [ ] `AppException` base class with `ErrorCode` enum defined and deployed
- [ ] Domain exception subclasses deployed (`ValidationException`, `IntegrationException`, etc.)
- [ ] `ErrorLog__e` Platform Event created in org with all required fields
- [ ] `Error_Log__c` custom object has all required fields with appropriate FLS (restrict `Payload__c` and `Stack_Trace__c`)
- [ ] `ErrorLog__e` subscriber trigger deployed — inserts `Error_Log__c` in bulk using single DML
- [ ] `ErrorLogger` utility class deployed — uses `EventBus.publish()` only, no direct DML
- [ ] `BatchApexErrorEvent` trigger deployed — checks `DoesExceedJobScopeMaxLength` before using `JobScope`
- [ ] All Queueable job constructors accept `correlationId` parameter
- [ ] All Batch job constructors accept `correlationId` parameter
- [ ] All `@AuraEnabled` controller methods: `AuraHandledException` constructed only in controller, not in service classes
- [ ] Integration error parsing: HTTP response bodies parsed for vendor error codes, mapped to `IntegrationException` with `ErrorCode`
- [ ] Checker script run: `python3 scripts/check_error_handling_framework.py --manifest-dir <path>`

---

## Review Checklist

Copy from SKILL.md and tick as verified:

- [ ] `ErrorLog__e` Platform Event exists with Level, Context, Message, Stack_Trace, Payload, Correlation_Id fields
- [ ] `Error_Log__c` is inserted by a trigger on `ErrorLog__e`, not by DML inside error-handling catch blocks
- [ ] `ErrorLogger` utility uses `EventBus.publish()` exclusively — no DML, no `insert` statement inside it
- [ ] `AppException` hierarchy defines an `ErrorCode` enum; callers branch by type or code, not by `getMessage()` string parsing
- [ ] `AuraHandledException` is constructed only in Aura/LWC controller catch blocks, not in service or selector classes
- [ ] `BatchApexErrorEvent` trigger exists and routes unhandled batch failures into the log store
- [ ] All Queueable and Batch job constructors accept a `correlationId` parameter and propagate it to log events
- [ ] Integration error parsing extracts vendor error codes from HTTP response bodies and maps them to `IntegrationException`

---

## Notes and Deviations

Record any deviations from the standard framework pattern and the rationale:

- (e.g., "Org is on API v43 — BatchApexErrorEvent not available; compensating with try/catch in all batch execute methods")
- (e.g., "External observability tool already deployed — ErrorLogger routes to Datadog webhook instead of ErrorLog__e")
- (e.g., "Payload__c field deliberately omitted from Error_Log__c for data residency compliance — correlation ID + Context__c used for diagnosis instead")
