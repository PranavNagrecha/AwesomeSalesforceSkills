# Gotchas — Error Handling Framework

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: ErrorLog__e Subscriber Trigger Hits Its Own Governor Limits and Fails Silently

**What happens:** The `ErrorLog__e` subscriber trigger inserts `Error_Log__c` records. If a single batch chunk generates hundreds of failures (e.g., a 200-record scope where all 200 records fail), the subscriber trigger must insert 200 `Error_Log__c` records. If that insert hits DML limits (150 statements) or CPU time limits, the subscriber transaction fails. The Platform Event is consumed but the `Error_Log__c` records are never written. No exception surfaces to the publishing context.

**When it occurs:** High-volume batch failures, cascading trigger logic on `Error_Log__c` inserts, or subscriber triggers that perform additional DML or SOQL per record. The subscriber failure is visible in Setup > Platform Events > Subscriptions under "Failed Deliveries," but only if someone is monitoring it — there is no automatic alert.

**How to avoid:** Keep the subscriber trigger lean: bulk-insert `Error_Log__c` records using a single DML operation (`insert logs`), ensure no after-insert triggers on `Error_Log__c` perform expensive operations, and set up a monitoring alert on the Platform Event subscription's failed delivery count. Consider using `Database.insert(logs, false)` in the subscriber to allow partial success rather than failing the entire batch on one bad record.

---

## Gotcha 2: BatchApexErrorEvent.JobScope Is Truncated and Silently Incomplete

**What happens:** `BatchApexErrorEvent.JobScope` contains the comma-separated list of record IDs in the failed scope chunk. When the failed scope contains many records, this String may exceed the field's character limit. In that case, `DoesExceedJobScopeMaxLength` is set to `true` and `JobScope` is truncated mid-list. Using the truncated `JobScope` to query the affected records yields an incomplete result set without any error or warning.

**When it occurs:** Any batch `execute` scope that fails and contains enough record IDs that the comma-separated string exceeds the Platform Event field limit. The default batch scope size of 200 records is often enough to trigger this.

**How to avoid:** Always check `evt.DoesExceedJobScopeMaxLength` before processing `evt.JobScope`. When it is `true`, query `AsyncApexJob WHERE Id = :evt.AsyncApexJobId` to retrieve the job metadata, and if complete scope recovery is needed, re-query the source data using the original batch query's criteria and the job's `NumberOfErrors` and `JobItemsProcessed` to identify the affected window. Store the `AsyncApexJobId` in `Error_Log__c.Correlation_Id__c` so the job can always be cross-referenced.

---

## Gotcha 3: Custom Exception Constructor Must Explicitly Set the Error Code Field

**What happens:** Apex auto-generates several constructors for custom exception classes that extend `Exception`. The inherited constructors (`new MyException('message')`, `new MyException(cause)`, etc.) do not call a custom constructor defined in the class. If the framework's typed exception class defines an `AppException(ErrorCode code, String message)` constructor and sets `this.code = code`, calling the inherited no-arg or message-only constructor skips that assignment entirely. `exception.code` is null, and any downstream code that branches on `exception.code` produces a `NullPointerException` or falls through to the default case silently.

**When it occurs:** Any place a developer throws a typed exception using the implicit inherited constructor form: `throw new IntegrationException('Connection refused');` — forgetting to use the `(ErrorCode, String)` constructor form.

**How to avoid:** Override all commonly used inherited constructors in `AppException` and ensure each one sets a default `code` (e.g., `ErrorCode.UNEXPECTED`) when no explicit code is provided. Add a static code analysis rule (PMD custom rule or a checker script) that flags `throw new *Exception(String)` without an `ErrorCode` argument in service or integration classes.

---

## Gotcha 4: Publishing ErrorLog__e Inside a Future Method Fails at API Limits

**What happens:** Platform Events published inside `@future` methods count against the org's daily Platform Event publish limits. If the org is already near the daily limit (300,000 events per 24 hours for standard orgs), `EventBus.publish()` inside a `@future` logger will fail. The `Database.SaveResult` will have `isSuccess() == false`, but since `@future` methods cannot throw `AuraHandledException` back to a calling context and their debug output may not be monitored, the failure is invisible.

**When it occurs:** High-volume orgs with many async jobs all publishing to the same `ErrorLog__e` topic, especially during batch processing windows.

**How to avoid:** Monitor the Platform Event daily publish limit via the `PlatformEventUsageMetric` entity (available in API v47+). Consider routing non-critical INFO-level logs to a direct DML path (when the transaction is expected to commit) and reserving `EventBus.publish()` for ERROR and FATAL levels where rollback safety is critical. Consolidate log events where possible: batch multiple failures into a single `Payload__c` JSON array rather than publishing one event per failure record.

---

## Gotcha 5: AuraHandledException Message Is Exposed Verbatim to the Browser

**What happens:** The message passed to `new AuraHandledException(msg)` is serialized into the Lightning component event payload and is visible in browser developer tools network responses. Any message that contains internal identifiers, stack trace fragments, SOQL query strings, field names, or user data creates an information disclosure vulnerability. Developers who pass `exception.getMessage()` directly to `AuraHandledException` may unknowingly expose query errors containing field names that reveal the data model, or DML errors that expose record IDs.

**When it occurs:** Whenever `getMessage()` from a `DmlException`, `QueryException`, or system exception is passed directly as the `AuraHandledException` message without sanitization.

**How to avoid:** Always construct `AuraHandledException` with a user-safe, human-authored message string. Include only a correlation ID reference for support engineers: `'An error occurred processing your request. Reference: ' + correlationId`. Never pass `e.getMessage()`, `e.getStackTraceString()`, or query result content directly into the `AuraHandledException` message.

---

## Gotcha 6: Correlation ID Lost When Batch Is Invoked from Flow or Process Builder

**What happens:** When a Batch job is started by a Flow or Process Builder action, there is no mechanism to pass a correlation ID from the Flow into the Batch constructor. The Batch constructor called by the invocable method receives no context about the originating record, user, or Flow interview. Log entries from the batch have `Correlation_Id__c` null, making them impossible to link to the triggering record without timestamp-based guessing.

**When it occurs:** Any `@InvocableMethod` or `@AuraEnabled` method that starts a Batch job from a Flow, LWC, or Quick Action where the originating record context is meaningful for support diagnosis.

**How to avoid:** Expose the correlation ID as a parameter on the `@InvocableMethod` and require the Flow to pass it (the Flow can compute it from `$Record.Id` concatenated with `NOW()`). Alternatively, store a `Correlation_Id__c` field on the triggering record before the job starts and have the Batch `start()` method read it from the query — making the correlation ID queryable from the source data rather than requiring it to be passed in memory.
