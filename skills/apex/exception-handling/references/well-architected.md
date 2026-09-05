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

- **Apex Developer Guide — "Exceptions in Apex" / "Exception Statements"** (`apexdev` L39572–39745),
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf —
  supports the uncatchable-exception rule (`LimitException`, assertion and license failures skip both
  `catch` and `finally`, L39722–39728), the DML-rollback-on-exception statement (L39587–39589), and the
  unhandled-exception email behaviour used in the Questions table (10 per hour per application server,
  duplicates suppressed, never sent for `@AuraEnabled`, L39597–39613).
- **Apex Developer Guide — "Create Custom Exceptions"** (`apexdev` L40139–40284) — supports the naming
  and inheritance rules (`extends Exception`, name ends in `Exception`, L40143–40145), the four
  documented constructor forms (L40151–40170), and the cause-chaining example whose `getCause()` output
  is quoted in `references/gotchas.md` (L40260–40284).
- **Apex Developer Guide — "Bulk DML Exception Handling"** (`apexdev` L9055–9080) — supports the
  `allOrNone` semantics behind the partial-success handler in `references/code-examples.md` and the
  three-attempt retry with re-fired triggers documented as a gotcha.
- **Apex Developer Guide — "Generating Savepoints and Rolling Back Transactions" / "Releasing Savepoints
  and Using Callouts"** (`apexdev` L8679–8790) — supports every claim in the savepoint gotcha: savepoints
  consume DML *statements* not rows (L8691–8696), the two `CalloutException` messages (L8742–8770),
  static variables surviving a rollback (L8692–8693), and the API 60.0 change that releases savepoints at
  `Test.startTest()` / `Test.stopTest()` (L8784–8786).
- **Apex Developer Guide — "Trigger Exceptions"** (`apexdev` L15825–15848) — supports the `addError`
  versus `throw` decision row in the Decision Guidance table: Apex-spawned DML rolls the whole operation
  back but still compiles a full error list, API-spawned bulk DML partial-saves, and an unhandled throw
  marks every record.
- **Apex Developer Guide — "Transaction Finalizers"** (`apexdev` L16284–16360) — supports the async
  section: `FinalizerContext.getResult()` / `getException()`, the five consecutive re-enqueues, and the
  fact that the finalizer runs in a separate transaction so its log write survives.
- **Apex Reference Guide — "Exception Class and Built-In Exceptions"** (`apexrefguide` L214911–215165) —
  supports the common method table (`getCause`, `getLineNumber`, `getMessage`, `getStackTraceString`,
  `getTypeName`, `initCause`, `setMessage`) and the `DmlException` method table including
  `getDmlIndex` ("the original row position of the ith failed row", L215140) and the deprecation of
  `getDmlStatusCode` in favour of `getDmlType`.
- **Apex Reference Guide — `Database.SaveResult` and `Database.Error` classes** (`apexrefguide`
  L148651–148720, L149976–150050) — supports the positional mapping from `SaveResult[]` back to the
  input list and the three-method surface of `Database.Error` used in `CaseIntakeService`.
- **Apex Reference Guide — `Assert` class, `fail()` / `fail(msg)`** (`apexrefguide` L200570–200640) —
  supports the negative-test pattern in `references/code-examples.md` and Anti-Pattern 7: an assertion
  failure cannot be caught by the surrounding `try/catch`.
- **Lightning Web Components Developer Guide — "Handle Errors from Apex"**
  (`lwc_guide` page `apex-error-handling`, L7509–7540),
  https://developer.salesforce.com/docs/platform/lwc/guide/apex-error-handling.html — supports the
  boundary rule quoted in `references/code-examples.md` ("Handle only the errors you expect to see in the
  catch block. The rest should be propagated further") and the statement that an `AuraHandledException`
  client error carries the custom message but not `body.stackTrace`.
- **Metadata API Developer Guide** (`api_meta` L2),
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — supports the
  `apiVersion` 67.0 (Summer '26) used in every `-meta.xml` and in `package.xml`.
- **Salesforce Well-Architected — Reliable / Resilient** — supports the pillar framing at the top of this
  file. UNVERIFIED (2026-09-05): architecture.salesforce.com is not in the grounding corpus; the pillar
  names and framing are carried forward from the skill's original authoring, not re-verified here.
