# Well-Architected Notes — Error Handling Framework

## Relevant Pillars

### Reliability

A well-designed error handling framework is the primary mechanism by which Apex code achieves operational reliability. Log durability — ensuring that a failure record survives the transaction that failed — directly determines whether an org can detect, diagnose, and recover from production failures. The Platform Event log pattern eliminates the most common cause of lost error records: DML rollback. The `BatchApexErrorEvent` subscriber provides a platform-guaranteed safety net so that no batch failure is silently discarded. Typed exceptions with error codes enable callers to distinguish retryable from non-retryable failures, which is the foundation of any retry or circuit-breaker strategy.

Reliability anti-patterns this skill targets: swallowed exceptions that silently succeed, logging that disappears on rollback, and catch-all handlers that prevent the platform's own error propagation from surfacing real defects.

### Operational Excellence

Structured logging with consistent fields (`Level__c`, `Context__c`, `Correlation_Id__c`, `Stack_Trace__c`) makes `Error_Log__c` queryable by monitoring dashboards and support engineers without relying on debug log parsing. Correlation IDs thread async job failures back to originating records, cutting mean time to diagnosis for batch and queueable failures. A single `ErrorLogger` utility class ensures log format consistency across all Apex entry points rather than ad hoc `System.debug` calls that only appear in transient debug logs.

### Security

The `AuraHandledException` boundary rule is a security concern, not just a code quality concern. Exposing raw `DmlException.getMessage()` or `QueryException.getMessage()` in the Lightning response discloses internal object names, field names, and query structure to the browser. Constructing `AuraHandledException` with only correlation ID references and user-safe messages prevents information disclosure. The `Payload__c` field on `Error_Log__c` should be treated as a sensitive field with appropriate FLS restrictions since it may contain record IDs and request parameters.

### Scalability

The rollback-safe logging pattern must remain bulk-safe. `ErrorLogger.logException()` publishes one event per call. In contexts where hundreds of failures can occur in a single execution (batch execute with 200-record scope, bulk trigger), the implementation must collect all failure events and publish them in a single `EventBus.publish(list)` call rather than looping with individual publishes. A single bulk publish counts as one DML statement; 200 individual publishes exhaust DML limits. Review all call sites to confirm bulk-safe invocation.

## Architectural Tradeoffs

**Rollback safety vs immediate DML simplicity:** Publishing to a Platform Event and relying on a subscriber trigger is more complex than inserting `Error_Log__c` directly. The additional indirection is justified for any context where the enclosing transaction may fail. For genuinely read-only or non-transactional contexts (e.g., a Lightning controller method that only queries data), direct DML for logging is simpler and acceptable.

**Typed exceptions vs string message parsing:** A typed exception hierarchy requires upfront investment in class design and deployment. It pays off when multiple callers need to branch on failure type. For simple scripts or single-use Apex classes with one caller, typed exceptions add overhead without proportional benefit. The framework design should be adopted for service-layer classes with multiple callers, not mandated for every utility method.

**Centralized `ErrorLogger` vs per-class logging:** A single utility class creates a deployment dependency: every class that logs must have `ErrorLogger` deployed and accessible. In packages or orgs with complex deployment sequencing, this can create dependency issues. Document `ErrorLogger` as a foundation class that must be deployed before any class that depends on it, and include it in the deployment manifest explicitly.

**`BatchApexErrorEvent` vs per-class try/catch in execute:** The `BatchApexErrorEvent` subscriber catches unhandled exceptions — it does not replace per-class catch blocks for expected, recoverable failures. A batch that can partially recover from specific record errors (e.g., skipping records with missing data and continuing) still needs per-record try/catch inside `execute`. The `BatchApexErrorEvent` is a safety net for the unexpected, not a substitute for deliberate error handling.

## Anti-Patterns

1. **DML logging inside catch blocks** — Inserting `Error_Log__c` via `insert` inside a catch block couples the log write to the failing transaction. If the transaction rolls back (as it often does at the point of exception), the log is lost. The platform does not provide any guarantee that DML inside a catch block survives a partial rollback. Replace with `EventBus.publish()` to `ErrorLog__e`.

2. **`AuraHandledException` as a service-layer exception base** — Some teams make `AuraHandledException` the parent class for all custom exceptions to "ensure the message reaches the UI." This suppresses full Apex stack traces in Lightning responses, couples service classes to the UI transport layer, and prevents exception-type branching in callers below the controller. The correct separation is: service classes throw typed `AppException` subclasses; the controller catches them and wraps the message in a new `AuraHandledException` at the boundary.

3. **Correlation ID as an afterthought** — Adding correlation ID support to an existing async framework after deployment requires changing constructor signatures on all existing Queueable and Batch classes, which is a breaking change for any callers. Design correlation ID threading into the job constructor signature from day one so it can be populated at enqueue time. An empty string is a safer default than null for the `correlationId` parameter, as it avoids null concatenation issues in log messages.

4. **One-event-per-failure in bulk contexts** — Calling `ErrorLogger.logException()` inside a loop over a 200-record batch scope publishes up to 200 individual Platform Events, consuming 200 DML statements. Apex's DML limit per transaction is 150. Refactor bulk error collection: accumulate all `ErrorLog__e` events in a list during the loop, publish the list once after the loop with a single `EventBus.publish(eventList)` call.

## Official Sources Used

- Apex Developer Guide — Custom Exceptions: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_exception_custom.htm
- Apex Developer Guide — AuraHandledException: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_exception_methods.htm
- Platform Events Developer Guide — BatchApexErrorEvent: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_error_batch.htm
- Platform Events Developer Guide — Publish Events with Apex: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_publish_apex.htm
- Apex Developer Guide — Exception Class: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_exception_methods.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
