# Well-Architected Notes — Exception Handling

## Relevant Pillars

### Reliability

Exception handling is primarily a Reliability concern in Salesforce because unhandled faults can roll back user transactions, scheduled jobs, or integration work. Good error classification separates expected business failures from unexpected system failures and avoids silently corrupting data.

Tag findings as Reliability when:
- a trigger or synchronous service can fail without a clear business message
- bulk DML uses all-or-none behavior where partial success is required
- one bad callout or validation error aborts processing for all records in scope

### Operational Excellence

Operational Excellence matters because exceptions are only useful if support teams can diagnose them. Logging once with context, correlation IDs, operation names, and record IDs creates an audit trail that is actionable during incidents.

Tag findings as Operational Excellence when:
- errors are only written to debug logs
- multiple layers log the same exception and create noisy duplicates
- there is no durable record of background-job or integration failures

## Architectural Tradeoffs

- **Fail fast vs partial success:** `update records;` is simpler and preserves transactional integrity, but `Database.update(records, false)` is often the safer design for bulk or integration workloads.
- **User-safe messages vs diagnostic detail:** LWC and Aura users need clean messages, but operations teams still need the original exception context somewhere durable.
- **Centralized logging vs local convenience:** Logging in every catch block feels safe but creates duplicate noise; centralized boundary logging is usually better.

## Anti-Patterns

1. **Generic catch-and-return** — swallowing an exception and returning `null`, `false`, or an empty list hides defects and produces ambiguous caller behavior.
2. **UI-specific exceptions in service classes** — throwing `AuraHandledException` from deep service logic couples business logic to presentation concerns.
3. **No `SaveResult` inspection on partial DML** — partial failures become invisible even though the code appears more resilient.

## Official Sources Used

- Apex Developer Guide — exception handling behavior and trigger exception guidance
- Apex Reference Guide — `Exception`, `DmlException`, and related API methods
- Salesforce Well-Architected Overview — reliability and operational excellence framing
