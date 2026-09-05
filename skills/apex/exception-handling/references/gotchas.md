# Gotchas — Exception Handling

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Trigger Exceptions Roll Back More Than You Expect

**What happens:** A developer catches one exception in a trigger helper, logs it, then rethrows a different generic exception. The entire save fails, including records that were otherwise valid in the same transaction.

**When it occurs:** Trigger logic throws unexpectedly during insert, update, delete, undelete, or cross-object DML from the same transaction.

**How to avoid:** Use `addError` for expected business validation on specific records. Let unexpected faults surface with enough context to debug, but do not confuse that with record-level validation behavior.

---

## `Database.*(..., false)` Moves Failures Into `SaveResult[]`

**What happens:** The code switches from `update records;` to `Database.update(records, false)` for bulk resilience, but still assumes an exception will be thrown when a row fails.

**When it occurs:** Partial success DML is used and the code never loops through `Database.SaveResult[]`.

**How to avoid:** Always inspect every `SaveResult`, record the failed IDs and messages, and make the return type or log structure explicit about partial success.

---

## `AuraHandledException` Can Hide The Real Root Cause

**What happens:** A deep service layer throws `AuraHandledException` directly. The message reaches the UI, but the platform stack trace and operational context are lost.

**When it occurs:** Teams use UI-specific exception types in reusable services shared by LWC, Batch, Flow-invocable methods, and REST resources.

**How to avoid:** Keep `AuraHandledException` at the controller boundary. Throw custom domain exceptions in lower layers, then translate them at the last user-facing hop.

---

## `System.debug` Is Not Production Error Handling

**What happens:** A catch block looks active because it prints the exception, but production troubleshooting has no durable record and the transaction continues in a bad state.

**When it occurs:** Teams rely on developer-console debugging habits in deployed Apex.

**How to avoid:** Log through a real mechanism such as a custom log object, platform event, or observability integration, and decide explicitly whether the exception should be rethrown.

---

## The Governor-Limit Exception Skips Your `finally` Block Too

**What happens:** A method takes a savepoint, opens a stream, or increments a static "in progress" flag,
and cleans up in `finally`. The transaction blows a governor limit. The `finally` block never runs and
the cleanup never happens.

**When it occurs:** Any `System.LimitException` — heap, CPU, SOQL query count, rows retrieved — and also
assertion failures and license exceptions. The guide is explicit: "Some special types of built-in
exceptions can’t be caught… When exceptions are uncatchable, catch blocks, as well as finally blocks if
any, aren’t executed" (Apex Developer Guide, `apexdev` L39722–39728).

**How to avoid:** Never make correctness depend on a `finally` running. Check headroom *before* the
expensive call with the `Limits` class rather than trying to recover after it, and put anything that
must survive on the platform-event path described in `apex/debug-and-logging`. Related: an
`ApplicationLogger.flush()` in a `finally` is the exact write that a `LimitException` discards.

---

## A Custom Exception That Does Not End In `Exception` Does Not Compile

**What happens:** `public class CaseIntakeError extends Exception {}` fails to save. So does a `throw`
of a bare type name — `throw CaseIntakeException;` — because `throw` needs an *object*.

**When it occurs:** Any hand-written or generated exception class. The rule is stated once and easy to
miss: "extend the built-in `Exception` class and make sure your class name ends with the word
Exception" (`apexdev` L40143–40145). `throw` takes an exception object — `throw exceptionObject;`
(`apexdev` L39653–39657) — so the `new` is not optional.

**How to avoid:** Name it `<Domain>Exception`, extend `Exception`, and construct it with one of the four
documented forms: no argument, a `String` message, an `Exception` cause, or `String` + cause
(`apexdev` L40151–40170). Anything you want to carry beyond the message is a public field on the
subclass, set after construction — see `references/code-examples.md`, `CaseIntakeException.of(...)`.

---

## Rethrowing Without The Cause Deletes The Stack Trace, Silently

**What happens:** A catch block does `throw new ServiceException(e.getMessage());`. The message survives.
`getCause()` on the new exception returns `null`, `getStackTraceString()` points at the rethrow line, and
the original failure's line number is gone from the log.

**When it occurs:** Every wrap that uses the single-`String` constructor. The guide demonstrates the
correct shape — `throw new MerchandiseException('Merchandise item could not be inserted.', e);` — and
shows the resulting `Cause:` line in the debug output (`apexdev` L40260–40284). Where the constructor
already ran, `initCause(Exception)` "sets the cause for this exception, if one hasn’t already been set"
(Apex Reference Guide, `apexrefguide` L215119–215120).

**How to avoid:** Use the two-argument constructor, or `initCause`. Assert on it: a test that checks
`e.getCause() instanceof DmlException` is what stops the next refactor from dropping the chain.

---

## `getDmlIndex(i)` And The Loop Counter `i` Are Different Numbers

**What happens:** Code loops `for (Integer i = 0; i < e.getNumDml(); i++)` and then reads
`inputRecords[i]` to name the offending record. With one failure at position 137 of 200, it names
record 0.

**When it occurs:** Every all-or-none `DmlException` where the failures are not the first rows.
`getNumDml` "returns the number of failed rows"; `getDmlIndex(i)` "returns the original row position of
the ith failed row" (`apexrefguide` L215140, L215160). The loop counter enumerates *failures*; the
return value enumerates *rows*.

**How to avoid:** Always dereference the input list with `e.getDmlIndex(i)`, never with `i`. The
positional guarantee is different again on the partial-success path: there, `Database.SaveResult[]`
lines up one-for-one with the input, "the first element in the SaveResult array matches the first
element passed in the sObject array" (`apexrefguide` L149984–149987), so the loop counter *is* the row.

---

## `addError` And `throw` Have Opposite Blast Radii In A Trigger

**What happens:** A developer swaps `record.addError('...')` for `throw new ValidationException('...')`
to "make it cleaner". Every record in the operation now fails, including the ones that were fine, and
the user sees one error instead of a list.

**When it occurs:** On the `addError` path, "If the trigger was spawned by a DML statement in Apex, any
one error results in the entire operation rolling back. However, the runtime engine still processes
every record in the operation to compile a comprehensive list of errors"; when the same trigger is
spawned by a bulk API call, "the runtime engine sets aside the bad records and attempts to do a partial
save" (`apexdev` L15832–15836). A thrown exception has no such nuance: "If a trigger ever throws an
unhandled exception, all records are marked with an error and no further processing takes place"
(`apexdev` L15844).

**How to avoid:** `addError` for anything a user can fix, `throw` only for defects and system faults.
Put it in a **before** trigger — "Users experience less of a delay in response time if errors are added
to before triggers" (`apexdev` L15829). Note the message is HTML-escaped by default, and the `escape`
parameter of `addError(errorMsg, escape)` "is ignored in both Lightning Experience and the Salesforce
mobile app" (`apexrefguide` L232233–232236) — you cannot render markup in a modern UI.

---

## The Partial-Save Retry Refires Your Triggers, Then Gives Up After Three Attempts

**What happens:** A partial-success load appears to work, but the trigger's side effects (an outbound
notification, a counter increment) fire two or three times for the same records. Or the whole load dies
with "Too many batch retries in the presence of Apex triggers and partial failures."

**When it occurs:** Whenever `allOrNone` is `false` or the call came from the API. The engine makes up to
three passes — the second including only rows that did not error, the third only rows clean after two —
and "Apex triggers are fired for the first save attempt, and if errors are encountered for some records
and subsequent attempts are made to save the subset of successful records, triggers are refired on this
subset of records." Governor limits are reset to their original state before each retry
(`apexdev` L9065–9080).

**How to avoid:** Make trigger side effects idempotent, or move them behind a `TriggerControl` guard
(`templates/apex/TriggerControl.cls`) keyed on record Id rather than on "has this handler run". Do not
read the retry as a reason to reduce batch size — the third failure is caused by errors, not volume.

---

## `Database.setSavepoint()` Spends A DML Statement, And Blocks The Next Callout

**What happens:** A service that takes a savepoint per record exhausts the DML statement limit long
before it exhausts the row limit. Or the compensating callout in the catch block fails with
`System.CalloutException` instead of notifying anyone.

**When it occurs:** "Each savepoint you set counts against the governor limit for DML statements"
(`apexdev` L8691), and `Database.rollback(Savepoint)` / `Database.setSavepoint()` "don’t count against
the DML row limit, but count toward the DML statement limit… This behavior applies to all API versions"
(`apexdev` L8695–8696). For the callout: an active savepoint produces "All active Savepoints must be
released before making callouts." and pending DML produces "You have uncommitted work pending. Please
commit or rollback before calling out." (`apexdev` L8742–8770).

**How to avoid:** One savepoint per transaction, taken at the service boundary — `BaseService`
(`templates/apex/BaseService.cls`) already does this. Before any callout in a catch block:
`Database.rollback(sp)` then `Database.releaseSavepoint(sp)`, in that order (`apexdev` L8730–8741). Two
more traps in the same list: static variables are **not** reverted by a rollback (`apexdev`
L8692–8693), and an sObject inserted after the savepoint keeps its Id after the rollback, so reusing
that variable for a second insert fails (`apexdev` L8697–8701). Deeper treatment lives in
`apex/apex-savepoint-and-rollback` and `apex/callout-and-dml-transaction-boundaries`.

---

## No Exception Email Is Ever Sent For An `@AuraEnabled` Failure

**What happens:** A team relies on unhandled-exception emails as its production alerting. LWC users
report errors for weeks and nobody's inbox ever mentions them.

**When it occurs:** "Emails aren’t sent for exceptions encountered with anonymous Apex executions or
with Apex methods accessed by Aura components and Lightning web components via the `@AuraEnabled`
annotation" (`apexdev` L39609–39610). Even where the email *is* sent, it goes by default to "the
developer specified in the LastModifiedBy field on the failing class or trigger", duplicates are
suppressed after the first, and delivery is "limited to 10 emails per hour, per application server"
(`apexdev` L39597–39613).

**How to avoid:** Treat the email as a courtesy, not a channel. Every `@AuraEnabled` catch block must
write to a durable sink before it throws — the pattern is in `references/code-examples.md`
(`CaseIntakeController.toAura`), and the sink itself is `apex/debug-and-logging`'s subject.

---

## The Exception That Killed Your Queueable Is Only Readable From The Finalizer

**What happens:** A Queueable wraps its whole `execute` body in `try/catch (Exception e)` and logs. The
job still shows `Failed` in `AsyncApexJob` and nothing was logged, because the failure was a
`LimitException` that the catch could not see (see the first gotcha above — the Apex Developer Guide's
own finalizer example does exactly this, with a `while (true)` loop inside a `try/catch`, `apexdev`
L16398–16414).

**When it occurs:** Any uncatchable failure inside async Apex. The recovery hook is a transaction
finalizer: `FinalizerContext.getResult()` returns the `System.ParentJobResult` enum, `SUCCESS` or
`UNHANDLED_EXCEPTION`, and `getException()` "returns the exception with which the Queueable job failed
when `getResult` is `UNHANDLED_EXCEPTION`, `null` otherwise" (`apexdev` L16330–16336). The finalizer runs
in its own transaction, so its DML survives the job's rollback, and callouts are allowed in it
(`apexdev` L16297–16298, L16353).

**How to avoid:** Attach a finalizer with `System.attachFinalizer`. Budget the retries: "A Queueable job
that failed due to an unhandled exception can be successively re-enqueued five times by a transaction
finalizer" and the counter resets only on a clean run (`apexdev` L16293–16295). For Batch Apex the
equivalent is `Database.RaisesPlatformEvents`, which fires a `BatchApexErrorEvent` carrying `JobScope`
and `ExceptionType` when `start`, `execute` or `finish` throws (`apexdev` L17862–17866). Design detail
is in `apex/apex-transaction-finalizers`.

---

## The Exception Message Is A Data-Privacy Surface

**What happens:** A custom exception is constructed as `new IntakeException('Cannot match ' + email +
' to a contact')`. That message lands in the debug log, the unhandled-exception email, the log object,
and — if it reaches an `AuraHandledException` — the browser.

**When it occurs:** Any exception whose message is built by concatenating record data. Salesforce states
the constraint directly: "make sure that test error messages and exception details don’t contain any
personal data. The Apex exception handler and testing framework can’t determine if sensitive data is
contained in user-defined messages and details" (`apexdev` L40308–40311).

**How to avoid:** Follow the guide's own remedy — "create an Exception subclass with new properties that
hold the personal data. Then, don’t include subclass property information in the exception's message
string" (`apexdev` L40311–40313). Put record Ids and a correlation id in the message; put anything
identifying in a typed field the logger chooses whether to persist.

---

## A `DmlException` Message Is Not A User Message

**What happens:** `throw new AuraHandledException(e.getMessage())` shows the end user
`FIELD_CUSTOM_VALIDATION_EXCEPTION, Discount above 40% needs VP approval: [Discount__c]` — the status
code, the internal validation-rule text, and the field API name.

**When it occurs:** Any `DmlException` surfaced verbatim. The exception's own accessors are built for
operators, not users: `getDmlFieldNames(i)` returns "the names of the field or fields that caused the
error", `getDmlType(i)` returns a `System.StatusCode` enum value, and `getDmlStatusCode` is deprecated
in its favour (`apexrefguide` L215130–215158).

**How to avoid:** Build the user message from your own vocabulary and log the platform one. On the LWC
side the client error "includes your custom message and the one returned from Apex, which is available
via `e.getMessage()`" but "doesn’t include the `body.stackTrace` property" (Lightning Web Components
Developer Guide, page `apex-error-handling`, `lwc_guide` L7522) — so `AuraHandledException` hides the
trace, not the message. Deciding what the component then renders is `lwc/lwc-error-boundaries`'s job.
