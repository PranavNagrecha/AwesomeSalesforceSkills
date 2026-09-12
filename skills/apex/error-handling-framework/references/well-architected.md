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

Each bullet names the claim in this package it supports. `apexdev L<n>` line
numbers are into the Apex Developer Guide text captured for this skill on
2026-09-12.

- Apex Developer Guide — "Exceptions that Can't be Caught" (`apexdev L39721-39728`): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_exception_definition.htm — supports Gotcha 7's claim that `System.LimitException` cannot be caught and that `catch` *and* `finally` blocks are skipped, which is why a `try/catch` logger records nothing for governor-limit failures.
- Apex Developer Guide — "Create Custom Exceptions" and the inheritance-tree example (`apexdev L40139-40180`): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_exception_custom.htm — supports the typed hierarchy in Pattern 2 and `references/code-examples.md` § 2: the class must extend `Exception` and be named `*Exception`, a `virtual` base with plain leaves is the documented shape, and the four generated constructor forms are the documented ways to construct one.
- Apex Developer Guide — "Common Exception Methods" and the `DmlException` accessors (`apexdev L39973-39981`, `L40018-40023`): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_exception_methods.htm — supports storing `getTypeName`, `getLineNumber`, `getStackTraceString` rather than message text, and the per-row failure record built from `getNumDml` / `getDmlId` / `getDmlMessage` / `getDmlFieldNames`.
- Apex Developer Guide — "Bulk DML Exception Handling" and "Returned Database Errors" (`apexdev L7583-7586`, `L8427-8443`, `L9055-9063`): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_dml_bulk_exceptions.htm — supports the partial-success design: `allOrNone = false` does not throw, returns `Database.SaveResult` with a list of `Database.Error`, and leaves the caller responsible for walking the results.
- Apex Developer Guide — "Generating Savepoints and Rolling Back Transactions" (`apexdev L8679-8697`): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_transaction_control.htm — supports Gotcha 11 (rollback does not clear Ids on records inserted after the savepoint) and the one-savepoint-per-transaction budget, since each savepoint spends a DML statement.
- Apex Developer Guide — "Transaction Finalizers" and the Logging Finalizer example (`apexdev L16285-16303`, `L16336-16344`, `L16364-16430`, `L16533-16534`): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_finalizers.htm — supports the rollback-safe async logging path in `references/code-examples.md` § 5: the Finalizer runs in a separate Apex and Database transaction, `getResult` returns `SUCCESS` or `UNHANDLED_EXCEPTION`, the guide's own example commits a log after a deliberate limit error, and a finalizer can still fail to execute if the request is terminated unexpectedly.
- Apex Developer Guide — "Firing Platform Events from Batch Apex" (`apexdev L17855-17867`, `L17911-17930`): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_platform_events.htm — supports Concept 2: `BatchApexErrorEvent` is available from API v44.0, the class must implement `Database.RaisesPlatformEvents`, events fire for uncatchable exceptions including `LimitException`, and `Test.getEventBus().deliver()` is the documented test hook.
- Apex Developer Guide — "Execution Governors and Limits" (`apexdev L19598-19599`, `L19635`): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm — supports Gotcha 10: publish-immediately events have their own 150-call ceiling while publish-after-commit events count against the transaction's DML statements, so the two behaviors have different budgets as well as different durability.
- Apex Developer Guide — async rollback behavior (`apexdev L15961`, `L18081`): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm — supports Gotcha 9 and Anti-Pattern 7: Queueable and `@future` jobs queued by a transaction that rolls back are never processed, so async is not an escape hatch from a failing transaction.
- Apex Developer Guide — JSON serialization versioned behavior (`apexdev L36804-36806`): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_json_json.htm — supports Gotcha 8 and Anti-Pattern 8: from API 63.0, serializing a custom or built-in exception throws `Type unsupported in JSON`, so log payloads must carry extracted scalars.
- Platform Events Developer Guide — BatchApexErrorEvent field reference: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_error_batch.htm — supports Gotcha 2's `DoesExceedJobScopeMaxLength` / `JobScope` truncation claim, which the Apex Developer Guide does not cover.
- Platform Events Developer Guide — Publish Event Messages with Apex: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_publish_apex.htm — the authority for the open question in Gotcha 10: what an event configured to publish after commit does when the publishing transaction rolls back.
- Salesforce Well-Architected — Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — supports the pillar framing at the top of this file.
