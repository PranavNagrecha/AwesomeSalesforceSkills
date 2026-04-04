# Gotchas — Custom Logging and Monitoring

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Direct DML Log Inserts Are Rolled Back with the Transaction

**What happens:** A developer adds `Database.insert(new Log__c(...))` in a catch block thinking the error is captured regardless of what happens to the transaction. When the transaction rolls back (e.g., after a Savepoint release or unhandled exception), the `Log__c` record is deleted along with everything else.

**When it occurs:** Any logging in a catch block inside a transaction that subsequently rolls back.

**How to avoid:** Use `EventBus.publish(new Log_Event__e(...))` for error-level logs where capture must survive rollback. PE publishes are outside the transaction boundary. The subscriber trigger inserts `Log__c` in a new transaction, which is permanent.

---

## Gotcha 2: Calling flush() With Log DML in a Callout Transaction

**What happens:** The `flush()` method (which does DML) is called before a callout in the same transaction. The callout then fails with `System.CalloutException: You have uncommitted work pending`.

**When it occurs:** When `flush()` is called early in a method that later makes an external callout.

**How to avoid:** Do not flush the log buffer before callouts. Either flush after the callout (last operation in the method), or use Platform Events for all logging in callout-containing transactions (PE publish does not count as "uncommitted work" for the callout restriction).

---

## Gotcha 3: Log__c Long Text Fields Are Not Filterable

**What happens:** An admin tries to build a report filtering on `Message__c` (Long Text Area) or sorts logs by message content. The report is extremely slow or times out.

**When it occurs:** Any SOQL query or report that uses `WHERE Message__c LIKE '%error%'` or similar filters on a Long Text Area field.

**How to avoid:** Design reports and queries to filter on indexed fields: `Level__c`, `Source__c` (standard text), `Retention_Date__c` (date, indexed), or `Correlation_Id__c` (External ID, indexed). Use full-text search (SOSL) if searching message content is required.

---

## Gotcha 4: Logger Singleton State Persists Across Test Methods

**What happens:** In test classes that use `@TestSetup` or multiple `@isTest` methods, the logger singleton is instantiated once and accumulates buffer entries across test methods. The second test method's flush() inserts records from both methods.

**When it occurs:** When the `LoggerService.instance` static variable is not reset between test methods.

**How to avoid:** Add a `reset()` static method on LoggerService that clears the buffer and nulls the instance: `public static void reset() { instance = null; }`. Call `LoggerService.reset()` in test `@TestSetup` or at the start of each test method.
