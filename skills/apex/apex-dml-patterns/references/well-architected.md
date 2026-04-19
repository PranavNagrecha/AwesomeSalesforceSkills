# Well-Architected Notes — Apex DML Patterns

## Relevant Pillars

- **Reliability** — Choosing between `allOrNone=true` and `allOrNone=false` is the primary reliability decision in DML design. All-or-nothing transactions are simpler to reason about but brittle in bulk scenarios. Partial success requires explicit error collection and retry/compensating logic to ensure no data is silently lost.
- **Performance Efficiency** — DML is counted in operations, not rows. Bulkifying into single statements is the foundation of Apex performance. `Database.DMLOptions` assignment rule firing adds per-record processing overhead.
- **Security** — `Database.merge` and `Database.convertLead` respect field-level security. For integrations using running-user context, validate FLS before DML using `SecurityUtils` or `with sharing` classes. `Database.emptyRecycleBin` is a permanent action — gate it with explicit confirmation logic.
- **Operational Excellence** — Error logging via `SaveResult.getErrors()` produces actionable failure records. Avoid swallowing DML errors silently — always surface them in an audit trail.

## Architectural Tradeoffs

**DML statement vs. Database class:** DML statements are simpler and the default for most Apex. Use `Database` class when you need partial success (integration jobs, data migrations), DMLOptions (lead assignment, duplicate bypass), or explicit result inspection per row. Using `Database` class everywhere is over-engineering; using DML statements in integration batch jobs that must tolerate individual row failures is under-engineering.

**Savepoints in complex transactions:** Savepoints enable rollback of a logical unit within a transaction but consume DML operations and add complexity. Use them for multi-step operations where atomicity is a correctness requirement (e.g., insert header + insert lines as a unit). Avoid them for simple single-object DML where allOrNone semantics already provide atomicity.

## Anti-Patterns

1. **DML inside loops** — calling `insert`/`update` inside a for-loop hits the 150-operation limit and causes an uncatchable `LimitException`. Always collect records in a list and issue a single bulk DML call.
2. **Silently swallowing SaveResult errors** — checking `results[i].isSuccess()` without logging or surfacing the errors creates data loss that is invisible to operators. Always write failures to an error log or throw a descriptive exception.
3. **Using Database.merge on unsupported objects** — attempting to merge custom objects or non-mergeable standard objects throws `DmlException` with no compile-time warning, causing runtime failures that are difficult to diagnose.

## Official Sources Used

- Apex Developer Guide — DML Statements: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_dml.htm
- Apex Developer Guide — Database Class Methods: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_dml_database.htm
- Apex Reference Guide — Database Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_database.htm
- Apex Reference Guide — SaveResult: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_database_saveresult.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
